"""
LaTeX 宏配置文件
"""

# LaTeX 宏和他们对应的原始定义
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


# LaTeX 带参数的宏
LATEX_COMMANDS = {
    "\\norm": (1, "\\left\\|{#1}\\right\\|"),
    "\\inner": (2, "\\left\\langle{#1},{#2}\\right\\rangle"),
    "\\light": (1, "\\textcolor{Orchid}{#1}"),
    "\\contrastlight": (1, "\\textcolor{TealBlue}{#1}")
}
