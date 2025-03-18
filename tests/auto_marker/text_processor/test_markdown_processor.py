from auto_marker.text_processor.markdown_processor import parse_content
from auto_marker.basics import ProblemID, AnswerGroup


def test_parse_content_empty():
    content = ""
    result = parse_content(content)
    assert isinstance(result, AnswerGroup)
    assert len(result) == 0


def test_parse_content_single_chapter_problem():
    content = """
## 第一章
### 1. Problem Title
This is the answer to problem 1.
"""
    result = parse_content(content)
    assert len(result) == 1
    problem_id = ProblemID.from_str("chap1.prob1")
    assert problem_id in result
    assert result[problem_id].answer == "This is the answer to problem 1."
    assert len(result[problem_id].sub_answers) == 0


def test_parse_content_multiple_problems():
    content = """
## 第二章
### 1. First Problem
Answer to first problem.

### 2. Second Problem
Answer to second problem.

### extra. Extra Problem
Extra answer.
"""
    result = parse_content(content)
    assert len(result) == 3

    assert ProblemID.from_str("chap2.prob1") in result
    assert (
        result[ProblemID.from_str("chap2.prob1")].answer == "Answer to first problem."
    )

    assert ProblemID.from_str("chap2.prob2") in result
    assert (
        result[ProblemID.from_str("chap2.prob2")].answer == "Answer to second problem."
    )

    assert ProblemID.from_str("chap2.probextra") in result
    assert result[ProblemID.from_str("chap2.probextra")].answer == "Extra answer."


def test_parse_content_with_subproblems():
    content = """
## 第三章
### 1. Problem with Subproblems
Main problem answer.

#### (a)
Answer to subproblem a.

#### (b)
Answer to subproblem b.
"""
    result = parse_content(content)
    assert len(result) == 1

    problem_id = ProblemID.from_str("chap3.prob1(a)(b)")
    assert problem_id in result
    assert result[problem_id].answer == "Main problem answer."
    assert len(result[problem_id].sub_answers) == 2
    assert result[problem_id].sub_answers[0] == ("a", "Answer to subproblem a.")
    assert result[problem_id].sub_answers[1] == ("b", "Answer to subproblem b.")


def test_parse_content_multiple_chapters():
    content = """
## 第一章
### 1. Problem in Chapter 1
Answer in chapter 1.

## 第二章
### 1. Problem in Chapter 2
Answer in chapter 2.
"""
    result = parse_content(content)
    assert len(result) == 2

    assert ProblemID.from_str("chap1.prob1") in result
    assert result[ProblemID.from_str("chap1.prob1")].answer == "Answer in chapter 1."

    assert ProblemID.from_str("chap2.prob1") in result
    assert result[ProblemID.from_str("chap2.prob1")].answer == "Answer in chapter 2."


def test_parse_content_with_complex_chapter_name():
    content = """
## 第二章: Complex Title
### 1. Problem Title
Problem answer.
"""
    result = parse_content(content)
    assert len(result) == 1
    assert ProblemID.from_str("chap2.prob1") in result
    assert result[ProblemID.from_str("chap2.prob1")].answer == "Problem answer."


def test_parse_content_complex_structure():
    content = """
## 第四章
### 1. Problem with intro and subproblems
This is the introduction.

#### (a)
Answer to 4.1.a

#### (b)
Answer to 4.1.b

### 2. Another problem
Just a regular answer.

## 第五章
### extra. Special problem
Special answer.
"""
    result = parse_content(content)
    assert len(result) == 3

    # Check chapter 4, problem 1 with subproblems
    problem_id_1 = ProblemID.from_str("chap4.prob1(a)(b)")
    assert problem_id_1 in result
    assert result[problem_id_1].answer == "This is the introduction."
    assert result[problem_id_1].sub_answers[0] == ("a", "Answer to 4.1.a")
    assert result[problem_id_1].sub_answers[1] == ("b", "Answer to 4.1.b")

    # Check chapter 4, problem 2
    assert ProblemID.from_str("chap4.prob2") in result
    assert result[ProblemID.from_str("chap4.prob2")].answer == "Just a regular answer."

    # Check chapter 5, extra problem
    assert ProblemID.from_str("chap5.probextra") in result
    assert result[ProblemID.from_str("chap5.probextra")].answer == "Special answer."


def test_parse_content_arabic_chapter_number():
    content = """
## 第10章
### 1. Problem in Arabic Numbered Chapter
Answer to the problem.
"""
    result = parse_content(content)
    assert len(result) == 1
    assert ProblemID.from_str("chap10.prob1") in result
    assert result[ProblemID.from_str("chap10.prob1")].answer == "Answer to the problem."
