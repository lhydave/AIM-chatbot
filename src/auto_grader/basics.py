"""
The basics module contains the basic classes and functions for the auto-grader.

Classes:
- ProblemID: Represents a problem ID with a chapter ID, and optional subproblem IDs (if any).
- Answer: Represents an answer to a problem with possible sub-answers to sub-problems.
- AnswerGroup: Well-structured answers for a submission. Also used to organize reference answers and problem descriptions.
- StudentSubmission: Represents a student submission with answers and metadata.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
import re


@dataclass
class ProblemID:
    """Represents a problem ID with a chapter ID, and optional subproblem IDs (if any)."""

    chapter_id: str
    problem_id: str
    subproblem_id: List[str] = field(default_factory=list)

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

        return cls(
            chapter_id=chapter_id, problem_id=problem_id, subproblem_id=subproblems
        )

    def __str__(self) -> str:
        """Convert the ProblemID object to a string."""
        if self.subproblem_id:
            return (
                f"chap{self.chapter_id}.prob{self.problem_id}({')('.join(self.subproblem_id)})"
            )
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

    def __hash__(self) -> int:
        """Hash function using the string representation of the ProblemID."""
        return hash(str(self))


@dataclass
class Answer:
    """Represents an answer to a problem with possible sub-answers to sub-problems."""

    answer: str
    sub_answers: List[tuple[str, str]] = field(default_factory=list)

    def add_sub_answer(self, subproblem_id: str, sub_answer: str) -> None:
        """Add a sub-answer to the answer."""
        self.sub_answers.append((subproblem_id, sub_answer))

    def get_sub_answer(self, subproblem_id: str, answer_name: str = "answer") -> str:
        """Get a sub-answer by subproblem ID."""
        for sub_id, sub_answer in self.sub_answers:
            if sub_id == subproblem_id:
                return sub_answer
        return f"No {answer_name} provided"

    def get_sub_answer_with_context(
        self, subproblem_id: str, answer_name: str = "answer"
    ) -> str:
        """
        Get the answer for a specific subproblem along with its context.

        The context includes the main answer and all subproblem answers that come before
        the requested subproblem (based on sorted subproblem IDs).

        Args:
            subproblem_id: The ID of the subproblem
            answer_name: The name to use for the answer section (default: "Answer")

        Returns:
            A string with the context and the answer for the subproblem
        """
        context = f"Stated {answer_name}:\n{self.answer}"
        for sub_id, sub_answer in self.sub_answers:
            if sub_id == subproblem_id:
                break
            context += f"\n\nStated {answer_name} to ({sub_id}):\n{sub_answer}"

        context += f"\n\nCurrent {answer_name} to ({subproblem_id}):\n{self.get_sub_answer(subproblem_id, answer_name)}"
        return context

    def to_json(self) -> dict:
        """Convert the Answer object to a JSON-serializable dictionary."""
        return {
            "answer": self.answer,
            "sub_answers": self.sub_answers
        }
    
    @classmethod
    def from_json(cls, json_dict: dict) -> "Answer":
        """Create an Answer object from a JSON dictionary."""
        return cls(
            answer=json_dict.get("answer", ""),
            sub_answers=json_dict.get("sub_answers", [])
        )


@dataclass
class AnswerGroup:
    """
    Well-structured answers for a submission. Maps ProblemID to Answer objects.
    Also used to organize reference answers and problem descriptions.
    """
    
    answers: Dict[ProblemID, Answer] = field(default_factory=dict)
    
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
        """Add a new answer for a problem ID."""
        self.answers[problem_id] = Answer(answer=answer)
    
    def add_sub_answer(self, problem_id: ProblemID, subproblem_id: str, sub_answer: str) -> None:
        """Add a sub-answer to the answer for a problem ID."""
        if problem_id not in self.answers:
            self.answers[problem_id] = Answer(answer="")
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
            sorted_answers.append({
                "problem_id": str(problem_id),
                "answer": answer.to_json()
            })
        
        return {
            "answers": sorted_answers
        }
    
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
                print(f"Warning: Skipping invalid problem ID: {problem_id_str}. Error: {e}")
        
        return answer_group


def parse_problem_list(problem_list_str: str) -> List[ProblemID]:
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
    for line in problem_list_str.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
            
        # Extract chapter number and problem list
        match = re.match(r'chapter\s+(\w+):\s*(.*)', line, re.IGNORECASE)
        if not match:
            continue
            
        chapter_id = match.group(1)
        problems = match.group(2).split(',')
        
        for problem in problems:
            problem = problem.strip()
            if not problem:
                continue
                
            # Extract problem number and any subproblems
            base_pattern = r'([^\s()]+)(?:\(([^()]+)\))*'
            base_match = re.match(base_pattern, problem)
            
            if base_match:
                problem_id = base_match.group(1)
                # Find all subproblem IDs
                subproblems = re.findall(r'\(([^()]+)\)', problem)
                
                # Create and add the ProblemID object
                problem_ids.append(ProblemID(
                    chapter_id=chapter_id,
                    problem_id=problem_id,
                    subproblem_id=subproblems
                ))
    
    return problem_ids
