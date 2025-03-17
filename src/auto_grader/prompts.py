class MarkingPromptTemplate:
    """
    A template class for generating prompts for AI auto-marking.
    This class allows customization of various components of the marking prompt.
    """
    
    def __init__(self, 
                 prologue: str,
                 problem_description: str, 
                 reference_answer: str,
                 student_answer: str,
                 sample_marking: str,
                 epilogue: str):
        """
        Initialize the MarkingPromptTemplate with optional components.
        
        Args:
        - prologue: The introductory text to the prompt.
        - problem_description: The description of the problem to be solved.
        - reference_answer: The correct answer to the problem.
        - student_answer: The student's answer to the problem.
        - sample_marking: An example of how the problem should be marked.
        - epilogue: The closing text of the prompt.
        """
        self.prologue = prologue
        self.problem_description = problem_description
        self.reference_answer = reference_answer
        self.student_answer = student_answer
        self.sample_marking = sample_marking
        self.epilogue = epilogue
            
    def generate_prompt(self):
        """Generate the complete prompt with all provided components."""
        prompt_parts = []
        
        # Add prologue
        prompt_parts.append(self.prologue)

        # Add problem description
        prompt_parts.append("问题描述：\n" + self.problem_description)

        # Add reference answer
        prompt_parts.append("参考答案：\n" + self.reference_answer)

        # Add student answer
        prompt_parts.append("学生答案：\n" + self.student_answer)

        # Add sample marking
        prompt_parts.append("批改示例：\n" + self.sample_marking)

        # Add epilogue
        prompt_parts.append(self.epilogue)
        
        # Join all parts with double newlines
        return "\n\n".join(prompt_parts)
    
    def __str__(self):
        """Return the string representation of the prompt template."""
        return self.generate_prompt()