from . import markdown_processor
from . import tex_processor
from auto_marker.basics import ProblemID, AnswerGroup, filter_answers
from auto_marker.logging import logger
from typing import Literal


def parse_content_with_filter(
    content: str, lang: Literal["markdown", "tex"], problem_list: list[ProblemID]
) -> AnswerGroup:
    """
    Parse the content of a file and filter out the answers that are not in the problem_list

    Args:
        content: The content of the file to parse
        lang: The language of the file, either "markdown" or "tex"

    Returns:
        The parsed content
    """
    ret: AnswerGroup
    if lang == "markdown":
        logger.info("Parsing content with markdown processor...")
        ret = markdown_processor.parse_content(content)
    elif lang == "tex":
        logger.info("Parsing content with tex processor...")
        ret = tex_processor.parse_content(content, problem_list)
    else:
        logger.error(f"Unsupported language: {lang}")
        raise ValueError(f"Unsupported language: {lang}")

    logger.info(f"Parse succeeded with {len(ret)} answers")

    logger.info("Filtering answers...")

    ret = filter_answers(problem_list, ret)

    logger.info("Filter succeeded")

    return ret
