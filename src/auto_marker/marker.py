import tomllib  # Changed from toml to tomllib (Python 3.11+)
import asyncio
import json
import shutil
import re
from typing import Any
from pathlib import Path
from dataclasses import dataclass

import logging
from auto_marker.logging import logger, configure_global_logger
from auto_marker.openreview_interact import OpenReviewInteract, OpenReviewConfig
from auto_marker.llm_interact import LLMInteractor, LLMConfig
from auto_marker.text_processor import parse_content_with_filter
from auto_marker.basics import ProblemID, StudentSubmission, Answer, AnswerGroup, parse_problem_list


@dataclass
class MarkerConfig:
    """Configuration for the automated marking system."""

    # OpenReview configuration
    openreview: dict[str, str]

    # LLM configuration
    llm: dict[str, Any]

    # Directory configurations
    paths: dict[str, str]

    # Homework ID to process
    homework_id: str

    # Problem list configuration
    problem_list: str

    # Marking prompt templates
    prompts: dict[str, str]

    @classmethod
    def from_toml(cls, toml_path: str) -> "MarkerConfig":
        """Load configuration from a TOML file."""
        try:
            with open(toml_path, "rb") as f:  # Changed to binary mode as required by tomllib
                config_dict = tomllib.load(f)  # Changed from toml.load to tomllib.load
                # The remaining sections are dictionaries
                return cls(**config_dict)
        except Exception as e:
            raise ValueError(f"Failed to load configuration from {toml_path}: {str(e)}")

    def validate(self) -> bool:
        """Validate the configuration."""
        # Check OpenReview configuration
        required_or_fields = [
            self.openreview.get("username"),
            self.openreview.get("password"),
            self.openreview.get("venue_id"),
        ]
        if not all(required_or_fields):
            raise ValueError("OpenReview configuration incomplete. Required fields: username, password, venue_id")

        # Check LLM configuration
        required_llm_fields = [
            self.llm.get("base_url"),
            self.llm.get("model"),
            self.llm.get("api_key"),
        ]
        if not all(required_llm_fields):
            raise ValueError("LLM configuration incomplete. Required fields: base_url, model, api_key")

        # Check prompts
        required_prompt_fields = [
            self.prompts.get("no_subproblem_template"),
            self.prompts.get("subproblem_first_round_template"),
            self.prompts.get("subproblem_round_template"),
        ]
        if not all(required_prompt_fields):
            raise ValueError(
                "Prompts configuration incomplete. Required fields: no_subproblem_template, subproblem_first_round_template, subproblem_round_template"  # noqa: E501
            )

        # check mark templates
        required_comment_fields = [
            self.prompts.get("llm_mark_template"),
            self.prompts.get("human_mark_template"),
        ]

        if not all(required_comment_fields):
            raise ValueError(
                "Prompts configuration incomplete. Required fields: llm_mark_template, human_mark_template"
            )

        # Check paths
        required_paths = [
            self.paths.get("reference_materials"),
            self.paths.get("processed_submissions"),
            self.paths.get("raw_submissions"),
            self.paths.get("human_marks"),
            self.paths.get("mark_logs"),  # for debugging
        ]
        if not all(required_paths):
            raise ValueError(
                "Path configuration incomplete. Required paths: reference_materials, processed_submissions, raw_submissions, human_marks, mark_logs"  # noqa: E501
            )

        # Check homework ID
        if not self.homework_id:
            raise ValueError("Homework ID must be specified")

        return True


class Marker:
    """
    Main class for automating the marking workflow:
    1. Download student submissions from OpenReview
    2. Process the submissions to extract relevant content
    3. Mark the submissions using LLM
    4. Upload the marks back to OpenReview
    """

    def __init__(self, config_path: str):
        """Initialize the marker with configuration.

        Args:
            config_path: Path to the configuration file (TOML format)
        """
        # Load and validate configuration
        self.config = MarkerConfig.from_toml(config_path)
        self.config.validate()

        # Configure the global logger
        self.log_dir = Path("../log")  # Create log directory first
        self.log_dir.mkdir(parents=True, exist_ok=True)

        log_file = self.log_dir / f"marker_hw{self.config.homework_id}_init.log"
        configure_global_logger(level=logging.INFO, log_file=str(log_file))

        logger.info(f"Initializing Marker with homework ID: {self.config.homework_id}")

        # Set up paths
        self.reference_materials_path = Path(self.config.paths["reference_materials"])
        self.processed_submissions_path = (
            Path(self.config.paths["processed_submissions"]) / f"HW{self.config.homework_id}"
        )
        self.raw_submissions_path = Path(self.config.paths["raw_submissions"]) / f"HW{self.config.homework_id}"
        self.mark_logs_path = Path(self.config.paths["mark_logs"]) / f"HW{self.config.homework_id}"
        self.human_marks_path = Path(self.config.paths["human_marks"]) / f"HW{self.config.homework_id}"

        # Create directories if they don't exist
        self.reference_materials_path.mkdir(parents=True, exist_ok=True)
        self.processed_submissions_path.mkdir(parents=True, exist_ok=True)
        self.raw_submissions_path.mkdir(parents=True, exist_ok=True)
        self.mark_logs_path.mkdir(parents=True, exist_ok=True)
        self.human_marks_path.mkdir(parents=True, exist_ok=True)

        # Set up problem list
        self.problem_list = parse_problem_list(self.config.problem_list)

        # Set up OpenReview config (but don't create client yet)
        self.openreview_config = OpenReviewConfig(
            username=self.config.openreview["username"],
            password=self.config.openreview["password"],
            venue_id=self.config.openreview["venue_id"],
            submission_store_path=str(self.raw_submissions_path),
            base_url=self.config.openreview.get("base_url", "https://api2.openreview.net"),
        )

        # Set up LLM config (but don't create client yet)
        self.llm_config = LLMConfig(
            base_url=self.config.llm["base_url"],
            api_key=self.config.llm["api_key"],
            model=self.config.llm["model"],
            no_subproblem_template=self.config.prompts["no_subproblem_template"],
            subproblem_first_round_template=self.config.prompts["subproblem_first_round_template"],
            subproblem_prompt_template=self.config.prompts["subproblem_round_template"],
            temperature=self.config.llm.get("temperature", 0.5),
            max_trials=self.config.llm.get("max_trials", 5),
        )

        # Set up reference answer and problem description file paths
        self.reference_answer_file = self.reference_materials_path / f"HW{self.config.homework_id}-answer.tex"
        self.problem_description_file = self.reference_materials_path / f"HW{self.config.homework_id}-description.tex"

        # Initialize data containers
        self.processed_submissions: dict[str, StudentSubmission] = {}
        self.reference_answers: AnswerGroup
        self.problem_descriptions: AnswerGroup

        # Check if reference materials exist
        if not self.reference_answer_file.exists():
            logger.warning(f"Reference answer file {self.reference_answer_file} does not exist")
        if not self.problem_description_file.exists():
            logger.warning(f"Problem description file {self.problem_description_file} does not exist")

    def dump_submission(self, submission: StudentSubmission) -> None:
        """
        Save a student submission to a JSON file.

        Args:
            submission: The StudentSubmission object to save
        """
        file_path = (
            self.processed_submissions_path
            / f"submission{submission.submission_number}-{submission.student_id}-{submission.student_name}.json"
        )
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(submission.to_json(), f, ensure_ascii=False, indent=2)

        logger.debug(f"Saved submission {submission.submission_number} to {file_path}")

    def _get_openreview_client(self) -> OpenReviewInteract:
        """
        Lazy-load the OpenReview client when needed.

        Returns:
            OpenReviewInteract: The initialized OpenReview client
        """
        if not hasattr(self, "_openreview_client"):
            logger.info("Initializing OpenReview client...")
            self._openreview_client = OpenReviewInteract(self.openreview_config)
        return self._openreview_client

    def _get_llm_interactor(self) -> LLMInteractor:
        """
        Lazy-load the LLM interactor when needed.

        Returns:
            LLMInteractor: The initialized LLM interactor
        """
        if not hasattr(self, "_llm_interactor"):
            logger.info("Initializing LLM client...")
            self._llm_interactor = LLMInteractor(self.llm_config)
        return self._llm_interactor

    def _check_raw_submissions_exist(self) -> bool:
        """Check if all raw submissions are in self.processed_submissions."""
        # the only case is that self.processed_submissions is empty
        return bool(self.processed_submissions)

    def _check_reference_materials_loaded(self) -> bool:
        """Check if reference materials have been loaded."""
        return hasattr(self, "reference_answers") and hasattr(self, "problem_descriptions")

    def _check_submissions_processed(self) -> bool:
        """Check if all submissions have been processed with answers extracted."""
        if not self.processed_submissions:
            return False

        # Check all submissions have been processed
        for submission in self.processed_submissions.values():
            if not submission.processed_source_code:
                return False
        return True

    def _check_submissions_marked(self) -> bool:
        """Check if all submissions have been marked."""
        if not self.processed_submissions:
            return False

        # Check all submissions have marks
        for submission in self.processed_submissions.values():
            if not submission.marks:
                return False

        return True

    def load_reference_materials(self) -> None:
        """
        Load reference answers and problem descriptions from files.
        """

        logger.info(f"Loading reference materials from {self.reference_materials_path}...")

        logger.info(f"Loading reference answers from {self.reference_answer_file}...")

        # Load reference answers
        if self.reference_answer_file.exists():
            with open(self.reference_answer_file, encoding="utf-8") as f:
                self.reference_answers = parse_content_with_filter(f.read(), "tex", self.problem_list)
                logger.info(f"Loaded {len(self.reference_answers)} reference answers.")
        else:
            logger.warning(f"Reference answer file {self.reference_answer_file} does not exist")
            self.reference_answers = AnswerGroup()

        logger.info(f"Loading problem descriptions from {self.problem_description_file}...")

        # Load problem descriptions
        if self.problem_description_file.exists():
            with open(self.problem_description_file, encoding="utf-8") as f:
                self.problem_descriptions = parse_content_with_filter(f.read(), "tex", self.problem_list)
                logger.info(f"Loaded {len(self.problem_descriptions)} problem descriptions.")
        else:
            logger.warning(f"Problem description file {self.problem_description_file} does not exist")
            self.problem_descriptions = AnswerGroup()

        logger.info("Reference materials loaded.")

    async def download_submissions(self) -> None:
        """
        Download student submissions from OpenReview for the configured homework ID.
        """
        logger.info(f"Downloading submissions for homework: {self.config.homework_id} to {self.raw_submissions_path}")

        # Use OpenReview client to fetch submissions
        openreview_client = self._get_openreview_client()
        submissions, failed_submissions = await openreview_client.process_all_submissions(self.config.homework_id)

        if failed_submissions:
            logger.warning(f"Failed to process {len(failed_submissions)} submissions:")
            for failed_submission in failed_submissions:
                logger.warning(f"  - {failed_submission}")

        logger.info(f"Successfully downloaded {len(submissions)} submissions.")

        # Save the submissions to disk
        logger.info(f"Saving source code to {self.processed_submissions_path}")

        for submission in submissions:
            self.processed_submissions[submission.submission_number] = submission
            self.dump_submission(submission)

            # Copy PDF to human_marks directory for manual review
            pdf_source = (
                self.raw_submissions_path
                / f"submission{submission.submission_number}-{submission.student_id}-{submission.student_name}"
                / "Submission-PDF.pdf"
            )

            if pdf_source.exists():
                pdf_dest = (
                    self.human_marks_path
                    / f"submission{submission.submission_number}-{submission.student_id}-{submission.student_name}.pdf"
                )
                try:
                    shutil.copy2(pdf_source, pdf_dest)
                    logger.info(f"Copied PDF for submission {submission.submission_number} to human marks directory")
                except Exception as e:
                    logger.error(f"Failed to copy PDF for submission {submission.submission_number}: {e}")
            else:
                logger.warning(f"PDF file for submission {submission.submission_number} not found at {pdf_source}")

    def load_submissions_from_files(self) -> None:
        """
        Load processed submissions from JSON files if they exist.
        """
        logger.info(f"Loading processed submissions from {self.processed_submissions_path}...")

        submission_files = list(self.processed_submissions_path.glob("*.json"))
        if not submission_files:
            logger.info("No processed submission files found.")
            return

        for file_path in submission_files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    submission_data = json.load(f)
                    submission = StudentSubmission.from_json(submission_data)
                    self.processed_submissions[submission.submission_number] = submission
            except Exception as e:
                logger.error(f"Error loading submission from {file_path}: {e}")

        logger.info(f"Loaded {len(self.processed_submissions)} submissions.")

    def parse_submission(self, submission: StudentSubmission) -> None:
        """
        Parse the submission content to extract the student's answers and filter it based on the problem list.

        NOTE: It will update the submission object with the processed content.

        Args:
            submission: The StudentSubmission object to parse
        """
        # Parse the submission content

        logger.info(
            f"Parsing submission {submission.submission_number}-{submission.student_id}-{submission.student_name}..."
        )
        parsed_content = parse_content_with_filter(
            submission.raw_source_code, submission.code_language, self.problem_list
        )

        # Update the submission with the parsed content
        submission.processed_source_code = parsed_content
        self.processed_submissions[submission.submission_number] = submission
        self.dump_submission(submission)
        return None

    def parse_submissions(self) -> None:
        """
        Parse all downloaded submissions to extract the student's answers.
        """
        # Check if submissions have been downloaded
        if not self._check_raw_submissions_exist():
            # Try to load from files first
            self.load_submissions_from_files()

            if not self._check_raw_submissions_exist():
                raise ValueError(
                    "No submissions available. Please download submissions first using download_submissions()."
                )

        logger.info("Parsing all submissions...")

        for submission_number, submission in self.processed_submissions.items():
            self.parse_submission(submission)

        logger.info("All submissions parsed.")

    async def mark_problem(self, problem_id: ProblemID, submission: StudentSubmission) -> Answer:
        """
        Mark a single problem for a student submission using LLM.

        NOTE: This method is asynchronous and thus it will NOT modify the submission object.

        Args:
            problem_id: The problem ID to mark
            submission: The StudentSubmission object to mark

        Returns:
            The Answer object containing the mark
        """
        logger.info(
            f"Marking problem {problem_id} for submission {submission.submission_number}-{submission.student_id}-{submission.student_name}..."  # noqa: E501
        )

        # Get problem description and reference answer for this problem
        problem_description = self.problem_descriptions.get(problem_id, Answer("No problem description available"))
        reference_answer = self.reference_answers.get(problem_id, Answer("No reference answer available"))

        # Get student's answer for this problem (or provide default)
        if not submission.processed_source_code:
            logger.warning(f"No processed source code found for submission {submission.submission_number}")
            student_answer = Answer("No answer provided")
        else:
            student_answer = submission.processed_source_code.get(problem_id, Answer("No answer provided"))

        # Generate log file path
        log_file = self.mark_logs_path / f"submission{submission.submission_number}_{problem_id}.txt"

        try:
            # Get LLM interactor and use it to mark the problem
            llm_interactor = self._get_llm_interactor()
            mark_result = await llm_interactor.mark_problem(
                problem_id=problem_id,
                problem_description=problem_description,  # type: ignore
                reference_answer=reference_answer,  # type: ignore
                student_answer=student_answer,  # type: ignore
                logging_path=str(log_file),
            )

            logger.info(f"Successfully marked problem {problem_id} for submission {submission.submission_number}")
            return mark_result

        except Exception as e:
            logger.error(f"Error marking problem {problem_id} for submission {submission.submission_number}: {e}")
            # Return a default answer indicating the error
            error_answer = Answer(answer=f"Error during marking: {str(e)}")
            return error_answer

    async def mark_submission(self, submission: StudentSubmission) -> StudentSubmission:
        """
        Mark all problems for a single student submission.

        NOTE: This method is asynchronous and it will modify the submission object.

        This method will:
        1. Process all problems in the problem list asynchronously
        2. Update the submission with the marks
        3. Save the updated submission to the JSON file and the Markdown-formatted mark files

        Args:
            submission: The StudentSubmission object to mark

        Returns:
            The updated StudentSubmission object with marks
        """
        logger.info(
            f"Marking submission {submission.submission_number}-{submission.student_id}-{submission.student_name}..."
        )

        # Initialize an AnswerGroup to store marks
        marks = AnswerGroup()

        # Process all problems asynchronously

        # Create a list of tasks for each problem
        mark_tasks = []
        for problem_id in self.problem_list:
            mark_tasks.append(self.mark_problem(problem_id, submission))

        # Wait for all tasks to complete
        mark_results = await asyncio.gather(*mark_tasks)

        # Update the marks with the results
        for problem_id, mark_result in zip(self.problem_list, mark_results):
            marks[problem_id] = mark_result

        # Update the submission with the marks
        submission.marks = marks
        self.processed_submissions[submission.submission_number] = submission
        self.dump_submission(submission)

        # Save the marks to a Markdown-formatted file
        mark_file = (
            self.processed_submissions_path
            / f"submission{submission.submission_number}-{submission.student_id}-{submission.student_name}-llm_marks.md"
        )
        with open(mark_file, "w", encoding="utf-8") as f:
            f.write(self.config.prompts["llm_mark_template"] + "\n\n" + marks.to_markdown_str("mark"))

        # Copy to human_marks directory for manual editing
        human_mark_file = (
            self.human_marks_path
            / f"submission{submission.submission_number}-{submission.student_id}-{submission.student_name}-human_marks.md"  # noqa: E501
        )
        try:
            with open(human_mark_file, "w", encoding="utf-8") as f:
                f.write(self.config.prompts["human_mark_template"] + "\n\n" + marks.to_markdown_str("mark"))
            logger.info(
                f"Copied marks for submission {submission.submission_number} to human marks directory for editing"
            )
        except Exception as e:
            logger.error(f"Failed to copy marks for submission {submission.submission_number}: {e}")

        logger.info(
            f"Successfully marked all problems for submission {submission.submission_number}-{submission.student_id}-{submission.student_name}"  # noqa: E501
        )
        return submission

    async def mark_all_submissions(self) -> None:
        """
        Mark all submissions asynchronously in parallel.

        This method will process all submissions in parallel since marking for different
        students can be done independently.
        """
        # Check if submissions have been downloaded and processed
        if not self._check_raw_submissions_exist():
            # Try to load from files first
            self.load_submissions_from_files()

            if not self._check_raw_submissions_exist():
                raise ValueError(
                    "No submissions available. Please download submissions first using download_submissions()."
                )

        # Check if submissions have been parsed
        if not self._check_submissions_processed():
            raise ValueError(
                "Submissions have not been fully processed. Please parse submissions first using parse_submissions()."
            )

        # Check if reference materials are loaded
        if not self._check_reference_materials_loaded():
            self.load_reference_materials()

        logger.info(f"Marking all {len(self.processed_submissions)} submissions...")

        # Create tasks for each submission
        mark_tasks = []
        for submission_number, submission in self.processed_submissions.items():
            mark_tasks.append(self.mark_submission(submission))

        # Execute all tasks in parallel
        try:
            # Use gather to run all tasks concurrently
            results = await asyncio.gather(*mark_tasks, return_exceptions=True)

            # Check for any exceptions
            successful_count = 0
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Error during marking: {result}")
                else:
                    successful_count += 1

            logger.info(f"Successfully marked {successful_count} out of {len(self.processed_submissions)} submissions")
        except Exception as e:
            logger.error(f"Error during marking process: {e}")

        logger.info("Marking process completed.")

    async def post_llm_marks(self) -> None:
        """
        Post LLM-generated marks to OpenReview.

        This method will:
        1. Convert the marks for each submission to a markdown-formatted comment
        2. Submit the comments to OpenReview using the OpenReview client
        3. Report on successful and failed comment postings
        """
        # Check if submissions have been downloaded, parsed, and marked
        if not self._check_raw_submissions_exist():
            # Try to load from files first
            self.load_submissions_from_files()

            if not self._check_raw_submissions_exist():
                raise ValueError("No submissions available. Please download and process submissions first.")

        if not self._check_submissions_marked():
            raise ValueError("No marks available. Please mark submissions first using mark_all_submissions().")

        logger.info("Posting LLM marks to OpenReview...")

        # Create a dictionary to map submission numbers to their comment content
        comment_contents = {}

        # Prepare all submissions with marks for posting
        valid_submissions = []

        for submission_number, submission in self.processed_submissions.items():
            # Skip submissions without marks
            if not submission.marks or len(submission.marks) == 0:
                logger.warning(f"No marks found for submission {submission_number}, skipping...")
                continue

            # Convert marks to markdown format for the comment
            mark_content = self.config.prompts["llm_mark_template"] + "\n\n" + submission.marks.to_markdown_str("mark")
            logger.debug(f"Mark content for submission {submission_number}: {mark_content}")
            comment_contents[submission.submission_number] = mark_content
            valid_submissions.append(submission)

        if not valid_submissions:
            logger.warning("No valid submissions with marks found. Nothing to post.")
            return

        logger.info(f"Sending {len(valid_submissions)} LLM comment(s) to OpenReview...")

        # Post the comments using the OpenReview client
        try:
            openreview_client = self._get_openreview_client()
            successful_comments, failed_comments = await openreview_client.post_comments(
                student_submissions=valid_submissions, comment_contents=comment_contents
            )

            # Report on results
            if successful_comments:
                logger.info(f"Successfully posted {len(successful_comments)} LLM comments.")

            if failed_comments:
                logger.warning(f"Failed to post LLM comments for {len(failed_comments)} submissions:")
                for submission_number in failed_comments:
                    logger.warning(f"  - {submission_number}")

        except Exception as e:
            logger.error(f"Error posting LLM comments to OpenReview: {e}")

        logger.info("LLM mark posting process completed.")

    async def post_human_marks(self) -> None:
        """
        Post human-verified marks to OpenReview.

        This method will:
        1. Read the human-edited mark files from the human_marks directory
        2. Submit the comments to OpenReview using the OpenReview client
        3. Report on successful and failed comment postings
        """
        logger.info("Posting human-verified marks to OpenReview...")

        # Check if human marks directory exists
        if not self.human_marks_path.exists():
            raise ValueError(f"Human marks directory {self.human_marks_path} does not exist.")

        # Find all human mark files
        human_mark_files = list(self.human_marks_path.glob("*-human_marks.md"))

        if not human_mark_files:
            logger.warning("No human mark files found. Nothing to post.")
            return

        # Create lists to track valid submissions and their content
        valid_submissions = []
        comment_contents = {}

        # Load all submissions if they haven't been loaded yet
        if not self._check_raw_submissions_exist():
            self.load_submissions_from_files()

        # Process each human mark file
        for mark_file in human_mark_files:
            # Extract submission info from filename
            filename = mark_file.name
            match = re.match(r"submission(\d+)-(\d+)-([\s\S]+)-human_marks\.md", filename)

            if not match:
                logger.warning(f"Invalid human mark filename format: {filename}, skipping...")
                continue

            submission_number, student_id, student_name = match.groups()

            # Check if we have this submission
            if submission_number not in self.processed_submissions:
                logger.warning(f"No submission record found for submission {submission_number}, skipping...")
                continue

            # Read the human mark content
            try:
                with open(mark_file, encoding="utf-8") as f:
                    mark_content = f.read()

                # Store the content for posting
                comment_contents[submission_number] = mark_content
                valid_submissions.append(self.processed_submissions[submission_number])

            except Exception as e:
                logger.error(f"Error reading human mark file for submission {submission_number}: {e}")
                continue

        if not valid_submissions:
            logger.warning("No valid human marks found. Nothing to post.")
            return

        logger.info(f"Sending {len(valid_submissions)} human-verified comment(s) to OpenReview...")

        # Post the comments using the OpenReview client
        try:
            openreview_client = self._get_openreview_client()
            successful_comments, failed_comments = await openreview_client.post_comments(
                student_submissions=valid_submissions, comment_contents=comment_contents
            )

            # Report on results
            if successful_comments:
                logger.info(f"Successfully posted {len(successful_comments)} human-verified comments.")

            if failed_comments:
                logger.warning(f"Failed to post human-verified comments for {len(failed_comments)} submissions:")
                for submission_number in failed_comments:
                    logger.warning(f"  - {submission_number}")

        except Exception as e:
            logger.error(f"Error posting human-verified comments to OpenReview: {e}")

        logger.info("Human mark posting process completed.")

    async def run(self, steps: str, log_level: str = "INFO") -> None:
        """
        Run the marking workflow with configurable steps.

        Each step will use a separate log file, and steps will only run based on the specified parameter.
        The workflow follows a logical progression: download -> load_references -> process -> mark -> post-llm -> post-human.

        Args:
            steps: Which steps to run, can be:
                  - "all": Run all steps
                  - "download": Download submissions only
                  - "reference": Load reference materials only
                  - "process": Process submissions only
                  - "mark": Mark submissions only
                  - "post-llm": Post LLM marks only
                  - "post-human": Post human-verified marks only
                  - Or any combination with "+" (e.g., "download+process+mark")
            log_level: Logging level for all steps ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        """  # noqa: E501
        hw_id = self.config.homework_id
        steps = steps.lower().strip()

        # Validate log level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        log_level = log_level.upper()
        if log_level not in valid_levels:
            logger.warning(f"Invalid log level '{log_level}'. Using 'INFO' instead.")
            log_level = "INFO"

        run_all = steps == "all"
        run_download = run_all or "download" in steps
        run_reference = run_all or "reference" in steps
        run_process = run_all or "process" in steps
        run_mark = run_all or "mark" in steps
        run_post_llm = run_all or "post-llm" in steps
        run_post_human = run_all or "post-human" in steps

        # Download submissions
        if run_download:
            log_file = self.log_dir / f"marker_hw{hw_id}_download.log"
            configure_global_logger(level=log_level, log_file=str(log_file), mode="w")
            logger.info(f"Starting download step for homework {hw_id}")
            await self.download_submissions()
            logger.info("Download step completed")

        # Load reference materials
        if run_reference:
            log_file = self.log_dir / f"marker_hw{hw_id}_reference.log"
            configure_global_logger(level=log_level, log_file=str(log_file), mode="w")
            logger.info(f"Starting reference materials loading for homework {hw_id}")
            self.load_reference_materials()
            logger.info("Reference materials loading completed")

        # Process submissions
        if run_process:
            log_file = self.log_dir / f"marker_hw{hw_id}_process.log"
            configure_global_logger(level=log_level, log_file=str(log_file), mode="w")
            logger.info(f"Starting submissions processing for homework {hw_id}")
            self.parse_submissions()
            logger.info("Submissions processing completed")

        # Mark submissions
        if run_mark:
            log_file = self.log_dir / f"marker_hw{hw_id}_mark.log"
            configure_global_logger(level=log_level, log_file=str(log_file), mode="w")
            logger.info(f"Starting marking step for homework {hw_id}")
            await self.mark_all_submissions()
            logger.info("Marking step completed")

        # Post LLM marks to OpenReview
        if run_post_llm:
            log_file = self.log_dir / f"marker_hw{hw_id}_post_llm.log"
            configure_global_logger(level=log_level, log_file=str(log_file), mode="w")
            logger.info(f"Starting posting LLM marks step for homework {hw_id}")
            await self.post_llm_marks()
            logger.info("Posting LLM marks step completed")

        # Post human marks to OpenReview
        if run_post_human:
            log_file = self.log_dir / f"marker_hw{hw_id}_post_human.log"
            configure_global_logger(level=log_level, log_file=str(log_file), mode="w")
            logger.info(f"Starting posting human marks step for homework {hw_id}")
            await self.post_human_marks()
            logger.info("Posting human marks step completed")

        # Reset logger to default
        log_file = self.log_dir / f"marker_hw{hw_id}_init.log"
        configure_global_logger(level=log_level, log_file=str(log_file), mode="w")
        logger.info(f"Completed requested workflow steps for homework {hw_id}")
