from auto_marker.text_processor.tex_processor import parse_content
from auto_marker.basics import ProblemID, AnswerGroup
from unittest.mock import patch


def test_parse_content_empty_input():
    """Test parsing empty content."""
    content = ""
    problem_list = [ProblemID("一", "1")]
    result = parse_content(content, problem_list)
    assert isinstance(result, AnswerGroup)
    assert len(result) == 0


def test_parse_content_no_document():
    """Test parsing content without document environment."""
    content = r"\section{第一章作业} \item[1.]"
    problem_list = [ProblemID("一", "1")]
    result = parse_content(content, problem_list)
    assert isinstance(result, AnswerGroup)
    assert len(result) == 0


def test_parse_content_simple_document():
    """Test parsing a simple document with one problem."""
    content = r"\begin{document}\section{第一章作业}\begin{enumerate}\item[1.] Answer content\end{enumerate}\end{document}"
    problem_list = [ProblemID("1", "1")]

    result = parse_content(content, problem_list)

    assert isinstance(result, AnswerGroup)
    assert len(result) == 1
    assert problem_list[0] in result
    assert result[problem_list[0]].answer == "Answer content"


def test_parse_content_with_subproblems():
    """Test parsing content with problem that has subproblems."""
    content = r"""
    \begin{document}
    \section{第一章作业}
    \begin{enumerate}
    \item[1.] Main answer
    \begin{enumerate}
    \item Sub answer 1
    \item Sub answer 2
    \end{enumerate}
    \end{enumerate}
    \end{document}
    """

    problem_id = ProblemID("1", "1")
    problem_id.subproblem_id = ["1", "2"]
    problem_list = [problem_id]

    result = parse_content(content, problem_list)

    assert isinstance(result, AnswerGroup)
    assert len(result) == 1
    assert problem_id in result
    assert result[problem_id].answer == "Main answer"
    assert len(result[problem_id].sub_answers) == 2
    assert result[problem_id].sub_answers[0] == ("1", "Sub answer 1")
    assert result[problem_id].sub_answers[1] == ("2", "Sub answer 2")


def test_parse_content_multiple_chapters():
    """Test parsing content with multiple chapters."""
    content = r"""
    \begin{document}
    \section{第一章作业}
    \begin{enumerate}
    \item[1.] Chapter 1 answer
    \end{enumerate}
    \section{第二章作业}
    \begin{enumerate}
    \item[1.] Chapter 2 answer
    \end{enumerate}
    \end{document}
    """

    problem_list = [ProblemID("1", "1"), ProblemID("2", "1")]

    result = parse_content(content, problem_list)

    assert isinstance(result, AnswerGroup)
    assert len(result) == 2
    assert problem_list[0] in result
    assert problem_list[1] in result
    assert result[problem_list[0]].answer == "Chapter 1 answer"
    assert result[problem_list[1]].answer == "Chapter 2 answer"


def test_parse_content_problem_not_in_list():
    """Test parsing content with a problem not in the problem list."""
    content = r"""
    \begin{document}
    \section{第一章作业}
    \begin{enumerate}
    \item[1.] Problem 1
    \item[2.] Problem 2
    \end{enumerate}
    \end{document}
    """

    problem_list = [ProblemID("1", "1")]  # Only problem 1 is in the list

    with patch("builtins.print") as mock_print:
        result = parse_content(content, problem_list)

        mock_print.assert_called_once()
        assert "Warning: Problem ID 2 not found" in mock_print.call_args[0][0]

    assert isinstance(result, AnswerGroup)
    assert len(result) == 1
    assert problem_list[0] in result
    assert result[problem_list[0]].answer == "Problem 1"


def test_parse_content_extra_problem():
    """Test parsing content with an 'extra' problem."""
    content = r"""
    \begin{document}
    \section{第一章作业}
    \begin{enumerate}
    \item[1.] Regular problem
    \item[extra.] Extra problem
    \end{enumerate}
    \end{document}
    """

    problem_list = [ProblemID("1", "1"), ProblemID("1", "extra")]

    result = parse_content(content, problem_list)

    assert isinstance(result, AnswerGroup)
    assert len(result) == 2
    assert result[problem_list[0]].answer == "Regular problem"
    assert result[problem_list[1]].answer == "Extra problem"
