from auto_marker.text_processor.tex_processor import parse_content, _find_last_matching_environment
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
    content = (
        r"\begin{document}\section{第一章作业}\begin{enumerate}\item[1.] Answer content\end{enumerate}\end{document}"
    )
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


def test_find_last_matching_environment_simple():
    """Test finding the last matching environment in a simple case."""

    text = r"\begin{itemize}Item 1\end{itemize} Other text \begin{itemize}Item 2\end{itemize}"
    start_pos, end_pos, content = _find_last_matching_environment(text, "itemize")

    assert content == "Item 2"
    assert text[start_pos : end_pos + 1] == r"\begin{itemize}Item 2\end{itemize}"


def test_find_last_matching_environment_nested():
    """Test finding the last matching environment with nested environments."""

    text = r"\begin{enumerate}\begin{itemize}Nested\end{itemize}\end{enumerate} \begin{itemize}Last one\end{itemize}"
    start_pos, end_pos, content = _find_last_matching_environment(text, "itemize")

    assert content == "Last one"
    assert text[start_pos : end_pos + 1] == r"\begin{itemize}Last one\end{itemize}"


def test_find_last_matching_environment_not_found():
    """Test when no matching environment is found."""

    text = r"No environment here"
    start_pos, end_pos, content = _find_last_matching_environment(text, "itemize")

    assert start_pos == -1
    assert end_pos == -1
    assert content == ""


def test_find_last_matching_environment_with_start_pos():
    """Test finding the last environment with a specific start position."""

    text = r"\begin{itemize}First\end{itemize} Middle \begin{itemize}Last\end{itemize}"
    # Start after the first itemize environment
    start_pos = text.find("Middle")
    start_pos, end_pos, content = _find_last_matching_environment(text, "itemize", start_pos)

    assert content == "Last"
    assert text[start_pos : end_pos + 1] == r"\begin{itemize}Last\end{itemize}"


def test_find_last_matching_environment_with_same_type():
    """Test finding the last of multiple environments of the same type."""

    text = r"\begin{itemize}First\end{itemize} \begin{itemize}Second\end{itemize} \begin{itemize}Third\end{itemize}"
    start_pos, end_pos, content = _find_last_matching_environment(text, "itemize")

    assert content == "Third"
    assert text[start_pos : end_pos + 1] == r"\begin{itemize}Third\end{itemize}"
