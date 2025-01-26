from content_construct import *
import os

def test_multiTex2Single():
    # Create test directory and files
    os.makedirs("./tests/sections", exist_ok=True)
    
    # Create main tex file
    mainContent = r"""\documentclass{ctexart}
\begin{document}
\input{sections/testTex1}
\input{sections/testTex2}
\end{document}
"""
    
    # Create included tex files
    with open("./tests/sections/testTex1.tex", "w", encoding="utf-8") as f:
        f.write("This is test file.\n\n\\section{Test section}")
        
    with open("./tests/sections/testTex2.tex", "w", encoding="utf-8") as f:
        f.write("This is another test file.\n\n\\section{Test another section}")

    # Run test
    mainDir = "./tests"
    ret = multiTex2Single(mainDir, mainContent)
    
    # Cleanup
    os.remove("./tests/sections/testTex1.tex")
    os.remove("./tests/sections/testTex2.tex")
    os.rmdir("./tests/sections")
    
    # Assert
    assert (
        ret
        == r"""\documentclass{ctexart}
\begin{document}
This is test file.

\section{Test section}
This is another test file.

\section{Test another section}
\end{document}
"""
    )


def test_splitTexBy():
    content = r"""\chapter{aaaa}
not good
\section{good}
some good things!

\section{better}
some better things!"""
    label = "section"
    ret = splitTexBy(content, label)
    assert ret == [
        r"""\chapter{aaaa}
not good""",
        r"""\section{good}
some good things!""",
        r"""\section{better}
some better things!""",
    ]

def test_stripDocument():
    content = r"""\documentclass{article}
\begin{document}
This is some content
With multiple lines
\end{document}"""
    result = stripDocument(content)
    assert result == "This is some content\nWith multiple lines"

def test_stripDocument_empty_document():
    content = r"""\documentclass{article}
\begin{document}

\end{document}"""
    result = stripDocument(content)
    assert result == ""

def test_splitTexByEnv_with_mixed_content():
    content = r"""Some text here
\begin{theorem}
Important theorem content
\end{theorem}
More text
\begin{example}
Example content
\end{example}"""
    ret = splitTexByEnv(content)
    assert ret == [
        "Some text here",
        r"""\begin{theorem}
Important theorem content
\end{theorem}""",
        "More text",
        r"""\begin{example}
Example content
\end{example}"""
    ]

def test_splitTexByEnv_only_environments():
    content = r"""\begin{definition}
Definition content
\end{definition}

\begin{theorem}
Theorem content
\end{theorem}"""
    ret = splitTexByEnv(content)
    assert ret == [
        r"""\begin{definition}
Definition content
\end{definition}""",
        r"""\begin{theorem}
Theorem content
\end{theorem}"""
    ]

def test_splitTexByEnv_only_text():
    content = "Just some plain text\nwith multiple lines"
    ret = splitTexByEnv(content) 
    assert ret == ["Just some plain text\nwith multiple lines"]

def test_splitTexByEnv_empty():
    content = ""
    ret = splitTexByEnv(content)
    assert ret == []
def test_splitTexByPar_basic():
    content = "First paragraph\n\nSecond paragraph\n\nThird paragraph"
    ret = splitTexByPar(content)
    assert ret == ["First paragraph", "Second paragraph", "Third paragraph"]

def test_splitTexByPar_with_multiple_newlines():
    content = "First\n\n\nSecond\n\n\n\nThird"
    ret = splitTexByPar(content)
    assert ret == ["First", "Second", "Third"]

def test_splitTexByPar_with_empty_paragraphs():
    content = "First\n\n\n\nSecond"
    ret = splitTexByPar(content)
    assert ret == ["First", "Second"]

def test_splitTexByPar_single_paragraph():
    content = "Just one paragraph"
    ret = splitTexByPar(content)
    assert ret == ["Just one paragraph"]

def test_splitTexByPar_empty():
    content = ""
    ret = splitTexByPar(content)
    assert ret == []