"""
Parse the latex file and make them into pieces of contents.
"""

import re
import os
import itertools
import textwrap

sectionOrder = ("part", "chapter", "section", "subsection")


def multiTex2Single(mainDir: str, mainContent: str):
    # Find all \input{xxx} patterns
    pattern = r"\\(?:input|include)\{([^}]+)\}"
    result = mainContent
    while True:
        matches = re.finditer(pattern, result)
        is_empty = True

        # Replace each match with the content of referenced file
        for match in matches:
            is_empty = False
            filepath = os.path.join(mainDir, match.group(1) + ".tex")
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            result = result.replace(match.group(0), content)
        if is_empty:
            break
    return result


def stripDocument(content: str) -> str:
    pattern = r"\\begin\{document\}([\s\S]*?)\\end\{document\}"
    match = re.search(pattern, content)
    if match:
        return match.group(1).strip()
    else:
        return content.strip()


def stripAppendix(content: str) -> str:
    pattern = r"([\s\S]*?)\\appendix[\s\S]*"
    match = re.match(pattern, content)
    if match:
        return match.group(1).strip()
    else:
        return content.strip()


def splitTexBy(content: str, label: str):
    # Find all \label{xxx} patterns
    pattern = r"(\\label\{[\s\S]*?\}[\s\S]*?|[\s\S]+?)(?=\\label\{|$)"
    pattern = pattern.replace("label", label)
    matches = re.finditer(pattern, content)

    result = [match.group(0).strip() for match in matches]
    result = filter(lambda x: x, result)
    return result


def splitTexBySection(content: str):
    ret = splitTexBy(content, sectionOrder[0])
    for i in range(1, len(sectionOrder)):
        ret = itertools.chain.from_iterable(
            map(lambda x: splitTexBy(x, sectionOrder[i]), ret)
        )
    return ret


def splitTexByEnv(content: str):
    # 正则表达式匹配 LaTeX 环境或非环境文本
    pattern = r"(\\begin\{([^}]+)\}([\s\S]*?)\\end\{\2\}|([\s\S]+?(?=\\begin\{|$)))"
    matches = re.findall(pattern, content)

    # 存储分割后的结果
    parts: list[str] = []
    for match in matches:
        if match[0].startswith("\\begin"):  # 如果是环境
            parts.append(match[0])
        else:  # 如果是非环境文本
            text = match[0].strip()
            if text:  # 忽略空文本
                parts.append(text)

    return parts


def splitTexByPar(content: str):
    return filter(lambda x: x.strip(), map(lambda x: x.strip(), content.split("\n\n")))


def split_single_file(mainPath: str, maxChunkSize: int):
    """
    split the single tex file into pieces
    """
    # Read and process the main file
    mainDir = os.path.dirname(mainPath)
    try:
        with open(mainPath, "r", encoding="utf-8") as f:
            mainContent = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Could not find file: {mainPath}")
    except IOError as e:
        raise IOError(f"Error reading file {mainPath}: {str(e)}")

    # Strip document environment
    mainContent = stripDocument(mainContent)

    # Strip the appendix
    mainContent = stripAppendix(mainContent)

    # Merge all tex files into one
    mainContent = multiTex2Single(mainDir, mainContent)

    # Split by sections
    sectionParts = splitTexBySection(mainContent)

    # Split each section by environments
    envParts = itertools.chain.from_iterable(map(splitTexByEnv, sectionParts))

    # Split each environment part by paragraphs
    parParts = itertools.chain.from_iterable(map(splitTexByPar, envParts))

    ret: list[str] = []
    currentChunk = ""
    for part in parParts:
        if len(part) + len(currentChunk) <= maxChunkSize:
            currentChunk += part
            continue
        if currentChunk:
            ret.append(currentChunk)
            currentChunk = ""

        if len(part) >= maxChunkSize:  # the part itself is too big
            ret.extend(textwrap.wrap(part, maxChunkSize))
        else:  # just good
            ret.append(part)
    return ret


def split_contents(contentPaths: list[str], maxChunkSize: int):
    ret: list[str] = []
    for contentPath in contentPaths:
        ret.extend(split_single_file(contentPath, maxChunkSize))
    return ret


if __name__ == "__main__":
    import tomllib
    config_path = './my_config.toml'
    with open(config_path, 'br') as f:
        config = tomllib.load(f)

    # Extract configuration values
    textbook_main_paths = config['textbook_main_paths']
    max_chunk_size = config['max_chunk_size']


    # Split the book and write chunks to file
    chunks = split_contents(textbook_main_paths, max_chunk_size)
    with open("book_chunks.txt", "w", encoding="utf-8") as f:
        for i, chunk in enumerate(chunks):
            f.write(f"=== Chunk {i} ===\n{chunk}\n\n")
