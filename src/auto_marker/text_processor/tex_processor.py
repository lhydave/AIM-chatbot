import re
from auto_marker.basics import ProblemID, AnswerGroup, Answer
from auto_marker.text_processor.utils import extract_chapter_id, extract_problem_id
from auto_marker.logging import logger


def parse_content(content: str, problem_list: list[ProblemID]) -> AnswerGroup:
    """
    Parse the content of a LaTeX file and extract answers based on the problem list.

    Args:
        content: The content of the LaTeX file to parse
        problem_list: The list of problems to extract

    Returns:
        An AnswerGroup object containing the extracted answers
    """
    logger.debug("Starting to parse content with %d problems in problem_list", len(problem_list))
    ret = AnswerGroup()

    # Extract the document body (between \begin{document} and \end{document})
    document_match = re.search(r"\\begin{document}(.*?)\\end{document}", content, re.DOTALL | re.MULTILINE)
    if not document_match:
        logger.debug("No document environment found in the content")
        return ret

    document_content = document_match.group(1)
    logger.debug("Extracted document content with length %d", len(document_content))

    # Extract sections (chapters)
    chapters = _extract_chapters(document_content)
    logger.debug("Extracted %d chapters from document", len(chapters))

    # Process each chapter
    for chapter_id, chapter_content in chapters:
        logger.debug("Processing chapter %s with content length %d", chapter_id, len(chapter_content))

        # Extract problems from the chapter
        problems = _extract_problems(chapter_content)
        logger.debug("Extracted %d problems from chapter %s", len(problems), chapter_id)

        for problem_id_str, problem_content in problems:
            # Process each problem
            logger.debug("Looking for problem ID %s in chapter %s", problem_id_str, chapter_id)
            problem_id = ProblemID.find_problem_id(problem_list, chapter_id, problem_id_str)
            if not problem_id:
                logger.debug(
                    "Problem ID %s not found in problem list when processing chapter %s", problem_id_str, chapter_id
                )
                print(
                    f"Warning: Problem ID {problem_id_str} not found in problem list when processing chapter {chapter_id}"  # noqa: E501
                )
                continue

            logger.debug("Processing problem %s", problem_id)
            # Process the problem content to extract main answer and subproblems
            answer_content = _process_problem(problem_content, problem_id)
            ret[problem_id] = answer_content
            logger.debug("Added answer for problem %s", problem_id)

    logger.debug("Completed parsing content, extracted %d answers", len(ret))
    return ret


def _extract_chapters(document_content: str) -> list[tuple[str, str]]:
    """
    Extract chapters (sections) from the document content.

    Args:
        document_content: The content of the document body

    Returns:
        List of tuples (chapter_id, chapter_content)
    """
    # Match section commands
    section_pattern = r"\\section{([^}]*)}(.*?)(?=\\section{|\Z)"
    sections = re.finditer(section_pattern, document_content, re.DOTALL | re.MULTILINE)

    chapters = []
    for section in sections:
        # Extract chapter ID from section title (e.g., "第一章作业" -> "一")
        section_title = section.group(1)
        chapter_id = extract_chapter_id(section_title)

        chapter_content = section.group(2).strip()
        chapters.append((chapter_id, chapter_content))

    return chapters


def _find_matching_environment(text: str, env_name: str, start_pos: int = 0) -> tuple[int, int, str]:
    """
    Find a matching LaTeX environment using a stack-based approach.

    Args:
        text: The text to search in
        env_name: The name of the environment to find
        start_pos: Position to start searching from

    Returns:
        Tuple of (start_pos, end_pos, environment_content)
        where environment_content does not include the \\begin and \\end tags
    """
    begin_pattern = r"\\begin{" + env_name + r"}"
    end_pattern = r"\\end{" + env_name + r"}"

    # Find the start of the environment
    begin_match = re.search(begin_pattern, text[start_pos:], re.DOTALL | re.MULTILINE)
    if not begin_match:
        return (-1, -1, "")

    begin_pos = start_pos + begin_match.start()
    end_pos = -1
    content_start = begin_pos + len(begin_match.group(0))

    # Use a stack to track nested environments
    stack = 1
    pos = content_start

    while stack > 0 and pos < len(text):
        # Look for the next begin or end tag
        begin_next = re.search(begin_pattern, text[pos:], re.DOTALL | re.MULTILINE)
        end_next = re.search(end_pattern, text[pos:], re.DOTALL | re.MULTILINE)

        # If we found a begin tag and it comes before any end tag (or no end tag was found)
        if begin_next and (not end_next or begin_next.start() < end_next.start()):
            pos += begin_next.start() + len(begin_next.group(0))
            stack += 1
        # If we found an end tag
        elif end_next:
            pos += end_next.start()
            stack -= 1
            # If this is the matching end tag for our original begin tag
            if stack == 0:
                end_pos = pos
                break
            pos += len(end_next.group(0))
        # If we didn't find either tag, we have a problem
        else:
            return (-1, -1, "")

    # If we couldn't find a matching end tag
    if stack > 0 or end_pos == -1:
        return (-1, -1, "")

    return (begin_pos, end_pos + len(end_pattern) - 1, text[content_start:end_pos])


def _extract_problems(chapter_content: str) -> list[tuple[str, str]]:
    """
    Extract problems from the chapter content based on the problem list.

    Args:
        chapter_content: The content of a chapter
        problem_list: The list of problems to extract

    Returns:
        List of tuples (problem_id, problem_content)
    """
    problems = []

    # Find the main enumerate environment
    begin_pos, end_pos, enumerate_content = _find_matching_environment(chapter_content, "enumerate")
    if begin_pos == -1:
        logger.debug("No main enumerate environment found in chapter content")
        return problems

    logger.debug(f"Found main enumerate environment with length {len(enumerate_content)}")

    # Find all \item entries in the main enumerate environment
    item_pattern = r"\\item\[([^\n]*)\.\](.*?)(?=\\item\[|\Z)"
    items = list(re.finditer(item_pattern, enumerate_content, re.DOTALL | re.MULTILINE))

    for item in items:
        logger.debug(f"Found item with ID {item.group(1)}")
        problem_id = extract_problem_id(item.group(1))
        logger.debug(f"Extracted problem ID {problem_id}")

        problem_content = item.group(2).strip()
        problems.append((problem_id, problem_content))

    return problems


def _process_problem(problem_content: str, problem_id: ProblemID) -> Answer:
    """
    Process a problem's content to extract main answer and subproblems based on the problem list.

    Args:
        problem_content: The content of a problem
        problem_id: The ID of the problem

    Returns:
        AnswerContent object with main answer and subproblem answers
    """
    answer_content = Answer(problem_content)

    # Try to find an enumerate environment (which would contain subproblems)
    begin_pos, end_pos, subproblems_content = _find_matching_environment(problem_content, "enumerate")

    # If no enumerate environment is found, or this problem has no subproblems in the problem_list
    if begin_pos == -1 or not problem_id.has_subproblems():
        return answer_content

    # The main answer is everything before the subproblems
    answer_content.answer = problem_content[:begin_pos].strip()

    # Extract individual subproblems
    logger.debug(f"Extracting subproblems from content with length {len(subproblems_content)}")
    subproblems = _extract_subproblems(subproblems_content)
    logger.debug(f"Extracted {len(subproblems)} subproblems")

    # Add subproblems to the answer content, but only those in the problem_list
    for i, subproblem_content in enumerate(subproblems, start=1):
        subproblem_id = str(i)
        answer_content.add_sub_answer(subproblem_id, subproblem_content)

    return answer_content


def _extract_subproblems(subproblems_content: str) -> list[str]:
    """
    Extract individual subproblems from the subproblems content.

    Args:
        subproblems_content: The content of the subproblems enumerate environment

    Returns:
        List of subproblem contents
    """
    subproblems = []

    # Find all \item entries in the content
    pos = 0
    while True:
        # Find the next \item
        item_match = re.search(r"\\item\s+", subproblems_content[pos:], re.DOTALL | re.MULTILINE)
        if not item_match:
            break

        item_start = pos + item_match.end()

        # Find the start of the next \item or the end of content
        next_match = re.search(r"\\item\s+", subproblems_content[item_start:], re.DOTALL | re.MULTILINE)
        if next_match:
            item_end = item_start + next_match.start()
            next_pos = item_start + next_match.start()
        else:
            item_end = len(subproblems_content)
            next_pos = item_end

        # Extract the content between this \item and the next (or end)
        subproblem_content = subproblems_content[item_start:item_end].strip()

        if subproblem_content:  # Only add non-empty subproblems
            subproblems.append(subproblem_content)

        pos = next_pos

    return subproblems
