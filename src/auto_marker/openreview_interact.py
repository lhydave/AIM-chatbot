from dataclasses import dataclass
from typing import Literal
import openreview
import openreview.api
from openreview import Note
import asyncio
import os
import zipfile
import chardet
import logging
from auto_marker.basics import StudentSubmission, parse_submission_title

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Files to skip when extracting ZIP files
ZIP_SKIP_FILES = [
    "__MACOSX",
    ".log",
    ".bbl",
    ".fdb_latexmk",
    ".fls",
    ".idx",
    ".ilg",
    ".ind",
    ".log",
    ".out",
    ".synctex.gz",
    ".synctex.gz(busy)",
    ".synctex(busy)",
    ".thm",
    ".toc",
    ".xdv",
    ".vscode",
    ".aux",
    ".run.xml",
    ".blg",
    ".DS_Store",
]


@dataclass
class OpenReviewConfig:
    """Configuration for OpenReview API access.

    Attributes:
        baseurl: Base URL for the OpenReview API (e.g., 'https://api.openreview.net').
        username: Username/email used for authenticating with OpenReview.
        password: Password associated with the username for OpenReview authentication.
        venue_id: The identifier for the venue/conference in OpenReview (e.g., 'ICLR.cc/2023/Conference').
        submission_store_path: Local file system path where downloaded submissions will be stored.
    """

    username: str
    password: str
    venue_id: str
    submission_store_path: str
    base_url: str = "https://api2.openreview.net"


def save_and_process_pdf(pdf_binary: bytes, title: str, submission_dir: str) -> None:
    """
    Save the PDF attachment of a submission.

    Args:
        pdf_binary: Binary content of the PDF
        title: The submission title
        submission_dir: Directory to save the PDF
    """
    if pdf_binary:
        pdf_path = os.path.join(submission_dir, "Submission-PDF.pdf")
        with open(pdf_path, "wb") as f:
            f.write(pdf_binary)


def extract_zip_file(zip_path: str, target_path: str) -> None:
    """
    Extract a ZIP file using the 7z command line tool.

    Args:
        zip_path: Path to the ZIP file
        target_path: Directory where the contents should be extracted
    """
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        # Get all files in the zip
        zip_list = zip_ref.namelist()
        for zip_file_name in zip_list:
            # fix encoding bugs in ZipFile for Windows platform
            new_file_name = zip_file_name
            encoding_decoding_pairs = [
                ("cp437", "gbk"),
                ("cp437", "gb2312"),
            ]
            for encoding, decoding in encoding_decoding_pairs:
                try:
                    new_file_name = zip_file_name.encode(encoding).decode(decoding)
                    break
                except Exception:
                    continue
            else:
                # seems no encoding problem
                new_file_name = zip_file_name

            # skip files that should be skipped
            if any(skip_file in new_file_name for skip_file in ZIP_SKIP_FILES):
                continue

            if new_file_name.endswith("/"):
                # create directory
                os.makedirs(os.path.join(target_path, new_file_name), exist_ok=True)
            else:
                with open(os.path.join(target_path, new_file_name), "wb") as f:
                    f.write(zip_ref.read(zip_file_name))


def process_source_code(
    source_binary: bytes, title: str, submission_dir: str
) -> tuple[str, Literal["markdown", "tex"]]:
    """
    Extract and process source code files from a submission.

    Args:
        source_binary: Binary content of the source code (zip file)
        title: The submission title
        submission_dir: Directory to save and extract source files

    Returns:
        raw_source_code: The raw content of the first .tex or .md file found
        code_language: The language of the source code file (markdown or latex)
    """
    source_files = {}
    try:
        # Assuming source_binary is a single zip file
        zip_path = os.path.join(submission_dir, "source_code.zip")
        with open(zip_path, "wb") as f:
            f.write(source_binary)

        # Extract the zip file using the dedicated function
        extract_zip_file(zip_path, submission_dir)

        logger.info(f"Extracted source code files for submission {title}")

        # Check if there's only one directory after extraction
        extracted_items = os.listdir(submission_dir)
        extracted_items = [
            item for item in extracted_items if item != "source_code.zip" and item != "Submission-PDF.pdf"
        ]
        logger.debug(f"Extracted items: {extracted_items}")

        if len(extracted_items) == 1:
            single_dir = os.path.join(submission_dir, extracted_items[0])
            # Check if it's a directory
            if os.path.isdir(single_dir):
                # Move contents of the single directory up one level
                for item in os.listdir(single_dir):
                    source_path = os.path.join(single_dir, item)
                    dest_path = os.path.join(submission_dir, item)
                    os.rename(source_path, dest_path)
                # Remove the now empty directory
                os.rmdir(single_dir)

        # Get all extracted files for further processing
        for root, _, files in os.walk(submission_dir):
            for file in files:
                if file == "source_code.zip" or file == "Submission-PDF.pdf":
                    continue
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, submission_dir)

                # Read the file content
                with open(file_path, "rb") as f:
                    content = f.read()
                    source_files[rel_path] = content
    except Exception as e:
        logger.warning(f"Error processing source files for submission {title}: {str(e)}")

    # Find .tex or .md files
    tex_md_files = {}
    for filename, content in source_files.items():
        if filename.endswith(".tex") or filename.endswith(".md"):
            # Try to decode content to text if it's binary
            if not isinstance(content, bytes):
                logger.warning(f"{filename} is not a binary file, skipping")
                continue
            encoding = chardet.detect(content)
            if encoding:
                text_content = content.decode(encoding["encoding"])
            else:
                text_content = content.decode("utf-8")

            tex_md_files[filename] = text_content

    raw_source_code = ""
    code_language = "markdown"  # Default value

    if tex_md_files:
        # Just take the first source file regardless of how many there are
        filename, content = next(iter(tex_md_files.items()))
        raw_source_code = content

        # Determine the language based on file extension
        if filename.endswith(".tex"):
            code_language = "tex"
        elif filename.endswith(".md"):
            code_language = "markdown"

        # Log a message if we're ignoring additional files
        if len(tex_md_files) > 1:
            logger.info(f"Multiple source files found for {title}, using only {filename}")
    else:
        logger.warning(f"No valid source files (.tex or .md) found for submission {title}")

    return raw_source_code, code_language


class OpenReviewInteract:
    """Class for interacting with OpenReview to download and organize student submissions."""

    def __init__(self, config: OpenReviewConfig):
        self.config = config
        logger.info(f"Initializing OpenReview client with base URL: {config.base_url}")
        try:
            self.client = openreview.api.OpenReviewClient(
                baseurl=config.base_url, username=config.username, password=config.password
            )
            logger.info("OpenReview client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenReview client: {str(e)}")
            raise

    def get_submissions(self) -> list[Note]:
        """Get all submissions for the configured venue."""
        try:
            venue_group = self.client.get_group(self.config.venue_id)
            submission_name = venue_group.get_content_value("submission_name")
            if not submission_name:
                logger.error("Submission name not found in venue configuration")
                raise ValueError("Submission name not found in venue configuration")

            logger.info(f"Fetching submissions for venue: {self.config.venue_id}")
            submissions = self.client.get_all_notes(invitation=f"{self.config.venue_id}/-/{submission_name}")
            logger.info(f"Successfully fetched {len(submissions)} submissions")
            return submissions
        except Exception as e:
            logger.error(f"Error fetching submissions: {str(e)}")
            raise

    def process_all_submissions(self, homework_id: str) -> tuple[list[StudentSubmission], list[str]]:
        """
        Process all submissions:
        1. Parse title to extract homework ID, student ID and name
        2. Download PDF and source code
        3. Extract source code files
        4. Organize everything into proper directories

        Returns:
            Tuple containing:
            - List of successfully processed student submissions
            - List of titles of submissions that failed to process
        """
        ret = asyncio.run(self.async_process_all_submissions(homework_id))
        return ret

    async def async_process_all_submissions(self, homework_id: str) -> tuple[list[StudentSubmission], list[str]]:
        """
        Process all submissions asynchronously. This is the async version of process_all_submissions.
        """
        logger.info(f"Processing submissions for homework ID: {homework_id}")
        submissions = self.get_submissions()

        valid_submissions = []
        failed_submission_titles = []

        tasks = []
        for submission in submissions:
            title = submission.content.get("title", "").get("value", "")
            try:
                hw_id, _, _ = parse_submission_title(title)
                # If homework_id doesn't match, skip this submission
                if hw_id != homework_id:
                    continue

                # Create task for concurrent processing
                tasks.append(self.process_submission(submission))
            except ValueError as e:
                # This is a parsing error, not a homework_id mismatch
                logger.error(f"Error processing submission {title}: {str(e)}")
                failed_submission_titles.append(title)

        # Process all submissions concurrently
        logger.info(f"Concurrently processing {len(tasks)} submissions")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for result in results:
            if isinstance(result, Exception):
                # If an exception occurred during processing
                logger.error(f"Error processing submission: {str(result)}")
            # Note: We can't easily map back to the title here
            # Consider adding a wrapper function that preserves the title
            else:
                valid_submissions.append(result)

        logger.info(
            f"Successfully processed {len(valid_submissions)} submissions, failed: {len(failed_submission_titles)}"
        )
        return valid_submissions, failed_submission_titles

    async def process_submission(self, submission: Note) -> StudentSubmission:
        """Process a single submission asynchronously.

        1. Download PDF and source code
        2. Extract content from .tex or .md files
        3. Save files to organized directory structure
        4. Return structured StudentSubmission object
        """
        title = submission.content.get("title", "").get("value", "")

        logger.info(f"Processing submission with title: {title}")

        try:
            homework_id, student_id, student_name = parse_submission_title(title)
        except ValueError:
            logger.error(f"Failed to parse submission title format: {title}")
            raise ValueError(f"Failed to parse submission title format: {title}")

        logger.info(
            f"Parsed title successfully: Homework ID: {homework_id}, Student ID: {student_id}, Student Name: {student_name}"  # noqa: E501
        )

        # Create directory structure: submission_store_path/HWxxx/学号-姓名/
        submission_dir = os.path.join(
            self.config.submission_store_path,
            f"HW{homework_id}",
            f"{student_id}-{student_name}",
        )
        os.makedirs(submission_dir, exist_ok=True)

        # Get submission files using OpenReview API v2
        submission_id = submission.id
        if not submission_id:
            logger.error(f"Submission ID not found for submission {title}")
            raise ValueError(f"Submission ID not found for submission {title}")

        # Download PDF
        pdf_binary = None
        try:
            logger.info(f"Downloading PDF for submission {title}")
            pdf_binary = self.client.get_attachment("pdf", submission_id)
            save_and_process_pdf(pdf_binary, title, submission_dir)
            logger.info(f"Successfully downloaded PDF for {title}")
        except Exception as e:
            logger.warning(f"Could not download PDF for submission {title}: {str(e)}")

        # Download source code
        source_binary = None
        raw_source_code = ""
        code_language: Literal["markdown", "tex"] = "markdown"
        try:
            logger.info(f"Downloading source code for submission {title}")
            source_binary = self.client.get_attachment("source_code", submission_id)
            raw_source_code, code_language = process_source_code(source_binary, title, submission_dir)
            logger.info(f"Successfully processed source code for {title}")
        except Exception as e:
            logger.warning(f"Could not download source files for submission {title}: {str(e)}")

        # Create and return StudentSubmission object
        return StudentSubmission(
            homework_id=homework_id,
            student_id=student_id,
            student_name=student_name,
            raw_source_code=raw_source_code,
            code_language=code_language,
            processed_source_code=None,
        )

    def post_reviews(
        self,
        student_submissions: list[StudentSubmission],
        review_contents: dict[str, str],
    ) -> tuple[list[str], list[str]]:
        """
        Post reviews for student submissions to OpenReview.

        Args:
            student_submissions: List of student submissions to review
            review_contents: Dictionary mapping student IDs to review content

        Returns:
            Tuple containing:
            - List of successfully posted review submission IDs
            - List of student IDs for which review posting failed
        """
        ret = asyncio.run(self.async_post_reviews(student_submissions, review_contents))
        return ret

    async def post_single_review(
        self, student_submission: StudentSubmission, submission: Note, review_content: str
    ) -> None:
        """
        Post a review for a single student submission.

        Args:
            student_submission: The student submission to review
            submission: The OpenReview submission Note
            review_content: The content of the review
        """
        submission_number = submission.number
        logger.info(f"Posting review for submission {submission_number} (Student: {student_submission.student_id})")

        try:
            # Use the user's own profile ID directly instead of looking for anonymous groups
            if not self.client.profile:
                logger.error("User profile not found, cannot post review")
                raise ValueError("User profile not found, cannot post review")

            signature = self.client.profile.id
            logger.info(f"Using direct user profile as signature: {signature}")

            # Create the review note
            review_note = openreview.api.Note(
                content={
                    "title": {"value": f"Marks for {student_submission.student_id}"},
                    "review": {"value": review_content},
                }
            )

            # Post the review using direct signature
            review_edit = self.client.post_note_edit(
                invitation=f"{self.config.venue_id}/Submission{submission_number}/-/Official_Review",
                signatures=[signature],
                note=review_note,
            )

            logger.debug(f"Review edit response: {review_edit}")

            logger.info(f"Successfully posted review for submission {submission_number}")

        except Exception as e:
            logger.error(f"Error posting review for submission {submission_number}: {str(e)}")
            raise

    async def async_post_reviews(
        self,
        student_submissions: list[StudentSubmission],
        review_contents: dict[str, str],
    ) -> tuple[list[str], list[str]]:
        """
        Post reviews for student submissions to OpenReview asynchronously. This is the async version of post_reviews.
        """
        logger.info(f"Posting reviews for {len(student_submissions)} submissions")
        try:
            venue_group = self.client.get_group(self.config.venue_id)
            submission_name = venue_group.get_content_value("submission_name")

            if not submission_name:
                logger.error("Submission name not found in venue configuration")
                raise ValueError("Submission name not found in venue configuration")

            # Get all submissions to find their IDs
            logger.info("Fetching all submissions to map student IDs to submission IDs")
            all_submissions = self.get_submissions()
            submission_map = {}
            for submission in all_submissions:
                title = submission.content.get("title", "").get("value", "")
                try:
                    _, student_id, _ = parse_submission_title(title)
                    submission_map[student_id] = submission
                except ValueError:
                    # Skip submissions with invalid titles
                    logger.warning(f"Invalid title format for submission: {title}")
                    continue

            successful_reviews = []
            failed_reviews = []

            # Create tasks for parallel processing
            tasks = []
            task_metadata = []  # Store metadata to track which task is for which submission

            for student_submission in student_submissions:
                student_id = student_submission.student_id

                # Skip if no review content is available for this student
                if student_id not in review_contents:
                    logger.warning(f"No review content available for student {student_id}")
                    failed_reviews.append(student_id)
                    continue

                # Skip if submission not found
                if student_id not in submission_map:
                    logger.warning(f"No submission found for student {student_id}")
                    failed_reviews.append(student_id)
                    continue

                submission = submission_map[student_id]
                # Create task for concurrent processing
                tasks.append(self.post_single_review(student_submission, submission, review_contents[student_id]))
                # Store metadata to identify the task result later
                task_metadata.append((student_id, submission.id))

            # Execute all tasks concurrently
            if tasks:
                logger.info(f"Concurrently posting {len(tasks)} reviews")
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Process results
                for i, result in enumerate(results):
                    student_id, submission_id = task_metadata[i]
                    if isinstance(result, Exception):
                        # An exception occurred during posting
                        logger.error(f"Failed to post review for student {student_id}: {str(result)}")
                        failed_reviews.append(student_id)
                    else:
                        # Success (post_single_review completed without exception)
                        successful_reviews.append(submission_id)
                        logger.info(f"Successfully posted review for student {student_id}, submission {submission_id}")

            logger.info(f"Posted {len(successful_reviews)} reviews successfully, {len(failed_reviews)} failed")
            return successful_reviews, failed_reviews

        except Exception as e:
            logger.error(f"Error in async_post_reviews: {str(e)}")
            raise
