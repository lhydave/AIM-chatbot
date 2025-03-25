import re
from auto_marker.basics import ProblemID, AnswerGroup, Answer
from auto_marker.text_processor.utils import extract_chapter_id, extract_problem_id
from auto_marker.logging import logger


def _strip_latex_comments(content: str) -> str:
    """
    Remove LaTeX comments from the content.
    LaTeX comments start with % and continue to the end of the line.

    Args:
        content: The content to remove comments from

    Returns:
        The content with comments removed
    """
    # Remove comments that start with % and continue to the end of line
    # But don't remove escaped percent signs (e.g., \%)
    return re.sub(r"(?<!\\)%.*?$", "", content, flags=re.MULTILINE)


def parse_content(content: str, problem_list: list[ProblemID]) -> AnswerGroup:
    """
    Parse the content of a LaTeX file and extract answers based on the problem list.

    Args:
        content: The content of the LaTeX file to parse
        problem_list: The list of problems to extract

    Returns:
        An AnswerGroup object containing the extracted answers
    """
    logger.debug(f"Starting to parse content with {len(problem_list)} problems in problem_list")
    ret = AnswerGroup()

    # Strip LaTeX comments before processing
    content = _strip_latex_comments(content)
    logger.debug("Removed LaTeX comments from content")

    # Extract the document body (between \begin{document} and \end{document})
    document_match = re.search(r"\\begin{document}(.*?)\\end{document}", content, re.DOTALL | re.MULTILINE)
    if not document_match:
        logger.debug("No document environment found in the content")
        return ret

    document_content = document_match.group(1)
    logger.debug(f"Extracted document content with length {len(document_content)}")

    # Extract sections (chapters)
    chapters = _extract_chapters(document_content)
    logger.debug(f"Extracted {len(chapters)} chapters from document")

    # Process each chapter
    for chapter_id, chapter_content in chapters:
        logger.debug(f"Processing chapter {chapter_id} with content length {len(chapter_content)}")

        # Extract problems from the chapter
        problems = _extract_problems(chapter_content, chapter_id)
        logger.debug(f"Extracted {len(problems)} problems from chapter {chapter_id}")

        for problem_id_str, problem_content in problems:
            # Process each problem
            logger.debug(f"Looking for problem ID {problem_id_str} in chapter {chapter_id}")
            problem_id = ProblemID.find_problem_id(problem_list, chapter_id, problem_id_str)
            if not problem_id:
                logger.debug(
                    f"Problem ID {problem_id_str} not found in problem list when processing chapter {chapter_id}"
                )
                continue

            logger.debug(f"Processing problem {problem_id}")
            # Process the problem content to extract main answer and subproblems
            answer_content = _process_problem(problem_content, problem_id)
            ret[problem_id] = answer_content
            logger.debug(f"Added answer for problem {problem_id}")

    logger.debug(f"Completed parsing content, extracted {len(ret)} answers")
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
    if not chapters:
        logger.warning("No chapters found in document content, possibly missing \\section commands")
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
            logger.warning(
                f"\\begin{{{env_name}}} is found, but no matching \\end{{{env_name}}} found for \\begin{{{env_name}}}."
            )
            return (-1, -1, "")

    # If we couldn't find a matching end tag
    if stack > 0 or end_pos == -1:
        logger.warning(
            f"\\begin{{{env_name}}} is found, but no matching \\end{{{env_name}}} found for \\begin{{{env_name}}}"
        )
        return (-1, -1, "")

    return (begin_pos, end_pos + len(end_pattern) - 1, text[content_start:end_pos])


def _find_last_matching_environment(text: str, env_name: str, start_pos: int = 0) -> tuple[int, int, str]:
    """
    Find the last matching LaTeX environment by repeatedly using _find_matching_environment.

    Args:
        text: The text to search in
        env_name: The name of the environment to find
        start_pos: Position to start searching from

    Returns:
        Tuple of (start_pos, end_pos, environment_content)
        where environment_content does not include the \\begin and \\end tags
    """
    last_match = (-1, -1, "")
    current_pos = start_pos

    while True:
        # Find the next occurrence of the environment
        match = _find_matching_environment(text, env_name, current_pos)

        # If no more environments found, break
        if match[0] == -1:
            break

        # Update the last match
        last_match = match

        # Move past this match to look for the next one
        current_pos = match[1]

    return last_match


def _check_enumerate_start(enumerate_content: str) -> tuple[bool, str]:
    """
    Check if there is content between \\begin{enumerate}[xxx] and the first \\item.

    Args:
        enumerate_content: The content of the enumerate environment

    Returns:
        Tuple of (has_content, content_text):
        - has_content: True if content exists between begin and first item, False otherwise
        - content_text: The content found between begin and first item, or empty string if none
    """
    # Look for any content between begin{enumerate}[...] and first \item
    match = re.match(
        r"^\s*\\begin{enumerate}(?:\[[^\]]*\])?\s*(.*?)\\item", enumerate_content, re.DOTALL | re.MULTILINE
    )
    if match and match.group(1).strip():
        return True, match.group(1).strip()
    return False, ""


def _extract_problems(chapter_content: str, chapter_id: str) -> list[tuple[str, str]]:
    """
    Extract problems from the chapter content based on the problem list.

    Args:
        chapter_content: The content of a chapter
        chapter_id: The ID of the chapter

    Returns:
        List of tuples (problem_id, problem_content)
    """
    problems = []

    # Find the main enumerate environment
    begin_pos, end_pos, enumerate_content = _find_matching_environment(chapter_content, "enumerate")
    if begin_pos == -1:
        logger.warning(
            f"No main enumerate environment found in chapter {chapter_id}, possibly missing \\begin{{enumerate}} or \\end{{enumerate}}"  # noqa: E501
        )
        return problems

    logger.debug(f"Found main enumerate environment with length {len(enumerate_content)}")

    # Check that there's no content between \begin{enumerate} and first \item
    has_content, unexpected_content = _check_enumerate_start(chapter_content[begin_pos:end_pos])
    if has_content:
        logger.warning(
            f"Invalid to have content between \\begin{{enumerate}} and first \\item in chapter {chapter_id}: '{unexpected_content}'"  # noqa: E501
        )

    # Find all \item entries in the main enumerate environment
    item_pattern = r"\\item\s*\[([^\n]*)\.\](.*?)(?=\\item\s*\[([^\n]*)\.\]|\Z)"
    items = re.finditer(item_pattern, enumerate_content, re.DOTALL | re.MULTILINE)

    for item in items:
        logger.debug(f"Found item with ID {item.group(1)}")
        problem_id = extract_problem_id(item.group(1))
        logger.debug(f"Extracted problem ID {problem_id}")

        problem_content = item.group(2).strip()
        logger.debug(f"Extracted problem content: {problem_content[:1000]}...")
        problems.append((problem_id, problem_content))

    if not problems:
        logger.warning(f"No problems found in chapter {chapter_id}, possibly missing \\item[xx.] commands")

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

    # If this problem has no subproblems, return the whole content as the main answer
    if not problem_id.has_subproblems():
        return answer_content

    # Try to find an enumerate environment (which would contain subproblems)
    begin_pos, end_pos, subproblems_content = _find_last_matching_environment(problem_content, "enumerate")

    logger.debug(f"Found enumerate environment: {subproblems_content}")

    # If no enumerate environment is found
    if begin_pos == -1:
        logger.warning(
            f"No subproblem enumerate environment found in problem {problem_id}, which should have subproblems"
        )
        return answer_content

    # Check if there's content between \begin{enumerate} and first \item
    has_content, content_text = _check_enumerate_start(problem_content[begin_pos:end_pos])
    if has_content:
        logger.debug(
            f"Found content between \\begin{{enumerate}} and first \\item in problem {problem_id}, adding to answer"
        )

    # Get content after enumerate environment
    after_enumerate = problem_content[end_pos:].strip()

    # The main answer is everything before the subproblems
    main_answer = problem_content[:begin_pos].strip()

    # If there was content between \begin{enumerate} and first \item, append it to the main answer
    if has_content:
        if main_answer:
            main_answer += "\n\n" + content_text
        else:
            main_answer = content_text

    answer_content.answer = main_answer

    # Extract individual subproblems
    logger.debug(f"Extracting subproblems from content with length {len(subproblems_content)}")
    subproblems = _extract_subproblems(subproblems_content)
    logger.debug(f"Extracted {len(subproblems)} subproblems")

    if len(subproblems) != len(problem_id.subproblem_id):
        logger.warning(
            f"Number of subproblems extracted ({len(subproblems)}) does not match expected number ({len(problem_id.subproblem_id)}) when processing problem {problem_id}"  # noqa: E501
        )

    # Add subproblems to the answer content, but only those in the problem_list
    for i, subproblem_content in enumerate(subproblems, start=1):
        subproblem_id = str(i)

        # If this is the last subproblem and there's content after the enumerate environment,
        # append it to the last subproblem
        if i == len(subproblems) and after_enumerate:
            logger.debug(f"Adding content after enumerate environment to the last subproblem in problem {problem_id}")
            subproblem_content = subproblem_content + "\n\n" + after_enumerate

        answer_content.add_sub_answer(subproblem_id, subproblem_content)

    return answer_content


def _extract_subproblems(subproblems_content: str) -> list[str]:
    """
    Extract individual subproblems from the subproblems content.
    Only gets top-level items in the enumerate environment, ignoring nested items.

    Args:
        subproblems_content: The content of the subproblems enumerate environment

    Returns:
        List of subproblem contents
    """
    subproblems = []
    logger.debug(f"extracting subproblems from {subproblems_content[:500]}...")

    # Keep track of nesting level
    nesting_level = 0
    top_level_items = []

    # First, find all the \item positions
    item_matches = list(re.finditer(r"\\item(?![a-zA-Z])", subproblems_content, re.MULTILINE))
    if not item_matches:
        logger.warning("No items found in the subproblems content")
        return subproblems

    # Process each position to determine if it's a top-level item
    for i, match in enumerate(item_matches):
        item_pos = match.start()

        # For the first item, check content before it
        if i == 0:
            text_before = subproblems_content[:item_pos]
            logger.debug(f"find an item with content {text_before}...")
            begin_envs = len(re.findall(r"\\begin{", text_before))
            end_envs = len(re.findall(r"\\end{", text_before))
            logger.debug(f"begin_envs: {begin_envs}, end_envs: {end_envs}")
            nesting_level = begin_envs - end_envs
        else:
            # For subsequent items, check content since the previous item
            prev_item_end = item_matches[i - 1].end()
            text_between = subproblems_content[prev_item_end:item_pos]
            begin_envs = len(re.findall(r"\\begin{", text_between))
            end_envs = len(re.findall(r"\\end{", text_between))
            nesting_level += begin_envs - end_envs

        # If we're at the top level (nesting_level == 0), this is a top-level item
        if nesting_level == 0:
            top_level_items.append(match)

    # Now extract the content between top-level items
    for i, item in enumerate(top_level_items):
        item_end = item.end()

        # If this is the last top-level item, content extends to the end
        if i == len(top_level_items) - 1:
            subproblem_content = subproblems_content[item_end:].strip()
        else:
            # Otherwise, content extends to the next top-level item
            next_item_pos = top_level_items[i + 1].start()
            subproblem_content = subproblems_content[item_end:next_item_pos].strip()

        logger.debug(f"find an item with content {subproblem_content[:30]}...")
        subproblems.append(subproblem_content)

    logger.debug(f"Extracted {len(subproblems)} top-level subproblems")
    return subproblems
