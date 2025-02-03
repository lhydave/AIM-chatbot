"""
utility functions for the chatbot.
"""

import re

# Dictionary of LaTeX macros with their replacements
LATEX_MACROS = {
    r"\\LHS": r"\\mathrm{LHS}",
    r"\\RHS": r"\\mathrm{RHS}",
    r"\\Z": r"\\mathbb{Z}",
    r"\\N": r"\\mathbb{N}",
    r"\\R": r"\\mathbb{R}",
    r"\\Q": r"\\mathbb{Q}",
    r"\\C": r"\\mathbb{C}",
    r"\\E": r"\\mathbb{E}",
    r"\\O": r"\\mathcal{O}",
    r"\\id": r"\\mathrm{id}",
    r"\\Span": r"\\operatorname{Span}",
    r"\\im": r"\\operatorname{Im}",
    r"\\rank": r"\\operatorname{rank}",
    r"\\card": r"\\operatorname{card}",
    r"\\grad": r"\\operatorname{grad}",
    r"\\argmax": r"\\operatorname{argmax}",
    r"\\epi": r"\\operatorname{epi}",
    r"\\maximize": r"\\operatorname{maximize}",
    r"\\minimize": r"\\operatorname{minimize}",
    r"\\d": r"\\mathrm{d}",
    r"\\Pow": r"\\mathcal{P}",
    r"\\cov": r"\\mathsf{Cov}",
    r"\\var": r"\\mathsf{Var}",
    r"\\Nor": r"\\mathcal{N}",
    r"\\U": r"\\mathcal{U}",
    r"\\t": r"\\mathsf{T}",
    r"\\T": r"\\top",
    r"\\F": r"\\bot",
    r"\\e": r"\\mathrm{e}",
    r"\\const": r"\\mathrm{const}",
    r"\\scB": r"\\mathscr{B}",
    r"\\scF": r"\\mathscr{F}",
    r"\\G": r"\\mathscr{G}",
    r"\\Exp": r"\\mathsf{Exp}",
    r"\\DExp": r"\\mathsf{DExp}",
    r"\\Lap": r"\\mathsf{Lap}",
    r"\\calP": r"\\mathcal P",
    r"\\calS": r"\\mathcal S",
    r"\\calF": r"\\mathcal F",
    r"\\calM": r"\\mathcal M",
    r"\\KL": r"\\mathrm{KL}",
    r"\\ReLU": r"\\mathsf{ReLU}",
    r"\\val": r"\\mathsf{val}",
}


# Commands with arguments
LATEX_COMMANDS = {
    "\\norm": (1, "\\left\\|{#1}\\right\\|"),
    "\\inner": (2, "\\left\\langle{#1},{#2}\\right\\rangle"),
    "\\light": (1, "\\textcolor{Orchid}{#1}"),
    "\\contrastlight": (1, "\\textcolor{TealBlue}{#1}")
}


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
