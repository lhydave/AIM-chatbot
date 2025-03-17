from util import replaceMacros


def test_replaceMacros_simple():
    content = r"The set \Z is a subset of \R"
    result = replaceMacros(content)
    assert result == r"The set \mathbb{Z} is a subset of \mathbb{R}"

def test_replaceMacros_overlap():
    content = r"Symbol \to is not \t"
    result = replaceMacros(content)
    assert result == r"Symbol \to is not \mathsf{T}"

def test_replaceMacros_multiple():
    content = r"\Z \N \R \Q \C"
    result = replaceMacros(content)
    assert result == r"\mathbb{Z} \mathbb{N} \mathbb{R} \mathbb{Q} \mathbb{C}"

def test_replaceMacros_with_commands():
    content = r"\norm{x} and \inner{a}{b}"
    result = replaceMacros(content)
    assert result == r"\left\|{x}\right\| and \left\langle{a},{b}\right\rangle"

def test_replaceMacros_mixed():
    content = r"Let \Z be a set and \norm{x} be its norm"
    result = replaceMacros(content)
    assert result == r"Let \mathbb{Z} be a set and \left\|{x}\right\| be its norm"

def test_replaceMacros_empty():
    content = ""
    result = replaceMacros(content)
    assert result == ""

def test_replaceMacros_no_replacements():
    content = "Plain text without macros"
    result = replaceMacros(content)
    assert result == "Plain text without macros"

def test_replaceMacros_operators():
    content = r"\rank(A) + \im(f) = \Span{v}"
    result = replaceMacros(content)
    assert result == r"\operatorname{rank}(A) + \operatorname{Im}(f) = \operatorname{Span}{v}"

def test_replaceMacros_nested_norm():
    content = r"\norm{\norm{x}}"
    result = replaceMacros(content) 
    assert result == r"\left\|{\left\|{x}\right\|}\right\|"
