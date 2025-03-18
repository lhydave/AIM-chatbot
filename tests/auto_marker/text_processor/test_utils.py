import pytest
from auto_marker.text_processor.utils import convert_to_arabic_number
from auto_marker.text_processor.utils import extract_chapter_id

def test_arabic_numerals():
    assert convert_to_arabic_number("123") == 123
    assert convert_to_arabic_number("0") == 0
    assert convert_to_arabic_number("9") == 9

def test_single_chinese_numerals():
    assert convert_to_arabic_number("零") == 0
    assert convert_to_arabic_number("一") == 1
    assert convert_to_arabic_number("二") == 2
    assert convert_to_arabic_number("三") == 3
    assert convert_to_arabic_number("四") == 4
    assert convert_to_arabic_number("五") == 5
    assert convert_to_arabic_number("六") == 6
    assert convert_to_arabic_number("七") == 7
    assert convert_to_arabic_number("八") == 8
    assert convert_to_arabic_number("九") == 9
    assert convert_to_arabic_number("十") == 10

def test_complex_chinese_numerals():
    assert convert_to_arabic_number("十一") == 11
    assert convert_to_arabic_number("二十") == 20
    assert convert_to_arabic_number("二十五") == 25
    assert convert_to_arabic_number("一百") == 100
    assert convert_to_arabic_number("一百二十三") == 123
    assert convert_to_arabic_number("一千") == 1000
    assert convert_to_arabic_number("一千二百三十四") == 1234
    assert convert_to_arabic_number("一万") == 10000
    assert convert_to_arabic_number("一亿") == 100000000

def test_invalid_input():
    with pytest.raises(ValueError):
        convert_to_arabic_number("   ")
    with pytest.raises(ValueError):
        convert_to_arabic_number("abc")
    with pytest.raises(ValueError):
        convert_to_arabic_number("abc123")
    with pytest.raises(ValueError):
        convert_to_arabic_number("123abc")

def test_extract_chapter_id_chinese():
    assert extract_chapter_id("第一章") == "1"
    assert extract_chapter_id("第二章") == "2"
    assert extract_chapter_id("第十章") == "10"
    assert extract_chapter_id("第十五章") == "15"
    assert extract_chapter_id("第二十三章") == "23"

def test_extract_chapter_id_arabic():
    assert extract_chapter_id("第1章") == "1"
    assert extract_chapter_id("第10章") == "10"
    assert extract_chapter_id("第123章") == "123"

def test_extract_chapter_id_with_content():
    assert extract_chapter_id("第一章：绪论") == "1"
    assert extract_chapter_id("第5章 - 线性代数") == "5"
    assert extract_chapter_id("内容：第二章 数学基础") == "2"

def test_extract_chapter_id_no_match():
    assert extract_chapter_id("章节一") == "章节一"
    assert extract_chapter_id("没有章节") == "没有章节"
    assert extract_chapter_id("Chapter 1") == "Chapter 1"

def test_extract_chapter_id_invalid_content():
    assert extract_chapter_id("第abc章") == "abc"
    assert extract_chapter_id("第 章") == " "
