import json
import os
from auto_marker.text_processor.tex_processor import parse_content
from auto_marker.basics import ProblemID


def test_markdown_parser():
    # Path to the sample markdown file
    file_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        "src",
        "auto_marker",
        "sample-homework",
        "sample-tex-homework.tex",
    )

    problem_list = [
        ProblemID.from_str("chap1.prob2(1)(2)"),
        ProblemID.from_str("chap1.prob5"),
        ProblemID.from_str("chap1.prob6"),
        ProblemID.from_str("chap1.prob7"),
        ProblemID.from_str("chap1.prob8"),
        ProblemID.from_str("chap1.prob10"),
        ProblemID.from_str("chap1.prob11"),
        ProblemID.from_str("chap1.prob12"),
        ProblemID.from_str("chap2.prob1"),
    ]

    # Read the file
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Parse the content
    answer_group = parse_content(content, problem_list)

    # Print as formatted JSON for manual inspection
    # Define the output file path
    output_path = os.path.join(os.path.dirname(__file__), "tex_parser_output.json")

    # Write to JSON file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(answer_group.to_json(), f, indent=2, ensure_ascii=False)

    print(f"JSON output written to {output_path}")
