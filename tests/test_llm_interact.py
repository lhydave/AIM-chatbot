import os
import pytest
from unittest.mock import patch, MagicMock

from auto_marker.llm_interact import LLMInteractor, LLMConfig
from auto_marker.basics import ProblemID, Answer


@pytest.fixture
def llm_config():
    """Create a mock LLM configuration for testing."""
    return LLMConfig(
        base_url="https://test-api.example.com",
        api_key="test_api_key",
        model="test-model",
        no_subproblem_template="Test template without subproblems: {problem_description} {reference_answer} {student_answer}",  # noqa: E501
        subproblem_first_round_template="Test template with {subproblem_nums} subproblems: {problem_description} {reference_answer} {student_answer}",  # noqa: E501
        subproblem_prompt_template="Subproblem {subproblem_id} template: {problem_description} {reference_answer} {student_answer}",  # noqa: E501
        temperature=0.7,
        max_trials=2,
    )


@pytest.fixture
def problem_data():
    """Create test problem data."""
    problem_id = ProblemID(chapter_id="1", problem_id="2", subproblem_id=["a", "b"])
    problem_description = Answer(answer="This is a test problem")
    reference_answer = Answer(answer="This is the reference answer")
    student_answer = Answer(answer="This is the student answer")

    # Add subproblem content
    problem_description.add_sub_answer("a", "Subproblem a description")
    problem_description.add_sub_answer("b", "Subproblem b description")

    reference_answer.add_sub_answer("a", "Reference answer to a")
    reference_answer.add_sub_answer("b", "Reference answer to b")

    student_answer.add_sub_answer("a", "Student answer to a")
    student_answer.add_sub_answer("b", "Student answer to b")

    return {
        "problem_id": problem_id,
        "problem_description": problem_description,
        "reference_answer": reference_answer,
        "student_answer": student_answer,
    }


@pytest.fixture
def mock_llm_responses():
    """Create mock LLM API responses."""
    first_response = MagicMock()
    first_response.choices = [MagicMock()]
    first_response.choices[0].message = MagicMock()
    first_response.choices[0].message.content = "First round response content"
    # Add reasoning_content attribute to the message
    first_response.choices[0].message.reasoning_content = "First round reasoning process"

    subprob_a_response = MagicMock()
    subprob_a_response.choices = [MagicMock()]
    subprob_a_response.choices[0].message = MagicMock()
    subprob_a_response.choices[0].message.content = "Subproblem a response content"
    # Add reasoning_content attribute to the message
    subprob_a_response.choices[0].message.reasoning_content = "Subproblem a reasoning process"

    subprob_b_response = MagicMock()
    subprob_b_response.choices = [MagicMock()]
    subprob_b_response.choices[0].message = MagicMock()
    subprob_b_response.choices[0].message.content = "Subproblem b response content"
    # Add reasoning_content attribute to the message
    subprob_b_response.choices[0].message.reasoning_content = "Subproblem b reasoning process"

    return {"first": first_response, "subprob_a": subprob_a_response, "subprob_b": subprob_b_response}


@pytest.mark.asyncio
async def test_mark_submission(llm_config, problem_data, mock_llm_responses):
    """Test the mark_submission method."""
    # Set up the interactor with a mocked client
    with patch("auto_marker.llm_interact.OpenAI") as mock_openai:
        # Configure the mock OpenAI client
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        interactor = LLMInteractor(llm_config)

        # Mock the _call_llm method to return predefined responses
        async def mock_call_llm(messages):
            print(messages)
            if len(interactor.messages) == 1:  # First call has only one message
                return mock_llm_responses["first"]
            elif "Subproblem a template" in str(messages[-1].get("content", "")):
                return mock_llm_responses["subprob_a"]
            else:
                return mock_llm_responses["subprob_b"]

        # Apply the mock to _call_llm
        with patch.object(interactor, "_call_llm", side_effect=mock_call_llm):
            # Set up logging path
            log_file = "./tests/auto_marker/test_log.log"
            log_path = str(log_file)

            # Call mark_submission
            result = await interactor.mark_problem(
                problem_data["problem_id"],
                problem_data["problem_description"],
                problem_data["reference_answer"],
                problem_data["student_answer"],
                logging_path=log_path,
            )

            # Verify the response is as expected
            assert result.answer == ""
            assert result.get_sub_answer("a") == "Subproblem a response content"
            assert result.get_sub_answer("b") == "Subproblem b response content"

            # Verify the messages list structure
            assert len(interactor.messages) == 6  # 3 pairs of user/assistant messages
            assert interactor.messages[0]["role"] == "user"
            assert interactor.messages[1]["role"] == "assistant"
            assert interactor.messages[1]["content"] == "First round response content"

            # Verify that logging occurred
            assert os.path.exists(log_path)
            with open(log_path) as f:
                log_content = f.read()
                # Check for expected content in the text log
                assert f"Problem ID: {problem_data['problem_id']}" in log_content
                assert "Round 1 starts" in log_content
                assert "First round response content" in log_content
                assert "Round 2 starts (Subproblem a)" in log_content
                assert "Subproblem a response content" in log_content
                assert "Round 3 starts (Subproblem b)" in log_content
                assert "Subproblem b response content" in log_content
                assert "User Message" in log_content
                assert "LLM Output" in log_content


@pytest.mark.asyncio
async def test_mark_submission_error_handling(llm_config, problem_data):
    """Test error handling in the mark_submission method."""
    # Set up the interactor with a mocked client
    with patch("auto_marker.llm_interact.OpenAI") as mock_openai:
        # Configure the mock OpenAI client
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        interactor = LLMInteractor(llm_config)

        # Mock _call_llm to raise an exception
        async def mock_call_llm_error(messages):
            raise Exception("API Error")

        # Apply the mock to _call_llm
        with patch.object(interactor, "_call_llm", side_effect=mock_call_llm_error):
            # Attempt to call mark_submission and expect an exception
            with pytest.raises(Exception, match="API Error"):
                await interactor.mark_problem(
                    problem_data["problem_id"],
                    problem_data["problem_description"],
                    problem_data["reference_answer"],
                    problem_data["student_answer"],
                )


@pytest.mark.asyncio
async def test_mark_submission_no_subproblems(llm_config, mock_llm_responses):
    """Test the mark_submission method with a problem that has no subproblems."""
    # Create a problem without subproblems
    problem_id = ProblemID(chapter_id="1", problem_id="3")
    problem_description = Answer(answer="Simple problem with no subproblems")
    reference_answer = Answer(answer="Simple reference answer")
    student_answer = Answer(answer="Simple student answer")

    # Set up the interactor with a mocked client
    with patch("auto_marker.llm_interact.OpenAI") as mock_openai:
        # Configure the mock OpenAI client
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        interactor = LLMInteractor(llm_config)

        # Mock the _call_llm method to return only first response (no subproblem calls)
        async def mock_call_llm(messages):
            return mock_llm_responses["first"]

        # Apply the mock to _call_llm
        with patch.object(interactor, "_call_llm", side_effect=mock_call_llm):
            # Call mark_submission
            result = await interactor.mark_problem(problem_id, problem_description, reference_answer, student_answer)

            # Verify the response is as expected
            assert result.answer == "First round response content"
            assert len(result.sub_answers) == 0  # No subproblem answers
            assert len(interactor.messages) == 2  # Just one pair of user/assistant messages
