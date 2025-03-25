import re
from auto_marker.basics import ProblemID, AnswerGroup, Answer
from auto_marker.text_processor.utils import extract_chapter_id, extract_problem_id


def parse_content(content: str) -> AnswerGroup:
    """
    Parse the content of a Markdown file and extract answers based on the problem list.

    Args:
        content: The content of the Markdown file to parse

    Returns:
        An AnswerGroup object containing the extracted answers
    """
    ret = AnswerGroup()

    # Split the content by chapter headers (## chapter_name)
    chapter_pattern = r"^\s*## ([^\n]*)\n([\s\S]*?)(?=^\s*## |\Z)"
    chapter_matches = re.finditer(chapter_pattern, content, re.MULTILINE)

    for chapter_match in chapter_matches:
        chapter_id = chapter_match.group(1).strip()
        chapter_id = extract_chapter_id(chapter_id)

        chapter_content = chapter_match.group(2).strip()

        # Split the chapter content by problem headers (### X. or ### extra.)
        problem_pattern = r"^\s*###\s+([^\n]*).*?\n([\s\S]*?)(?=^\s*###\s+([^\n]*)|\Z)"
        problem_matches = re.finditer(problem_pattern, chapter_content, re.MULTILINE)

        for problem_match in problem_matches:
            problem_id = extract_problem_id(problem_match.group(1))
            problem_content = problem_match.group(2).strip()

            # Extract subproblems (#### (X)  )
            subproblem_pattern = r"^\s*####\s+\(([^\n]*)\)[^\n]*\n([\s\S]*?)(?=^\s*####\s+\(|\Z)"
            subproblem_matches = re.finditer(
                subproblem_pattern, problem_content, re.MULTILINE
            )

            # Track the start position of the first subproblem
            first_subproblem_start = len(problem_content)
            subproblems_found = False

            problem_str = f"chap{chapter_id}.prob{problem_id}"

            answer = Answer(problem_content)

            # Process all subproblems
            for subproblem_match in subproblem_matches:
                subproblems_found = True
                subproblem_id = subproblem_match.group(1).strip()
                subproblem_content = subproblem_match.group(2).strip()

                answer.add_sub_answer(subproblem_id, subproblem_content)
                problem_str += f"({subproblem_id})"

                # Keep track of the earliest subproblem position
                subproblem_start = problem_content.find(subproblem_match.group(0))
                if subproblem_start < first_subproblem_start:
                    first_subproblem_start = subproblem_start

            # The main answer is everything before the first subproblem
            if subproblems_found:
                answer.answer = problem_content[:first_subproblem_start].strip()

            ret[ProblemID.from_str(problem_str)] = answer

    return ret
