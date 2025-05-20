import os
from typing import Optional
from openai import OpenAI
from dataclasses import dataclass
from auto_marker.prompts import MarkPromptTemplate
from auto_marker.basics import Answer, ProblemID
from auto_marker.logging import logger
import asyncio


@dataclass
class LLMConfig:
    """Configuration class for LLM settings"""

    base_url: str
    api_key: str
    model: str
    no_subproblem_template: str
    subproblem_first_round_template: str
    subproblem_prompt_template: str
    temperature: float = 0.5
    max_trials: int = 5

    def get_client(self) -> OpenAI:
        """Create and return an OpenAI client with the config settings"""
        logger.info(f"Creating OpenAI client with base_url: {self.base_url}, model: {self.model}")
        return OpenAI(api_key=self.api_key, base_url=self.base_url)


class LLMInteractor:
    """Handles many rounds of interaction with an LLM"""

    def __init__(self, config: LLMConfig):
        """Initialize the LLM interactor with configuration.

        Args:
            config: Configuration for the LLM interaction
        """
        self.config = config
        self.client = config.get_client()
        self.messages = []
        self.reasoning_history = []  # To store reasoning content when available
        logger.info(f"Initialized LLMInteractor with model: {config.model}, temperature: {config.temperature}")

    def _reset_conversation(self):
        """Reset conversation history for a new problem."""
        logger.debug("Resetting conversation history")
        self.messages = []
        self.reasoning_history = []

    async def _call_llm(self, messages):
        """Call the LLM API with retry logic.

        Args:
            messages: The messages to send to the LLM

        Returns:
            The response from the LLM

        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None
        message_length = sum(len(str(m.get("content", ""))) for m in messages)
        logger.info(f"Calling LLM API with {len(messages)} messages (total length: ~{message_length} chars)")

        for attempt in range(self.config.max_trials):
            try:
                logger.debug(f"Attempt {attempt + 1}/{self.config.max_trials} to call LLM API")
                # OpenAI's client is synchronous, so we don't use await here
                response = self.client.chat.completions.create(
                    model=self.config.model,
                    messages=messages,
                    temperature=self.config.temperature,
                )
                logger.info(f"LLM API call successful on attempt {attempt + 1}")
                return response
            except Exception as e:
                last_exception = e
                logger.warning(f"LLM API call failed (attempt {attempt + 1}/{self.config.max_trials}): {str(e)}")
                if attempt < self.config.max_trials - 1:
                    backoff_time = 60*(2**attempt)
                    logger.info(f"Retrying in {backoff_time} seconds...")
                    # Use asyncio.sleep for non-blocking wait
                    await asyncio.sleep(backoff_time)

        # If we get here, all attempts failed
        logger.error(f"All {self.config.max_trials} attempts to call LLM API failed. Last error: {str(last_exception)}")
        raise last_exception or Exception("All attempts to call LLM API failed")

    async def first_round_interaction(
        self,
        problem_description: Answer,
        reference_answer: Answer,
        student_answer: Answer,
        subproblem_nums: int = 0,
    ) -> None:
        """Handle the first round of interaction for a problem.

        Args:
            problem_description: The description of the problem
            reference_answer: The reference answer to the problem
            student_answer: The student's answer to the problem
            subproblem_nums: The number of subproblems in the problem
        """
        logger.info(f"Starting first round interaction with {subproblem_nums} subproblems")

        # Reset conversation for new problem
        self._reset_conversation()

        try:
            if subproblem_nums > 0:
                # For problems with subproblems, only send problem description in first round
                prompt_template = MarkPromptTemplate(
                    template=self.config.subproblem_first_round_template,
                    problem_description=problem_description.answer,
                    # Don't include reference or student answers in first round
                    reference_answer="",
                    student_answer="",
                    subproblem_nums=subproblem_nums,
                )
            else:
                # For problems without subproblems, include all information
                prompt_template = MarkPromptTemplate(
                    template=self.config.no_subproblem_template,
                    problem_description=problem_description.to_markdown_str("problem description"),
                    reference_answer=reference_answer.to_markdown_str("reference answer"),
                    student_answer=student_answer.to_markdown_str("student answer"),
                    subproblem_nums=subproblem_nums,
                )

            # Format the prompt
            prompt = prompt_template.to_prompt()
            prompt_length = len(prompt)
            logger.debug(f"Generated first round prompt with length: {prompt_length} characters")

            # Add the user message
            self.messages.append({"role": "user", "content": prompt})

            # Send the request to the LLM with retry logic
            logger.info("Sending first round request to LLM")
            response = await self._call_llm(self.messages)

            # Extract and store the response
            response_content = response.choices[0].message.content
            response_length = len(response_content) if response_content else 0
            logger.info(f"Received first round response from LLM (length: {response_length} characters)")

            self.messages.append({"role": "assistant", "content": response_content})

            # Store reasoning content if the model supports it
            if hasattr(response.choices[0].message, "reasoning_content"):
                reasoning_content = response.choices[0].message.reasoning_content  # type: ignore
                reasoning_length = len(reasoning_content) if reasoning_content else 0
                logger.debug(f"Received reasoning content (length: {reasoning_length} characters)")
                self.reasoning_history.append(reasoning_content)
            else:
                logger.debug("No reasoning content available in this response")
                self.reasoning_history.append(None)

        except Exception as e:
            logger.error(f"Error in first round interaction: {str(e)}")
            raise

    async def subproblem_round_interaction(
        self,
        problem_description: Answer,
        reference_answer: Answer,
        student_answer: Answer,
        subproblem_id: str,
        is_first_subproblem: bool,
    ) -> None:
        """Handle a round of interaction for a subproblem.

        Args:
            problem_description: The description of the problem
            reference_answer: The reference answer to the problem
            student_answer: The student's answer to the problem
            subproblem_id: The ID of the subproblem
            is_first_subproblem: Whether this is the first subproblem
        """
        logger.info(f"Starting subproblem interaction for subproblem ID: {subproblem_id}")

        try:
            if is_first_subproblem:
                # For first subproblem, include main problem answers along with subproblem
                prompt_template = MarkPromptTemplate(
                    template=self.config.subproblem_prompt_template,
                    problem_description=problem_description.get_sub_answer(subproblem_id, "problem description"),
                    # Include both main reference answer and subproblem reference answer
                    reference_answer=reference_answer.answer
                    + "\n\n"
                    + reference_answer.get_sub_answer(subproblem_id, "reference answer"),
                    # Include both main student answer and subproblem student answer
                    student_answer=student_answer.answer
                    + "\n\n"
                    + student_answer.get_sub_answer(subproblem_id, "student answer"),
                    subproblem_id=subproblem_id,
                )
            else:
                # For subsequent subproblems, keep original behavior
                prompt_template = MarkPromptTemplate(
                    template=self.config.subproblem_prompt_template,
                    problem_description=problem_description.get_sub_answer(subproblem_id, "problem description"),
                    reference_answer=reference_answer.get_sub_answer(subproblem_id, "reference answer"),
                    student_answer=student_answer.get_sub_answer(subproblem_id, "student answer"),
                    subproblem_id=subproblem_id,
                )

            # Format the prompt
            prompt = prompt_template.to_prompt()
            prompt_length = len(prompt)
            logger.debug(f"Generated subproblem prompt with length: {prompt_length} characters")

            # Add the user message
            self.messages.append({"role": "user", "content": prompt})

            # Send the request to the LLM with retry logic
            logger.info(f"Sending subproblem {subproblem_id} request to LLM")
            response = await self._call_llm(self.messages)

            # Extract and store the response
            response_content = response.choices[0].message.content
            response_length = len(response_content) if response_content else 0
            logger.info(f"Received subproblem {subproblem_id} response from LLM (length: {response_length} characters)")

            self.messages.append({"role": "assistant", "content": response_content})

            # Store reasoning content if the model supports it
            if hasattr(response.choices[0].message, "reasoning_content"):
                reasoning_content = response.choices[0].message.reasoning_content  # type: ignore
                reasoning_length = len(reasoning_content) if reasoning_content else 0
                logger.debug(f"Received subproblem reasoning content (length: {reasoning_length} characters)")
                self.reasoning_history.append(reasoning_content)
            else:
                logger.debug("No reasoning content available in this response")
                self.reasoning_history.append(None)

        except Exception as e:
            logger.error(f"Error in subproblem {subproblem_id} interaction: {str(e)}")
            raise

    def _save_conversation_log(self, logging_path: str, problem_id: ProblemID) -> None:
        """Save the conversation log to a file.

        Args:
            logging_path: The path to save the conversation log
            problem_id: The ID of the problem
        """
        logger.info(f"Writing conversation log to {logging_path}")
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(logging_path), exist_ok=True)

            with open(logging_path, "w", encoding="utf-8") as f:
                # Write problem ID at the top
                f.write(f"Problem ID: {problem_id}\n\n")

                # Process each round of conversation
                round_count = len(self.messages) // 2
                for round_idx in range(round_count):
                    user_msg_idx = round_idx * 2
                    assistant_msg_idx = user_msg_idx + 1

                    # Determine round info
                    if round_idx == 0:
                        round_info = "Round 1 starts"
                    else:
                        subprob_idx = round_idx - 1
                        subprob_id = problem_id.subproblem_id[subprob_idx]
                        round_info = f"Round {round_idx + 1} starts (Subproblem {subprob_id})"

                    f.write(f"{round_info}\n")

                    # User message
                    header = "User Message".center(90, "=")
                    f.write(f"{header}\n")
                    f.write(f"{self.messages[user_msg_idx]['content']}\n\n")

                    # Reasoning content (if available)
                    header = "Reasoning Content".center(90, "=")
                    f.write(f"{header}\n")
                    if round_idx < len(self.reasoning_history) and self.reasoning_history[round_idx]:
                        f.write(f"{self.reasoning_history[round_idx]}\n\n")
                    else:
                        f.write("No reasoning content available\n\n")

                    # LLM output
                    header = "LLM Output".center(90, "=")
                    f.write(f"{header}\n")
                    f.write(f"{self.messages[assistant_msg_idx]['content']}\n\n")

                    # Round end
                    if round_idx == 0:
                        f.write("Round 1 ends\n\n")
                    else:
                        subprob_idx = round_idx - 1
                        subprob_id = problem_id.subproblem_id[subprob_idx]
                        f.write(f"Round {round_idx + 1} ends (Subproblem {subprob_id})\n\n")

            logger.info(f"Successfully wrote conversation log to {logging_path}")

        except Exception as e:
            logger.error(f"Failed to write conversation log: {str(e)}")

    async def mark_problem(
        self,
        problem_id: ProblemID,
        problem_description: Answer,
        reference_answer: Answer,
        student_answer: Answer,
        logging_path: Optional[str] = None,
    ) -> Answer:
        """Run the full grading process for a problem and its subproblems.

        Args:
            problem_id: The ID of the problem
            problem_description: The description of the problem
            reference_answer: The reference answer to the problem
            student_answer: The student's answer to the problem
            logging_path: The path to log the conversation

        Returns:
            The whole mark for the student's submission, an Answer object
        """
        logger.info(f"Starting marking process for problem ID: {problem_id}")

        try:
            # Reset conversation for new problem
            self._reset_conversation()

            # First round interaction
            logger.info("Starting first round interaction")
            await self.first_round_interaction(
                problem_description,
                reference_answer,
                student_answer,
                len(problem_id.subproblem_id),
            )

            # If there are subproblems, handle each one
            if problem_id.has_subproblems():
                logger.info(f"Processing {len(problem_id.subproblem_id)} subproblems")
                for i, subproblem_id in enumerate(problem_id.subproblem_id):
                    logger.info(f"Processing subproblem: {subproblem_id}")
                    is_first_subproblem = i == 0
                    await self.subproblem_round_interaction(
                        problem_description,
                        reference_answer,
                        student_answer,
                        subproblem_id,
                        is_first_subproblem,
                    )

            # Create a new Answer object to store the grading results
            logger.info("Creating final grading result")

            # Initialize marks differently based on whether we have subproblems
            if problem_id.has_subproblems():
                # For problems with subproblems, don't use the first round response
                # since it's just for confirmation, not for actual grading
                logger.debug("Problem has subproblems - discarding first round response")
                marks = Answer(answer="")
            else:
                # For problems without subproblems, use the first round response
                logger.debug("Problem has no subproblems - using first round response")
                marks = Answer(answer=self.messages[1]["content"])

            # Process subproblem responses
            if problem_id.has_subproblems():
                logger.debug("Adding subproblem responses to final result")
                # For each subproblem, add the corresponding response as a sub-answer
                for i, subproblem_id in enumerate(problem_id.subproblem_id):
                    # Get the message index for this subproblem (each interaction adds two messages)
                    message_idx = 3 + (i * 2)  # First round has indices 0,1; first subproblem starts at 2,3; etc.
                    if message_idx < len(self.messages):
                        subproblem_content = self.messages[message_idx]["content"]
                        logger.debug(f"Adding response for subproblem {subproblem_id}")
                        marks.add_sub_answer(subproblem_id, subproblem_content)

            # Log the conversatio alogging path is provided
            if logging_path:
                self._save_conversation_log(logging_path, problem_id)

            logger.info("Marking process completed successfully")
            return marks

        except Exception as e:
            logger.error(f"Error in marking submission: {str(e)}")
            raise
