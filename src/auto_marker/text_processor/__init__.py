from . import markdown_processor
from . import tex_processor
from auto_marker.basics import ProblemID,AnswerGroup
from typing import Literal


def parse_content(
    content: str, lang: Literal["markdown", "tex"], problem_list: list[ProblemID]
) -> AnswerGroup:
    """
    Parse the content of a Markdown or LaTeX file and extract answers based on the problem list.

    Args:
        content: The content of the file to parse
        lang: The language of the file, either "markdown" or "tex"

    Returns:
        An AnswerGroup object containing the extracted answers
    """
    if lang == "markdown":
        return markdown_processor.parse_content(content)
    elif lang == "tex":
        return tex_processor.parse_content(content, problem_list)
    else:
        raise ValueError(f"Unsupported language: {lang}")
