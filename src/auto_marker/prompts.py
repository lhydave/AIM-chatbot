class MarkPromptTemplate:
    """A template for creating prompts with formatting placeholders.

    Supported formatting placeholders are:
        - {problem_description}: The description of the problem.
        - {reference_answer}: The reference answer to the problem.
        - {student_answer}: The student's answer to the problem.
        - {subproblem_nums}: The number of subproblems in the problem.
        - {subproblem_id}: The subproblem ID.
    """

    def __init__(
        self,
        template: str,
        problem_description: str = "",
        reference_answer: str = "",
        student_answer: str = "",
        subproblem_nums: int = 0,
        subproblem_id: str = "",
    ):
        """Initialize the prompt template.

        Args:
            prompt (str): The text of the prompt with formatting placeholders.
            problem_description (str): The description of the problem.
            reference_answer (str): The reference answer to the problem.
            student_answer (str): The student's answer to the problem.
            subproblem_nums (int): The number of subproblems in the problem.
            subproblem_id (str): The subproblem ID.
        """
        self.prompt = template
        self.problem_description = problem_description
        self.reference_answer = reference_answer
        self.student_answer = student_answer
        self.subproblem_nums = subproblem_nums
        self.subproblem_id = subproblem_id

    def to_prompt(self) -> str:
        """Format and return the prompt with the provided values.

        Returns:
            str: The formatted prompt.
        """
        return self.prompt.format(
            problem_description=self.problem_description,
            reference_answer=self.reference_answer,
            student_answer=self.student_answer,
            subproblem_nums=self.subproblem_nums,
            subproblem_id=self.subproblem_id,
        )
