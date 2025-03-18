import re


def convert_to_arabic_number(text: str) -> int:
    """
    Convert Chinese or Arabic numerals to Arabic numbers.

    Args:
        text: The text containing Chinese or Arabic numerals

    Returns:
        The converted Arabic number
    """
    text = text.strip()

    if not text:
        raise ValueError("Empty string cannot be converted to a number")

    # If already an Arabic number, try to convert directly
    try:
        return int(text)
    except ValueError:
        pass

    # Chinese numeral mapping
    cn_num = {
        "零": 0,
        "一": 1,
        "二": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
        "十": 10,
        "百": 100,
        "千": 1000,
        "万": 10000,
        "亿": 100000000,
    }

    result = 0
    temp = 0

    # Handle special case of just "十" meaning 10
    if text == "十":
        return 10

    for i in range(len(text)):
        if text[i] in cn_num:
            # For characters like 十, 百, 千, 万, 亿

            if cn_num[text[i]] >= 10:
                # If we had a temporary value, multiply it
                if temp == 0:
                    temp = 1
                result += temp * cn_num[text[i]]
                temp = 0
            else:
                # For characters like 一, 二, 三...
                temp = temp * 10 + cn_num[text[i]]
        else:
            raise ValueError(
                f"Invalid character when converting {text} to Arabic number: {text[i]}"
            )

    # Add any remaining temporary value
    result += temp

    return result


def extract_chapter_id(text: str) -> str:
    """
    Extract the chapter ID from a string.

    Args:
        text: The text containing the chapter ID, such as "第一章" or "第1章"

    Returns:
        The extracted chapter ID. If not found, returns the raw text."
    """
    # Match the chapter ID using a regular expression
    match = re.search(r"第([\s\S]+)章", text)
    if match:
        try:
            return str(convert_to_arabic_number(match.group(1)))
        except ValueError:
            return match.group(1)
    return text


def extract_problem_id(text: str) -> str:
    """
    Extract the problem ID from a string.

    Args:
        text: The text containing the problem ID, which should be a number or string like "extra"

    Returns:
        The extracted problem ID. If not found, returns the raw text.
    """
    # Match the problem ID using a regular expression
    match = re.search(r"(\d+|extra|Extra)\.?", text)
    if match:
        if match.group(1).lower() == "extra":
            return "extra"
        return match.group(1)
    return text
