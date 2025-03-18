import json
import os
from auto_marker.text_processor.markdown_processor import parse_content


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
        "sample-markdown-homework.md",
    )

    # Read the file
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Parse the content
    answer_group = parse_content(content)

    # Print as formatted JSON for manual inspection
    # Define the output file path
    output_path = os.path.join(os.path.dirname(__file__), "markdown_parser_output.json")

    # Write to JSON file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(answer_group.to_json(), f, indent=2, ensure_ascii=False)

    print(f"JSON output written to {output_path}")
