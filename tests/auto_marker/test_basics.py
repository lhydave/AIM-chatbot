import pytest
from auto_marker.basics import (
    parse_problem_list,
    parse_submission_title,
    filter_answers,
    ProblemID,
    AnswerGroup,
    Answer,
    StudentSubmission,
)


class TestProblemID:
    def test_problem_id_from_str_basic(self):
        """Test basic problem ID parsing without subproblems."""
        problem_id = ProblemID.from_str("chap1.prob1")
        assert problem_id.chapter_id == "1"
        assert problem_id.problem_id == "1"
        assert problem_id.subproblem_id == []

    def test_problem_id_from_str_with_subproblems(self):
        """Test problem ID parsing with subproblems."""
        problem_id = ProblemID.from_str("chap1.prob1(1)(2)")
        assert problem_id.chapter_id == "1"
        assert problem_id.problem_id == "1"
        assert problem_id.subproblem_id == ["1", "2"]

    def test_problem_id_from_str_with_single_subproblem(self):
        """Test problem ID parsing with a single subproblem."""
        problem_id = ProblemID.from_str("chap1.prob1(a)")
        assert problem_id.chapter_id == "1"
        assert problem_id.problem_id == "1"
        assert problem_id.subproblem_id == ["a"]

    def test_problem_id_from_str_complex_ids(self):
        """Test problem ID parsing with complex chapter and problem IDs."""
        problem_id = ProblemID.from_str("chap2A.prob3B(i)(ii)")
        assert problem_id.chapter_id == "2A"
        assert problem_id.problem_id == "3B"
        assert problem_id.subproblem_id == ["i", "ii"]

    def test_problem_id_from_str_invalid_format(self):
        """Test that invalid format raises ValueError."""
        with pytest.raises(ValueError) as excinfo:
            ProblemID.from_str("invalid_format")
        assert "Invalid problem ID format" in str(excinfo.value)

    def test_problem_id_from_str_empty_string(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError) as excinfo:
            ProblemID.from_str("")
        assert "Invalid problem ID format" in str(excinfo.value)

    def test_problem_id_from_str_missing_problem(self):
        """Test that missing problem component raises ValueError."""
        with pytest.raises(ValueError) as excinfo:
            ProblemID.from_str("chap1.")
        assert "Invalid problem ID format" in str(excinfo.value)


class TestParseProblemList:
    def test_parse_problem_list_basic(self):
        """Test basic parsing of problem list with simple chapters and problems."""
        problem_list = """
        chapter 1: 1,2,3
        chapter 2: 4,5,6
        """

        result = parse_problem_list(problem_list)

        expected = [
            ProblemID(chapter_id="1", problem_id="1"),
            ProblemID(chapter_id="1", problem_id="2"),
            ProblemID(chapter_id="1", problem_id="3"),
            ProblemID(chapter_id="2", problem_id="4"),
            ProblemID(chapter_id="2", problem_id="5"),
            ProblemID(chapter_id="2", problem_id="6"),
        ]

        assert result == expected

    def test_parse_problem_list_with_subproblems(self):
        """Test parsing problem list with subproblems."""
        problem_list = """
        chapter 1: 1,2(a)(b),3(c)
        """

        result = parse_problem_list(problem_list)

        expected = [
            ProblemID(chapter_id="1", problem_id="1"),
            ProblemID(chapter_id="1", problem_id="2", subproblem_id=["a", "b"]),
            ProblemID(chapter_id="1", problem_id="3", subproblem_id=["c"]),
        ]

        assert result == expected

    def test_parse_problem_list_empty_string(self):
        """Test parsing an empty problem list."""
        result = parse_problem_list("")
        assert result == []

    def test_parse_problem_list_with_spaces(self):
        """Test parsing problem list with extra whitespace."""
        problem_list = """
        chapter 1:   1, 2,  3
        """

        result = parse_problem_list(problem_list)

        expected = [
            ProblemID(chapter_id="1", problem_id="1"),
            ProblemID(chapter_id="1", problem_id="2"),
            ProblemID(chapter_id="1", problem_id="3"),
        ]

        assert result == expected

    def test_parse_problem_list_mixed_content(self):
        """Test parsing problem list with mixed valid and invalid lines."""
        problem_list = """
        This is an invalid line
        chapter 1: 1,2
        Another invalid line
        chapter 2: 3,4
        """

        result = parse_problem_list(problem_list)

        expected = [
            ProblemID(chapter_id="1", problem_id="1"),
            ProblemID(chapter_id="1", problem_id="2"),
            ProblemID(chapter_id="2", problem_id="3"),
            ProblemID(chapter_id="2", problem_id="4"),
        ]

        assert result == expected

    def test_parse_problem_list_complex_ids(self):
        """Test parsing problem list with complex IDs."""
        problem_list = """
        chapter A1: x1,y2,z3(a)(b)
        chapter B2: extra,special(i)(ii)
        """

        result = parse_problem_list(problem_list)

        expected = [
            ProblemID(chapter_id="A1", problem_id="x1"),
            ProblemID(chapter_id="A1", problem_id="y2"),
            ProblemID(chapter_id="A1", problem_id="z3", subproblem_id=["a", "b"]),
            ProblemID(chapter_id="B2", problem_id="extra"),
            ProblemID(chapter_id="B2", problem_id="special", subproblem_id=["i", "ii"]),
        ]

        assert result == expected


class TestAnswer:
    def test_answer_to_json_basic(self):
        """Test the basic to_json method of Answer."""
        answer = Answer(answer="Test answer")
        json_dict = answer.to_json()

        assert isinstance(json_dict, dict)
        assert json_dict["answer"] == "Test answer"
        assert json_dict.get("sub_answers") is None

    def test_answer_to_json_with_sub_answers(self):
        """Test to_json method with sub_answers."""
        answer = Answer(answer="Main answer")
        answer.add_sub_answer("a", "Sub-answer A")
        answer.add_sub_answer("b", "Sub-answer B")

        json_dict = answer.to_json()

        assert isinstance(json_dict, dict)
        assert json_dict["answer"] == "Main answer"
        assert len(json_dict["sub_answers"]) == 2
        assert json_dict["sub_answers"][0] == {"sub_id": "a", "sub_answer": "Sub-answer A"}
        assert json_dict["sub_answers"][1] == {"sub_id": "b", "sub_answer": "Sub-answer B"}

    def test_answer_from_json_basic(self):
        """Test creating an Answer object from JSON data."""
        json_dict = {"answer": "Test answer", "sub_answers": []}

        answer = Answer.from_json(json_dict)

        assert answer.answer == "Test answer"
        assert answer.sub_answers == []

    def test_answer_from_json_with_sub_answers(self):
        """Test creating an Answer with sub_answers from JSON data."""
        json_dict = {
            "answer": "Main answer",
            "sub_answers": [
                {"sub_id": "a", "sub_answer": "Sub-answer A"},
                {"sub_id": "b", "sub_answer": "Sub-answer B"},
            ],
        }

        answer = Answer.from_json(json_dict)

        assert answer.answer == "Main answer"
        assert len(answer.sub_answers) == 2
        assert answer.sub_answers[0] == ("a", "Sub-answer A")
        assert answer.sub_answers[1] == ("b", "Sub-answer B")

    def test_answer_roundtrip_json(self):
        """Test Answer object -> JSON -> Answer object roundtrip."""
        original = Answer(answer="Test answer")
        original.add_sub_answer("a", "Sub-answer A")

        json_dict = original.to_json()
        recreated = Answer.from_json(json_dict)

        assert recreated.answer == original.answer
        assert recreated.sub_answers == original.sub_answers


class TestAnswerGroup:
    def test_answer_group_initialization(self):
        """Test AnswerGroup initialization."""
        answer_group = AnswerGroup()
        assert len(answer_group) == 0

        # Test with initial data
        problem_id = ProblemID(chapter_id="1", problem_id="1")
        answer = Answer(answer="Test answer")
        answers = {problem_id: answer}
        answer_group = AnswerGroup(answers=answers)
        assert len(answer_group) == 1

    def test_answer_group_get_set_item(self):
        """Test getting and setting items in AnswerGroup."""
        answer_group = AnswerGroup()
        problem_id = ProblemID(chapter_id="1", problem_id="1")
        answer = Answer(answer="Test answer")

        # Test __setitem__
        answer_group[problem_id] = answer
        assert len(answer_group) == 1

        # Test __getitem__
        retrieved_answer = answer_group[problem_id]
        assert retrieved_answer.answer == "Test answer"
        assert retrieved_answer.sub_answers == []

    def test_answer_group_contains(self):
        """Test the __contains__ method of AnswerGroup."""
        answer_group = AnswerGroup()
        problem_id1 = ProblemID(chapter_id="1", problem_id="1")
        problem_id2 = ProblemID(chapter_id="1", problem_id="2")
        answer = Answer(answer="Test answer")

        answer_group[problem_id1] = answer
        assert problem_id1 in answer_group
        assert problem_id2 not in answer_group

    def test_answer_group_add_answer(self):
        """Test adding answers to AnswerGroup."""
        answer_group = AnswerGroup()
        problem_id = ProblemID(chapter_id="1", problem_id="1")

        answer_group.add_answer(problem_id, "Test answer")
        assert problem_id in answer_group
        assert answer_group[problem_id].answer == "Test answer"
        assert answer_group[problem_id].sub_answers == []

    def test_answer_group_add_sub_answer(self):
        """Test adding sub-answers to AnswerGroup."""
        answer_group = AnswerGroup()
        problem_id = ProblemID(chapter_id="1", problem_id="1")

        # Adding a sub-answer to a non-existing problem should create the problem
        answer_group.add_sub_answer(problem_id, "a", "Sub-answer 1")
        assert problem_id in answer_group
        assert answer_group[problem_id].answer == ""
        assert len(answer_group[problem_id].sub_answers) == 1
        assert answer_group[problem_id].sub_answers[0] == ("a", "Sub-answer 1")

        # Adding another sub-answer
        answer_group.add_sub_answer(problem_id, "b", "Sub-answer 2")
        assert len(answer_group[problem_id].sub_answers) == 2
        assert answer_group[problem_id].sub_answers[1] == ("b", "Sub-answer 2")

    def test_answer_group_get(self):
        """Test the get method of AnswerGroup."""
        answer_group = AnswerGroup()
        problem_id1 = ProblemID(chapter_id="1", problem_id="1")
        problem_id2 = ProblemID(chapter_id="1", problem_id="2")
        answer = Answer(answer="Test answer")

        answer_group[problem_id1] = answer

        # Test get with existing key
        retrieved_answer = answer_group.get(problem_id1)
        assert retrieved_answer is not None
        assert retrieved_answer.answer == "Test answer"

        # Test get with non-existing key and default
        default_answer = Answer(answer="Default")
        retrieved_answer = answer_group.get(problem_id2, default_answer)
        assert retrieved_answer is not None
        assert retrieved_answer.answer == "Default"

        # Test get with non-existing key and no default
        retrieved_answer = answer_group.get(problem_id2)
        assert retrieved_answer is None

    def test_answer_group_dict_methods(self):
        """Test the dictionary-like methods of AnswerGroup (items, keys, values)."""
        answer_group = AnswerGroup()
        problem_id1 = ProblemID(chapter_id="1", problem_id="1")
        problem_id2 = ProblemID(chapter_id="1", problem_id="2")
        answer1 = Answer(answer="Test answer 1")
        answer2 = Answer(answer="Test answer 2")

        answer_group[problem_id1] = answer1
        answer_group[problem_id2] = answer2

        # Test keys
        keys = list(answer_group.keys())
        assert len(keys) == 2
        assert problem_id1 in keys
        assert problem_id2 in keys

        # Test values
        values = list(answer_group.values())
        assert len(values) == 2
        assert any(v.answer == "Test answer 1" for v in values)
        assert any(v.answer == "Test answer 2" for v in values)

        # Test items
        items = list(answer_group.items())
        assert len(items) == 2
        assert any(k == problem_id1 and v.answer == "Test answer 1" for k, v in items)
        assert any(k == problem_id2 and v.answer == "Test answer 2" for k, v in items)

    def test_answer_group_to_json_empty(self):
        """Test to_json method of AnswerGroup with no answers."""
        answer_group = AnswerGroup()
        json_dict = answer_group.to_json()

        assert isinstance(json_dict, dict)
        assert "answers" in json_dict
        assert json_dict["answers"] == []

    def test_answer_group_to_json_basic(self):
        """Test the basic to_json method of AnswerGroup."""
        answer_group = AnswerGroup()
        problem_id = ProblemID(chapter_id="1", problem_id="1")
        answer = Answer(answer="Test answer")
        answer_group[problem_id] = answer

        json_dict = answer_group.to_json()

        assert isinstance(json_dict, dict)
        assert "answers" in json_dict
        assert len(json_dict["answers"]) == 1
        assert json_dict["answers"][0]["problem_id"] == "chap1.prob1"
        assert json_dict["answers"][0]["answer"]["answer"] == "Test answer"
        assert json_dict["answers"][0]["answer"].get("sub_answers") is None

    def test_answer_group_to_json_multiple_problems(self):
        """Test to_json with multiple problems in sorted order."""
        answer_group = AnswerGroup()

        # Add problems in non-sorted order
        problem_id2 = ProblemID(chapter_id="1", problem_id="2")
        problem_id1 = ProblemID(chapter_id="1", problem_id="1")
        problem_id3 = ProblemID(chapter_id="2", problem_id="1")

        answer_group[problem_id2] = Answer(answer="Answer 2")
        answer_group[problem_id1] = Answer(answer="Answer 1")
        answer_group[problem_id3] = Answer(answer="Answer 3")

        json_dict = answer_group.to_json()

        # Check that the problems are sorted correctly
        assert len(json_dict["answers"]) == 3
        assert json_dict["answers"][0]["problem_id"] == "chap1.prob1"
        assert json_dict["answers"][1]["problem_id"] == "chap1.prob2"
        assert json_dict["answers"][2]["problem_id"] == "chap2.prob1"

    def test_answer_group_to_json_with_subproblems(self):
        """Test to_json with problems containing subproblems."""
        answer_group = AnswerGroup()
        problem_id = ProblemID(chapter_id="1", problem_id="1", subproblem_id=["a", "b"])

        answer = Answer(answer="Main answer")
        answer.add_sub_answer("a", "Sub-answer A")
        answer.add_sub_answer("b", "Sub-answer B")

        answer_group[problem_id] = answer

        json_dict = answer_group.to_json()

        assert len(json_dict["answers"]) == 1
        assert json_dict["answers"][0]["problem_id"] == "chap1.prob1(a)(b)"
        assert json_dict["answers"][0]["answer"]["answer"] == "Main answer"
        assert len(json_dict["answers"][0]["answer"]["sub_answers"]) == 2
        assert json_dict["answers"][0]["answer"]["sub_answers"][0] == {"sub_id": "a", "sub_answer": "Sub-answer A"}
        assert json_dict["answers"][0]["answer"]["sub_answers"][1] == {"sub_id": "b", "sub_answer": "Sub-answer B"}

    def test_answer_group_from_json_basic(self):
        """Test creating an AnswerGroup from JSON data."""
        json_dict = {
            "answers": [
                {
                    "problem_id": "chap1.prob1",
                    "answer": {"answer": "Test answer", "sub_answers": []},
                }
            ]
        }

        answer_group = AnswerGroup.from_json(json_dict)

        assert len(answer_group) == 1
        problem_id = ProblemID(chapter_id="1", problem_id="1")
        assert problem_id in answer_group
        assert answer_group[problem_id].answer == "Test answer"
        assert answer_group[problem_id].sub_answers == []

    def test_answer_group_roundtrip_json(self):
        """Test AnswerGroup -> JSON -> AnswerGroup roundtrip."""
        original = AnswerGroup()
        problem_id1 = ProblemID(chapter_id="1", problem_id="1")
        problem_id2 = ProblemID(chapter_id="2", problem_id="1", subproblem_id=["a"])

        original[problem_id1] = Answer(answer="Answer 1")

        answer2 = Answer(answer="Answer 2")
        answer2.add_sub_answer("a", "Sub-answer A")
        original[problem_id2] = answer2

        # Convert to JSON and back
        json_dict = original.to_json()
        recreated = AnswerGroup.from_json(json_dict)

        # Verify the recreated object
        assert len(recreated) == 2
        assert problem_id1 in recreated
        assert problem_id2 in recreated
        assert recreated[problem_id1].answer == "Answer 1"
        assert recreated[problem_id2].answer == "Answer 2"
        assert len(recreated[problem_id2].sub_answers) == 1
        assert recreated[problem_id2].sub_answers[0] == ("a", "Sub-answer A")


class TestStudentSubmission:
    def test_student_submission_to_json_basic(self):
        """Test basic to_json method of StudentSubmission without processed_source_code."""

        submission = StudentSubmission(
            homework_id="1",
            student_id="2300017001",
            student_name="Test Student",
            submission_number="1",
            raw_source_code="# Test code",
            code_language="markdown",
        )

        json_dict = submission.to_json()

        assert isinstance(json_dict, dict)
        assert json_dict["homework_id"] == "1"
        assert json_dict["student_id"] == "2300017001"
        assert json_dict["student_name"] == "Test Student"
        assert json_dict["submission_number"] == "1"
        assert json_dict["raw_source_code"] == "# Test code"
        assert json_dict["code_language"] == "markdown"
        assert "processed_source_code" not in json_dict

    def test_student_submission_to_json_with_processed_code(self):
        """Test to_json method with processed_source_code."""

        answer_group = AnswerGroup()
        problem_id = ProblemID(chapter_id="1", problem_id="1")
        answer = Answer(answer="Test answer")
        answer_group[problem_id] = answer

        submission = StudentSubmission(
            homework_id="2",
            student_id="2300017002",
            student_name="Another Student",
            submission_number="2",
            raw_source_code="# More code",
            code_language="tex",
            processed_source_code=answer_group,
        )

        json_dict = submission.to_json()

        assert isinstance(json_dict, dict)
        assert json_dict["homework_id"] == "2"
        assert json_dict["student_id"] == "2300017002"
        assert json_dict["student_name"] == "Another Student"
        assert json_dict["submission_number"] == "2"
        assert json_dict["raw_source_code"] == "# More code"
        assert json_dict["code_language"] == "tex"
        assert "processed_source_code" in json_dict
        assert isinstance(json_dict["processed_source_code"], dict)
        assert "answers" in json_dict["processed_source_code"]
        assert len(json_dict["processed_source_code"]["answers"]) == 1
        assert json_dict["processed_source_code"]["answers"][0]["problem_id"] == "chap1.prob1"

    def test_student_submission_from_json_basic(self):
        """Test creating a StudentSubmission from JSON data without processed_source_code."""

        json_dict = {
            "homework_id": "3",
            "student_id": "2300017003",
            "student_name": "Third Student",
            "submission_number": "3",
            "raw_source_code": "function test() {}",
            "code_language": "markdown",
        }

        submission = StudentSubmission.from_json(json_dict)

        assert submission.homework_id == "3"
        assert submission.student_id == "2300017003"
        assert submission.student_name == "Third Student"
        assert submission.submission_number == "3"
        assert submission.raw_source_code == "function test() {}"
        assert submission.code_language == "markdown"
        assert submission.processed_source_code is None

    def test_student_submission_from_json_with_processed_code(self):
        """Test creating a StudentSubmission from JSON data with processed_source_code."""

        json_dict = {
            "homework_id": "4",
            "student_id": "2300017004",
            "student_name": "Fourth Student",
            "submission_number": "4",
            "raw_source_code": "# Python code",
            "code_language": "tex",
            "processed_source_code": {
                "answers": [
                    {
                        "problem_id": "chap2.prob3",
                        "answer": {
                            "answer": "Main answer",
                            "sub_answers": [{"sub_id": "a", "sub_answer": "Sub answer A"}],
                        },
                    }
                ]
            },
        }

        submission = StudentSubmission.from_json(json_dict)

        assert submission.homework_id == "4"
        assert submission.student_id == "2300017004"
        assert submission.student_name == "Fourth Student"
        assert submission.submission_number == "4"
        assert submission.raw_source_code == "# Python code"
        assert submission.code_language == "tex"
        assert submission.processed_source_code is not None
        assert len(submission.processed_source_code) == 1

        problem_id = ProblemID(chapter_id="2", problem_id="3")
        assert problem_id in submission.processed_source_code
        assert submission.processed_source_code[problem_id].answer == "Main answer"
        assert len(submission.processed_source_code[problem_id].sub_answers) == 1
        assert submission.processed_source_code[problem_id].sub_answers[0] == (
            "a",
            "Sub answer A",
        )


def test_parse_submission_title_basic():
    """Test basic submission title parsing with standard format."""

    homework_id, student_id, student_name = parse_submission_title("HW1-2300017000-李二")

    assert homework_id == "1"
    assert student_id == "2300017000"
    assert student_name == "李二"


def test_parse_submission_title_variations():
    """Test parsing with different format variations."""

    # Test with lowercase hw
    hw_id, student_id, student_name = parse_submission_title("hw2-2300017001-张三")
    assert hw_id == "2"
    assert student_id == "2300017001"
    assert student_name == "张三"

    # Test with brackets
    hw_id, student_id, student_name = parse_submission_title("HW[3]-2300017002-王五")
    assert hw_id == "3"
    assert student_id == "2300017002"
    assert student_name == "王五"

    # Test with underscore separator
    hw_id, student_id, student_name = parse_submission_title("HW4_2300017003_李四")
    assert hw_id == "4"
    assert student_id == "2300017003"
    assert student_name == "李四"


def test_parse_submission_title_complex_name():
    """Test parsing with a complex student name."""

    hw_id, student_id, student_name = parse_submission_title("HW1-2300017004-John Doe")
    assert hw_id == "1"
    assert student_id == "2300017004"
    assert student_name == "John Doe"


def test_parse_submission_title_invalid_format():
    """Test that invalid format raises ValueError."""

    with pytest.raises(ValueError) as excinfo:
        parse_submission_title("invalid_format")
    assert "Invalid submission title format" in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo:
        parse_submission_title("H1-12345-name")
    assert "Invalid submission title format" in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo:
        parse_submission_title("")
    assert "Invalid submission title format" in str(excinfo.value)


class TestFilterAnswers:
    def test_filter_answers_basic(self):
        """Test basic filtering where all problems exist."""
        # Create an answer group with some answers
        answer_group = AnswerGroup()
        problem_id1 = ProblemID(chapter_id="1", problem_id="1")
        problem_id2 = ProblemID(chapter_id="1", problem_id="2")
        answer_group[problem_id1] = Answer(answer="Answer 1")
        answer_group[problem_id2] = Answer(answer="Answer 2")

        # Filter with a list that includes all problems
        problem_id_list = [problem_id1, problem_id2]
        filtered = filter_answers(problem_id_list, answer_group)

        # Verify the filtered result
        assert len(filtered) == 2
        assert problem_id1 in filtered
        assert problem_id2 in filtered
        assert filtered[problem_id1].answer == "Answer 1"
        assert filtered[problem_id2].answer == "Answer 2"

    def test_filter_answers_missing_problem(self):
        """Test filtering with a problem that doesn't exist in the answer group."""
        # Create an answer group with one answer
        answer_group = AnswerGroup()
        problem_id1 = ProblemID(chapter_id="1", problem_id="1")
        answer_group[problem_id1] = Answer(answer="Answer 1")

        # Filter with a list that includes a missing problem
        problem_id2 = ProblemID(chapter_id="1", problem_id="2")
        problem_id_list = [problem_id1, problem_id2]
        filtered = filter_answers(problem_id_list, answer_group)

        # Verify the filtered result
        assert len(filtered) == 2
        assert problem_id1 in filtered
        assert problem_id2 in filtered
        assert filtered[problem_id1].answer == "Answer 1"
        assert filtered[problem_id2].answer == "No answer provided"

    def test_filter_answers_custom_default(self):
        """Test filtering with a custom default answer."""
        # Create an answer group with one answer
        answer_group = AnswerGroup()
        problem_id1 = ProblemID(chapter_id="1", problem_id="1")
        answer_group[problem_id1] = Answer(answer="Answer 1")

        # Filter with a list that includes a missing problem and a custom default
        problem_id2 = ProblemID(chapter_id="1", problem_id="2")
        problem_id_list = [problem_id1, problem_id2]
        custom_default = "Custom default answer"
        filtered = filter_answers(problem_id_list, answer_group, custom_default)

        # Verify the filtered result
        assert len(filtered) == 2
        assert problem_id1 in filtered
        assert problem_id2 in filtered
        assert filtered[problem_id1].answer == "Answer 1"
        assert filtered[problem_id2].answer == custom_default

    def test_filter_answers_with_subproblems(self):
        """Test filtering with problems that have subproblems."""
        # Create an answer group with problems that have subproblems
        answer_group = AnswerGroup()
        problem_id1 = ProblemID(chapter_id="1", problem_id="1", subproblem_id=["a", "b"])
        answer1 = Answer(answer="Main answer 1")
        answer1.add_sub_answer("a", "Sub-answer 1a")
        answer1.add_sub_answer("b", "Sub-answer 1b")
        answer_group[problem_id1] = answer1

        # Filter with matching problem ID and subproblem IDs
        filtered = filter_answers([problem_id1], answer_group)

        # Verify the filtered result
        assert len(filtered) == 1
        assert problem_id1 in filtered
        assert filtered[problem_id1].answer == "Main answer 1"
        assert len(filtered[problem_id1].sub_answers) == 2
        assert filtered[problem_id1].get_sub_answer("a") == "Sub-answer 1a"
        assert filtered[problem_id1].get_sub_answer("b") == "Sub-answer 1b"

    def test_filter_answers_missing_subproblem(self):
        """Test filtering with a problem that has subproblems where some are missing."""
        # Create an answer group with a problem that has subproblems
        answer_group = AnswerGroup()
        problem_id1 = ProblemID(chapter_id="1", problem_id="1", subproblem_id=["a"])
        answer1 = Answer(answer="Main answer 1")
        answer1.add_sub_answer("a", "Sub-answer 1a")
        answer_group[problem_id1] = answer1

        # Filter with a problem that has an additional subproblem
        filter_problem_id = ProblemID(chapter_id="1", problem_id="1", subproblem_id=["a", "b"])
        filtered = filter_answers([filter_problem_id], answer_group)

        # Verify the filtered result
        assert len(filtered) == 1
        assert filter_problem_id in filtered
        assert filtered[filter_problem_id].answer == "Main answer 1"
        assert len(filtered[filter_problem_id].sub_answers) == 2
        assert filtered[filter_problem_id].get_sub_answer("a") == "Sub-answer 1a"
        assert filtered[filter_problem_id].get_sub_answer("b") == "No answer provided"

    def test_filter_answers_extra_problems(self):
        """Test filtering with a list that excludes some problems from the answer group."""
        # Create an answer group with multiple answers
        answer_group = AnswerGroup()
        problem_id1 = ProblemID(chapter_id="1", problem_id="1")
        problem_id2 = ProblemID(chapter_id="1", problem_id="2")
        problem_id3 = ProblemID(chapter_id="1", problem_id="3")
        answer_group[problem_id1] = Answer(answer="Answer 1")
        answer_group[problem_id2] = Answer(answer="Answer 2")
        answer_group[problem_id3] = Answer(answer="Answer 3")

        # Filter with a list that only includes some problems
        problem_id_list = [problem_id1, problem_id3]
        filtered = filter_answers(problem_id_list, answer_group)

        # Verify the filtered result
        assert len(filtered) == 2
        assert problem_id1 in filtered
        assert problem_id3 in filtered
        assert problem_id2 not in filtered
        assert filtered[problem_id1].answer == "Answer 1"
        assert filtered[problem_id3].answer == "Answer 3"


class TestAnswerGroupToMarkdownStr:
    def test_basic(self):
        """Test basic to_markdown_str method of AnswerGroup with single chapter."""
        answer_group = AnswerGroup()
        problem_id1 = ProblemID(chapter_id="1", problem_id="1")
        problem_id2 = ProblemID(chapter_id="1", problem_id="2")

        answer_group[problem_id1] = Answer(answer="Answer 1")
        answer_group[problem_id2] = Answer(answer="Answer 2")

        markdown_str = answer_group.to_markdown_str()

        assert "## answer for Chapter 1" in markdown_str
        assert "## answer to chap1.prob1" in markdown_str
        assert "## answer to chap1.prob2" in markdown_str
        assert "Answer 1" in markdown_str
        assert "Answer 2" in markdown_str

    def test_multiple_chapters(self):
        """Test to_markdown_str with multiple chapters."""
        answer_group = AnswerGroup()
        problem_id1 = ProblemID(chapter_id="1", problem_id="1")
        problem_id2 = ProblemID(chapter_id="2", problem_id="1")

        answer_group[problem_id1] = Answer(answer="Answer for chapter 1")
        answer_group[problem_id2] = Answer(answer="Answer for chapter 2")

        markdown_str = answer_group.to_markdown_str()

        assert "## answer for Chapter 1" in markdown_str
        assert "## answer for Chapter 2" in markdown_str
        assert "## answer to chap1.prob1" in markdown_str
        assert "## answer to chap2.prob1" in markdown_str
        assert "Answer for chapter 1" in markdown_str
        assert "Answer for chapter 2" in markdown_str

    def test_custom_answer_name(self):
        """Test to_markdown_str with custom answer name."""
        answer_group = AnswerGroup()
        problem_id = ProblemID(chapter_id="1", problem_id="1")

        answer_group[problem_id] = Answer(answer="My answer")

        markdown_str = answer_group.to_markdown_str(answer_name="solution")

        assert "## solution for Chapter 1" in markdown_str
        assert "## solution to chap1.prob1" in markdown_str
        assert "My answer" in markdown_str

    def test_with_subproblems(self):
        """Test to_markdown_str with problems containing subproblems."""
        answer_group = AnswerGroup()
        problem_id = ProblemID(chapter_id="1", problem_id="1")

        answer = Answer(answer="Main answer")
        answer.add_sub_answer("a", "Sub-answer A")
        answer.add_sub_answer("b", "Sub-answer B")
        answer_group[problem_id] = answer

        markdown_str = answer_group.to_markdown_str()

        assert "## answer for Chapter 1" in markdown_str
        assert "## answer to chap1.prob1" in markdown_str
        assert "Main answer" in markdown_str
        assert "#### answer to (a)" in markdown_str
        assert "Sub-answer A" in markdown_str
        assert "#### answer to (b)" in markdown_str
        assert "Sub-answer B" in markdown_str

    def test_empty(self):
        """Test to_markdown_str with an empty answer group."""
        answer_group = AnswerGroup()
        markdown_str = answer_group.to_markdown_str()

        assert markdown_str == ""

    def test_complex_sorting(self):
        """Test to_markdown_str with mixed numeric and alphabetic chapter IDs."""
        answer_group = AnswerGroup()

        # Add in non-sorted order
        problem_id1 = ProblemID(chapter_id="2", problem_id="1")
        problem_id2 = ProblemID(chapter_id="10", problem_id="1")
        problem_id3 = ProblemID(chapter_id="1", problem_id="1")

        answer_group[problem_id1] = Answer(answer="Chapter 2 answer")
        answer_group[problem_id2] = Answer(answer="Chapter 10 answer")
        answer_group[problem_id3] = Answer(answer="Chapter 1 answer")

        markdown_str = answer_group.to_markdown_str()

        # Check order in the output (Chapter 1, 2, then 10)
        chapter1_pos = markdown_str.find("Chapter 1 answer")
        chapter2_pos = markdown_str.find("Chapter 2 answer")
        chapter10_pos = markdown_str.find("Chapter 10 answer")

        assert chapter1_pos < chapter2_pos < chapter10_pos
