import re
import os
import smtplib
import csv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from auto_marker.logging import logger, configure_global_logger


def get_email_settings(email: str) -> tuple[str, int]:
    """
    Get SMTP server and port based on email domain.

    Args:
        email: Email address

    Returns:
        Tuple containing SMTP server and port
    """
    if email.endswith("@pku.edu.cn"):
        return "smtp.pku.edu.cn", 465
    elif email.endswith("@stu.pku.edu.cn"):
        return "smtphz.qiye.163.com", 994
    else:
        # Default to PKU settings if no match
        logger.warning(f"Unknown email domain for {email}, using default PKU settings")
        return "smtp.pku.edu.cn", 465


class EmailNotifier:
    """Class for sending email notifications to students based on log warnings."""

    def __init__(self, smtp_server: str, smtp_port: int):
        """
        Initialize the EmailNotifier.

        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP server port
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port

    def parse_logs(self, download_log_path: str, process_log_path: str) -> dict[str, tuple[str, list[str]]]:
        """
        Parse download and process logs to extract warnings by student ID.

        Args:
            download_log_path: Path to the download log file
            process_log_path: Path to the process log file

        Returns:
            Dictionary mapping student IDs to tuples of (student_name, list of warning messages)
        """
        logger.info(f"Parsing logs from {download_log_path} and {process_log_path}")

        # Dictionary to store warnings by student ID: {student_id: (student_name, [warnings])}
        warnings_by_student: dict[str, tuple[str, list[str]]] = {}

        # Parse download log
        if os.path.exists(download_log_path):
            with open(download_log_path) as file:
                # Find lines with WARNING and extract student IDs, names, Homework IDs and submission numbers
                for line in file:
                    if "WARNING" not in line:
                        continue
                    warning_message = line.split("WARNING - ")[-1].strip()
                    match = re.search(r"for (HW\d+)-(\d{10})-(.+?),", warning_message)
                    if match:
                        hw_id, student_id, student_name = match.groups()
                        if student_id not in warnings_by_student:
                            warnings_by_student[student_id] = (student_name, [])
                        warnings_by_student[student_id][1].append(warning_message)

        # Parse process log
        if os.path.exists(process_log_path):
            with open(process_log_path) as file:
                current_student_id = None
                current_student_name = "Unknown"

                for line in file:
                    # Check if line indicates starting to process a new submission
                    submission_match = re.search(r"Parsing submission \d+-(\d{10})-(.+?)\.{3}", line)
                    if submission_match:
                        current_student_id = submission_match.group(1)
                        current_student_name = submission_match.group(2)

                    # Initialize the student entry if not exists
                    if not current_student_id:
                        continue
                    if current_student_id not in warnings_by_student:
                        warnings_by_student[current_student_id] = (current_student_name, [])
                    else:
                        # Update name if it was unknown
                        name, warnings = warnings_by_student[current_student_id]
                        if name == "Unknown":
                            warnings_by_student[current_student_id] = (current_student_name, warnings)

                    # Check if line contains a warning and there is a current student ID
                    if current_student_id and "WARNING" in line:
                        warning_message = line.split("WARNING - ")[-1].strip()
                        warnings_by_student[current_student_id][1].append(warning_message)

        # Convert from {id: (name, [warnings])} to {id: (name, [warnings])}
        final_warnings: dict[str, tuple[str, list[str]]] = {}
        for student_id, (name, warnings) in warnings_by_student.items():
            if warnings:
                final_warnings[student_id] = (name, warnings)

        logger.info(f"Found warnings for {len(final_warnings)} students")
        return final_warnings

    def categorize_warnings(self, warnings: list[str]) -> dict[str, list[str]]:
        """
        Categorize warnings into different types.

        Args:
            warnings: list of warning messages

        Returns:
            dictionary mapping warning categories to lists of warning messages
        """
        categories = {
            "submission_issues": [],
            "format_issues": [],
            "problem_id_issues": [],
            "subproblem_issues": [],
            "other_issues": [],
        }

        for warning in warnings:
            if "duplicate" in warning:
                categories["submission_issues"].append(warning)
            elif "No valid source files" in warning:
                categories["submission_issues"].append(warning)
            elif "Multiple source files found" in warning:
                categories["submission_issues"].append(warning)
            elif "ill-formatted" in warning.lower():
                categories["format_issues"].append(warning)
            elif "between \\begin{{enumerate}} and first \\item in" in warning.lower():
                categories["format_issues"].append(warning)
            elif "content after \\end{{enumerate}}" in warning.lower():
                categories["format_issues"].append(warning)
            elif "problem id" in warning.lower() and "not found" in warning.lower():
                categories["problem_id_issues"].append(warning)
            elif "no problems found" in warning.lower():
                categories["problem_id_issues"].append(warning)
            elif "subproblem" in warning.lower():
                categories["subproblem_issues"].append(warning)
            else:
                categories["other_issues"].append(warning)

        # Check if only submission_issues is non-empty
        other_categories_empty = all(
            len(categories[cat]) == 0
            for cat in ["format_issues", "problem_id_issues", "subproblem_issues", "other_issues"]
        )

        # it is okay to have submission_issues only since it does not affect the grading
        if other_categories_empty and categories["submission_issues"]:
            categories["submission_issues"] = []

        return categories

    def generate_email_content(
        self, student_id: str, student_name: str, categorized_warnings: dict[str, list[str]]
    ) -> tuple[str, str]:
        """
        Generate email subject and body for a student based on their warnings.

        Args:
            student_id: Student ID
            student_name: Student name
            categorized_warnings: dictionary of warnings categorized by type

        Returns:
            tuple containing email subject and body
        """
        subject = "[AI中的数学课程] 作业格式问题通知"

        body = f"""{student_name}同学（学号 {student_id}），

你好！我们在自动批改系统中发现您提交的作业存在以下问题，请您及时检查并修正：

"""
        if categorized_warnings["submission_issues"]:
            body += "\n提交问题：\n"
            for warning in categorized_warnings["submission_issues"]:
                body += f"- {warning}\n"

        has_non_submission_issues = any(
            categorized_warnings[category]
            for category in ["format_issues", "problem_id_issues", "subproblem_issues", "other_issues"]
        )
        if categorized_warnings["submission_issues"] and has_non_submission_issues:
            body += (
                "\n尽管提交存在问题，我们还是尝试对您的作业进行批改。但请注意，在我们批改的过程中，发现了以下问题：\n"
            )

        if categorized_warnings["format_issues"]:
            body += "\n文件格式问题：\n"
            for warning in categorized_warnings["format_issues"]:
                body += f"- {warning}\n"

        if categorized_warnings["problem_id_issues"]:
            body += "\n题目编号问题：\n"
            for warning in categorized_warnings["problem_id_issues"]:
                body += f"- {warning}\n"

        if categorized_warnings["subproblem_issues"]:
            body += "\n子问题格式问题：\n"
            for warning in categorized_warnings["subproblem_issues"]:
                body += f"- {warning}\n"

        if categorized_warnings["other_issues"]:
            body += "\n其他问题：\n"
            for warning in categorized_warnings["other_issues"]:
                body += f"- {warning}\n"

        body += """

这些问题可能导致自动批改系统无法正确识别您的答案。请确保：
1. 章节和问题的格式正确
2. 对于有子问题的题目，正确标注子问题编号
3. 提交的文件使用正确的模板（LaTeX或Markdown）
4. enumerate 环境的范围正确

如有任何疑问，请联系课程助教。

此致，
AI中的数学课助教团队
"""

        return subject, body

    def send_email(self, to_email: str, subject: str, body: str, sender_email: str, sender_password: str) -> bool:
        """
        Send an email using the configured SMTP server.

        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body
            sender_email: Email address to send notifications from
            sender_password: Password for the sender email account

        Returns:
            True if the email was sent successfully, False otherwise
        """
        try:
            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = to_email
            message["Subject"] = subject

            message.attach(MIMEText(body, "plain"))

            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(sender_email, sender_password)
                logger.info(f"Logged in to SMTP server {self.smtp_server}")
                server.send_message(message)

            logger.info(f"Successfully sent email to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def notify_students(
        self,
        warnings_by_student: dict[str, tuple[str, list[str]]],
        sender_email: Optional[str] = None,
        sender_password: Optional[str] = None,
        dry_run: bool = False,
    ) -> set[str]:
        """
        Send notification emails to students based on their warnings.

        Args:
            warnings_by_student: Dictionary mapping student IDs to tuples of (student_name, list of warning messages)
            sender_email: Email address to send notifications from
            sender_password: Password for the sender email account
            dry_run: If True, only print emails instead of sending them

        Returns:
            Set of student IDs that were notified successfully
        """
        notified_students = set()

        for student_id, (student_name, warnings) in warnings_by_student.items():
            if not warnings:
                continue

            categorized_warnings = self.categorize_warnings(warnings)

            # Only send email if there are actual warnings
            if any(categorized_warnings.values()):
                to_email = f"{student_id}@stu.pku.edu.cn"
                subject, body = self.generate_email_content(student_id, student_name, categorized_warnings)

                if dry_run:
                    logger.info(f"Would send email to {to_email} ({student_name})")
                    logger.info(f"Subject: {subject}")
                    logger.info(f"Body: {body}")
                    notified_students.add(student_id)
                else:
                    if sender_email is None or sender_password is None:
                        logger.error("Cannot send emails: sender_email and sender_password are required")
                        break
                    if self.send_email(to_email, subject, body, sender_email, sender_password):
                        notified_students.add(student_id)

        logger.info(f"Successfully notified {len(notified_students)} students")
        return notified_students

    def export_student_list(self, warnings_by_student: dict[str, tuple[str, list[str]]], output_csv_path: str) -> None:
        """
        Export list of students with warnings to a CSV file.

        Args:
            warnings_by_student: Dictionary mapping student IDs to tuples of (student_name, list of warning messages)
            output_csv_path: Path to output CSV file
        """
        try:
            # Create a set of unique student entries
            students = set()
            for student_id, (student_name, warnings) in warnings_by_student.items():
                if warnings:  # Only include students with warnings
                    students.add((student_id, student_name))

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_csv_path) or ".", exist_ok=True)

            # Write to CSV
            with open(output_csv_path, "w", encoding="utf-8", newline="") as csvfile:
                csv_writer = csv.writer(csvfile)
                # Write header
                csv_writer.writerow(["学号", "姓名"])
                # Write data (sorted by student ID)
                for student in sorted(students):
                    csv_writer.writerow(student)

            logger.info(f"Successfully exported {len(students)} students with issues to {output_csv_path}")

        except Exception as e:
            logger.error(f"Failed to export student list: {str(e)}")


def main():
    """Main function to run the email notifier."""
    import argparse

    parser = argparse.ArgumentParser(description="Send email notifications to students based on log warnings")
    parser.add_argument("--hw_id", required=True, help="Homework ID")
    parser.add_argument("--download_log", help="Path to download log file")
    parser.add_argument("--process_log", help="Path to process log file")
    parser.add_argument("--sender_email", help="Sender email address")
    parser.add_argument("--sender_password", help="Sender email password")
    parser.add_argument("--dry_run", action="store_true", help="Print emails instead of sending them")
    parser.add_argument("--log_file", help="Path to log file")
    parser.add_argument(
        "--export_csv",
        nargs="?",
        const="problematic_students.csv",
        help="Export list of problematic students to CSV (default: problematic_students.csv)",
    )

    args = parser.parse_args()

    # Configure logger
    if args.log_file:
        configure_global_logger(log_file=args.log_file)

    # Default log paths if not provided
    hw_id = args.hw_id
    download_log = args.download_log or f"../log/marker_hw{hw_id}_download.log"
    process_log = args.process_log or f"../log/marker_hw{hw_id}_process.log"

    logger.info(f"Starting email notifier for homework {hw_id}")

    # Configure SMTP settings based on sender email
    smtp_server = "mail.pku.edu.cn"  # default
    smtp_port = 465  # default

    if args.sender_email:
        smtp_server, smtp_port = get_email_settings(args.sender_email)
        logger.info(f"Using email settings: server={smtp_server}, port={smtp_port} for {args.sender_email}")

    # Create notifier with configured settings
    notifier = EmailNotifier(smtp_server=smtp_server, smtp_port=smtp_port)

    # Parse logs and get warnings by student
    warnings_by_student = notifier.parse_logs(download_log, process_log)

    # Send email notifications
    if not args.dry_run:
        notifier.notify_students(warnings_by_student, args.sender_email, args.sender_password, dry_run=args.dry_run)
    else:
        notifier.notify_students(warnings_by_student, dry_run=args.dry_run)

    # Export student list to CSV if requested
    if args.export_csv:
        notifier.export_student_list(warnings_by_student, args.export_csv)

    logger.info("Email notification process completed")


if __name__ == "__main__":
    main()
