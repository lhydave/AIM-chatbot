"""
utility functions for the chatbot.
"""

import re
from latex_defs import LATEX_COMMANDS, LATEX_MACROS

def replaceMacros(content: str):
    """
    Replace LaTeX macros and commands in the content
    """

    # Replace simple macros
    for macro, replacement in LATEX_MACROS.items():
        # Add word boundary after the macro to ensure it's not followed by letters
        pattern = re.compile(macro + r'(?![a-zA-Z])')
        content = pattern.sub(replacement, content)

    # Replace commands with arguments
    for cmd, (num_args, template) in LATEX_COMMANDS.items():
        while True:
            idx = content.find(cmd)
            if idx == -1:
                break

            # Find arguments
            args = []
            pos = idx + len(cmd)
            for _ in range(num_args):
                if pos >= len(content):
                    break
                if content[pos] == "{":
                    # Find matching closing brace
                    brace_count = 1
                    end_pos = pos + 1
                    while end_pos < len(content) and brace_count > 0:
                        if content[end_pos] == "{":
                            brace_count += 1
                        elif content[end_pos] == "}":
                            brace_count -= 1
                        end_pos += 1
                    args.append(content[pos + 1 : end_pos - 1])
                    pos = end_pos
                else:
                    break

            if len(args) == num_args:
                # Replace command with template
                repl = template
                for j, arg in enumerate(args, 1):
                    repl = repl.replace(f"#{j}", arg)
                content = content[:idx] + repl + content[pos:]

    return content


def replaceDelimiters(content: str):
    """
    Replace LaTeX delimiters with simpler ones.
    """
    return (
        content.replace("\\(", "$")
        .replace("\\)", "$")
        .replace("\\[", "$$")
        .replace("\\]", "$$")
    )


def processResponse(content: str):
    return replaceMacros(replaceDelimiters(content))
