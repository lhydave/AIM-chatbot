"""
The basics module contains the basic classes and functions for the auto-marker.

Classes:
- ProblemID: Represents a problem ID with a chapter ID, and optional subproblem IDs (if any).
- Answer: Represents an answer to a problem with possible sub-answers to sub-problems.
- AnswerGroup: Well-structured answers for a submission. Also used to organize reference answers and problem descriptions.
- StudentSubmission: Represents a student submission with answers and metadata.

It also contains functions to parse problem lists and submission titles, and filter answers based on a list of ProblemID objects.
"""  # noqa: E501

from dataclasses import dataclass, field
from typing import Optional, Any, Literal
from collections.abc import Iterable
import re
import copy
from auto_marker.logging import logger


@dataclass
class ProblemID:
    """Represents a problem ID with a chapter ID, and optional subproblem IDs (if any)."""

    chapter_id: str
    problem_id: str
    subproblem_id: list[str] = field(default_factory=list)

    @classmethod
    def from_str(cls, problem_id_str: str) -> "ProblemID":
        """
        Create a ProblemID object from a string. It should be in the format
        - \"chap1.prob1\" for a problem of chapter 1, problem 1
        - \"chap1.prob1(1)(2)\" for a subproblem of chapter 1, problem 1, with subproblems 1 and 2
        """
        # Match pattern: chapter.problem(subprob1)(subprob2)...
        pattern = r"chap([^.]+)\.prob([^()]+)(?:\(([^()]+)\))*"
        match = re.match(pattern, problem_id_str)

        if not match:
            raise ValueError(f"Invalid problem ID format: {problem_id_str}")

        chapter_id = match.group(1)
        problem_id = match.group(2)

        # Find all subproblem IDs using a separate pattern
        subproblems = re.findall(r"\(([^()]+)\)", problem_id_str)

        return cls(chapter_id=chapter_id, problem_id=problem_id, subproblem_id=subproblems)

    def has_subproblems(self) -> bool:
        """Check if the problem has subproblems."""
        return len(self.subproblem_id) > 0

    @staticmethod
    def find_problem_id(problem_list: Iterable["ProblemID"], chapter_id: str, problem_id: str) -> Optional["ProblemID"]:
        """
        Find a ProblemID object in a list based on chapter and problem IDs.

        Args:
            problem_list: An Iterable of ProblemID objects
            chapter_id: The chapter ID to search for
            problem_id: The problem ID to search for

        Returns:
            The ProblemID object if found, otherwise None
        """
        for problem in problem_list:
            if problem.chapter_id == chapter_id and problem.problem_id == problem_id:
                return problem
        return None

    def __str__(self) -> str:
        """Convert the ProblemID object to a string."""
        if self.subproblem_id:
            return f"chap{self.chapter_id}.prob{self.problem_id}({')('.join(self.subproblem_id)})"
        return f"chap{self.chapter_id}.prob{self.problem_id}"

    def __lt__(self, other: "ProblemID") -> bool:
        """
        Compare two ProblemID objects.
        First compares chapter_id, then problem_id.
        If the IDs are numeric, compares them as numbers, otherwise compares them as strings.
        """
        # Compare chapter_id
        try:
            self_chapter = int(self.chapter_id)
            other_chapter = int(other.chapter_id)
            if self_chapter != other_chapter:
                return self_chapter < other_chapter
        except ValueError:
            if self.chapter_id != other.chapter_id:
                return self.chapter_id < other.chapter_id

        # If chapter_id is the same, compare problem_id
        try:
            self_problem = int(self.problem_id)
            other_problem = int(other.problem_id)
            return self_problem < other_problem
        except ValueError:
            return self.problem_id < other.problem_id

    def __eq__(self, other: object) -> bool:
        """
        Check if two ProblemID objects are equal.
        Two ProblemIDs are equal if their chapter_id, problem_id, and subproblem_id are all equal.
        """
        if not isinstance(other, ProblemID):
            return False
        return (
            self.chapter_id == other.chapter_id
            and self.problem_id == other.problem_id
            and self.subproblem_id == other.subproblem_id
        )

    def __hash__(self) -> int:
        """Hash function using the string representation of the ProblemID."""
        return hash(str(self))


@dataclass
class Answer:
    """Represents an answer to a problem with possible sub-answers to sub-problems."""

    answer: str
    sub_answers: list[tuple[str, str]] = field(default_factory=list)

    def add_sub_answer(self, subproblem_id: str, sub_answer: str) -> None:
        """Add a sub-answer to the answer."""
        self.sub_answers.append((subproblem_id, sub_answer))

    def get_sub_answer(self, subproblem_id: str, answer_name: str = "answer") -> str:
        """Get a sub-answer by subproblem ID."""
        for sub_id, sub_answer in self.sub_answers:
            if sub_id == subproblem_id:
                return sub_answer
        return f"No {answer_name} provided"

    def to_json(self) -> dict:
        """Convert the Answer object to a JSON-serializable dictionary."""
        ret: dict[str, Any] = {"answer": self.answer}
        if self.sub_answers:
            ret["sub_answers"] = [
                {"sub_id": sub_id, "sub_answer": sub_answer} for sub_id, sub_answer in self.sub_answers
            ]
        return ret

    def to_markdown_str(self, answer_name: str = "answer") -> str:
        """
        Convert the Answer object to a Markdown-formatted string.
        Includes the main answer and all sub-answers.
        """
        result = f"{self.answer}\n\n"
        for sub_id, sub_answer in self.sub_answers:
            result += f"#### {answer_name} to ({sub_id})\n\n{sub_answer}\n\n"
        return result

    @classmethod
    def from_json(cls, json_dict: dict) -> "Answer":
        """Create an Answer object from a JSON dictionary."""
        answer = cls(answer=json_dict.get("answer", ""))
        sub_answers = json_dict.get("sub_answers", [])
        for sub_answer in sub_answers:
            answer.add_sub_answer(sub_answer.get("sub_id", "Unknown sub_id"), sub_answer.get("sub_answer", ""))
        return answer


@dataclass
class AnswerGroup:
    """
    Well-structured answers for a submission. Maps ProblemID to Answer objects.
    Also used to organize reference answers and problem descriptions.
    """

    answers: dict[ProblemID, Answer] = field(default_factory=dict)

    def __getitem__(self, key: ProblemID) -> Answer:
        """Get an answer by problem ID."""
        return self.answers[key]

    def __setitem__(self, key: ProblemID, value: Answer) -> None:
        """Set an answer for a problem ID."""
        self.answers[key] = value

    def __contains__(self, key: ProblemID) -> bool:
        """Check if an answer exists for a problem ID."""
        return key in self.answers

    def __len__(self) -> int:
        """Get the number of answers."""
        return len(self.answers)

    def items(self):
        """Return a view of (problem_id, answer) pairs."""
        return self.answers.items()

    def keys(self):
        """Return a view of problem IDs."""
        return self.answers.keys()

    def values(self):
        """Return a view of answers."""
        return self.answers.values()

    def get(self, key: ProblemID, default: Optional[Answer] = None) -> Optional[Answer]:
        """Get an answer by problem ID with a default value if not found."""
        return self.answers.get(key, default)

    def add_answer(self, problem_id: ProblemID, answer: str) -> None:
        """Add a new answer for a problem ID. If the answer already exists, it will be replaced."""
        self.answers[problem_id] = Answer(answer=answer)

    def add_sub_answer(self, problem_id: ProblemID, subproblem_id: str, sub_answer: str) -> None:
        """Add a sub-answer to the answer for a problem ID."""
        if problem_id not in self.answers:
            self.answers[problem_id] = Answer(answer="")
            logger.warning(f"Problem ID {problem_id} not found, creating a new answer with an empty main answer.")
        self.answers[problem_id].add_sub_answer(subproblem_id, sub_answer)

    def to_json(self) -> dict:
        """
        Convert the AnswerGroup to a JSON-serializable dictionary.
        The answers are sorted by ProblemID.
        """
        sorted_answers = []
        # Sort the problem IDs
        sorted_problem_ids = sorted(self.answers.keys())

        for problem_id in sorted_problem_ids:
            answer = self.answers[problem_id]
            sorted_answers.append({"problem_id": str(problem_id), "answer": answer.to_json()})

        return {"answers": sorted_answers}

    def to_markdown_str(self, answer_name: str = "answer") -> str:
        """
        Convert the AnswerGroup to a Markdown-formatted string.
        Includes the main answers and all sub-answers.

        Args:
            answer_name: The name of the answer to use in the output

        Returns:
            A Markdown-formatted string
        """
        result = ""
        # Sort the problem IDs
        sorted_problem_ids = sorted(self.answers.keys())
        if not sorted_problem_ids:
            logger.warning("Empty answer group")
            return result
        current_chapter = sorted_problem_ids[0].chapter_id
        result += f"## {answer_name} for Chapter {current_chapter}\n\n"

        for problem_id in sorted_problem_ids:
            if problem_id.chapter_id != current_chapter:
                current_chapter = problem_id.chapter_id
                result += f"\n\n## {answer_name} for Chapter {current_chapter}\n\n"

            answer = self.answers[problem_id]
            result += f"## {answer_name} to {problem_id}\n\n"
            result += answer.to_markdown_str(answer_name=answer_name)

        return result

    @classmethod
    def from_json(cls, json_dict: dict) -> "AnswerGroup":
        """
        Create an AnswerGroup object from a JSON dictionary.
        Reconstructs the ProblemID objects from their string representations.
        """
        answer_group = cls()

        for item in json_dict.get("answers", []):
            problem_id_str = item.get("problem_id", "")
            try:
                problem_id = ProblemID.from_str(problem_id_str)
                answer = Answer.from_json(item.get("answer", {}))
                answer_group[problem_id] = answer
            except ValueError as e:
                # Skip invalid problem IDs
                logger.warning(f"Skipping invalid problem ID: {problem_id_str}. Error: {e}")

        return answer_group


def parse_problem_list(problem_list_str: str) -> list[ProblemID]:
    """
    Parse a multi-line string where each line is in the format "chapter X: problem1,problem2,..."

    Args:
        problem_list_str: A multi-line string containing chapter and problem information

    Returns:
        A list of ProblemID objects

    Example:
        Input:
        '''
        chapter 1: 1,2,3,4(1)(2)
        chapter 2: 1,2,extra
        '''

        Output:
        [
            ProblemID(chapter_id="1", problem_id="1", subproblem_id=[]),
            ProblemID(chapter_id="1", problem_id="2", subproblem_id=[]),
            ProblemID(chapter_id="1", problem_id="3", subproblem_id=[]),
            ProblemID(chapter_id="1", problem_id="4", subproblem_id=["1", "2"]),
            ProblemID(chapter_id="2", problem_id="1", subproblem_id=[]),
            ProblemID(chapter_id="2", problem_id="2", subproblem_id=[]),
            ProblemID(chapter_id="2", problem_id="extra", subproblem_id=[])
        ]
    """
    problem_ids = []

    # Split the input string into lines and process each line
    for line in problem_list_str.strip().split("\n"):
        line = line.strip()
        if not line:
            continue

        # Extract chapter number and problem list
        match = re.match(r"chapter\s+(\w+):\s*(.*)", line, re.IGNORECASE)
        if not match:
            continue

        chapter_id = match.group(1)
        problems = match.group(2).split(",")

        for problem in problems:
            problem = problem.strip()
            if not problem:
                continue

            # Extract problem number and any subproblems
            base_pattern = r"([^\s()]+)(?:\(([^()]+)\))*"
            base_match = re.match(base_pattern, problem)

            if base_match:
                problem_id = base_match.group(1)
                # Find all subproblem IDs
                subproblems = re.findall(r"\(([^()]+)\)", problem)

                # Create and add the ProblemID object
                problem_ids.append(
                    ProblemID(
                        chapter_id=chapter_id,
                        problem_id=problem_id,
                        subproblem_id=subproblems,
                    )
                )

    return problem_ids


@dataclass
class StudentSubmission:
    """Represents a student's submission data.

    Attributes:
        homework_id: Identifier of the homework assignment (e.g., '1', '2').
        student_id: The student's ID number (e.g., '2300017000').
        student_name: The student's name.
        raw_source_code: Original source code content from the student's submission files.
        processed_source_code: Processed version of the source code which is organized using a TextProcessor, if available.
        marks: Marks assigned to the submission, if available.
    """  # noqa: E501

    homework_id: str
    student_id: str
    student_name: str
    raw_source_code: str
    code_language: Literal["markdown", "tex"]
    processed_source_code: Optional[AnswerGroup] = None
    marks: Optional[AnswerGroup] = None

    def to_json(self) -> dict[str, Any]:
        """Convert the StudentSubmission to a JSON-serializable dictionary.

        Returns:
            Dictionary containing the submission data fields.
        """
        result: dict[str, Any] = {
            "homework_id": self.homework_id,
            "student_id": self.student_id,
            "student_name": self.student_name,
            "raw_source_code": self.raw_source_code,
            "code_language": self.code_language,
        }

        # Include processed_source_code if available
        if self.processed_source_code is not None:
            result["processed_source_code"] = self.processed_source_code.to_json()

        # Include marks if available
        if self.marks is not None:
            result["marks"] = self.marks.to_json()

        return result

    @classmethod
    def from_json(cls, json_dict: dict[str, Any]) -> "StudentSubmission":
        """Create a StudentSubmission instance from a JSON dictionary."""
        # Process source code if available
        processed_source_code = None
        if "processed_source_code" in json_dict:
            processed_source_code = AnswerGroup.from_json(json_dict["processed_source_code"])

        # Marks if available
        marks = None
        if "marks" in json_dict:
            marks = AnswerGroup.from_json(json_dict["processed_source_code"])

        return cls(
            homework_id=json_dict["homework_id"],
            student_id=json_dict["student_id"],
            student_name=json_dict["student_name"],
            raw_source_code=json_dict["raw_source_code"],
            code_language=json_dict["code_language"],
            processed_source_code=processed_source_code,
            marks=marks,
        )


def parse_submission_title(title: str) -> tuple[str, str, str]:
    """
    Parse the submission title to extract homework ID, student ID, and name.
    Example title format: "HW1-2300017000-李二"

    Returns:
        Tuple containing (homework_id, student_id, student_name)
    """
    pattern = r"(?:HW|hw)\[?(\d+)\]?[-_](\d+)[-_](.+)"
    match = re.search(pattern, title)
    if not match:
        raise ValueError(f"Invalid submission title format: {title}")

    homework_id, student_id, student_name = match.groups()
    return homework_id, student_id, student_name


def filter_answers(
    problem_id_list: list[ProblemID],
    answer_group: AnswerGroup,
    default_answer: str = "No answer provided",
) -> AnswerGroup:
    """
    Filter an AnswerGroup based on a list of ProblemID objects.
    - If a (sub)problem is not in the list, it will be removed from the AnswerGroup.
    - If a (sub)problem is in the list but not in the AnswerGroup, it will be added with an default answer.

    Args:
        problem_id_list: A list of ProblemID objects to filter the AnswerGroup
        answer_group: The AnswerGroup to filter
        default_answer: The default answer to use for missing problems

    Returns:
        A new AnswerGroup with the filtered answers
    """
    filtered_answer_group = AnswerGroup()

    for problem_id in problem_id_list:
        chapter_id = problem_id.chapter_id

        logger.debug(f"Checking problem {problem_id}")
        problem_id_str = problem_id.problem_id
        found_problem_id = ProblemID.find_problem_id(answer_group.keys(), chapter_id, problem_id_str)
        if not found_problem_id:
            logger.warning(f"Problem ID {problem_id} not found, use the default answer instead.")
            # Add the problem with a default answer
            filtered_answer_group[problem_id] = Answer(answer=default_answer)
            if not problem_id.has_subproblems():
                continue
            for subproblem_id in problem_id.subproblem_id:
                filtered_answer_group.add_sub_answer(problem_id, subproblem_id, default_answer)
        else:
            logger.debug(f"Found problem {found_problem_id} in chapter {chapter_id}")
            # Add the existing answer
            filtered_answer_group[problem_id] = copy.deepcopy(answer_group[found_problem_id])

            # clear the subproblems for further check
            filtered_answer_group[problem_id].sub_answers.clear()

            if not problem_id.has_subproblems():
                continue

            # check the subproblems
            for subproblem_id in problem_id.subproblem_id:
                logger.debug(f"Checking subproblem {subproblem_id} for problem {problem_id}")
                if subproblem_id not in found_problem_id.subproblem_id:
                    logger.warning(
                        f"Subproblem ID {subproblem_id} not found for {problem_id}, use the default answer instead."  # noqa: E501
                    )

                    filtered_answer_group.add_sub_answer(problem_id, subproblem_id, default_answer)
                else:
                    logger.debug(f"Found subproblem {subproblem_id} for problem {problem_id} in chapter {chapter_id}")
                    filtered_answer_group.add_sub_answer(
                        problem_id,
                        subproblem_id,
                        answer_group[found_problem_id].get_sub_answer(subproblem_id),
                    )

    return filtered_answer_group
