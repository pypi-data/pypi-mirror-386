"""Command-line interface for GitHub PR extractor."""

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import Optional

from pr2md.formatter import MarkdownFormatter
from pr2md.pr_extractor import GitHubAPIError, GitHubPRExtractor


def setup_logging(verbose: bool = False) -> None:
    """
    Set up logging configuration.

    Args:
        verbose: Enable verbose logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """
    Parse GitHub PR URL to extract owner, repo, and PR number.

    Args:
        url: GitHub PR URL

    Returns:
        Tuple of (owner, repo, pr_number)

    Raises:
        ValueError: If URL is invalid
    """
    pattern = r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.match(pattern, url)
    if not match:
        raise ValueError(
            f"Invalid GitHub PR URL: {url}\n"
            "Expected format: https://github.com/owner/repo/pull/123"
        )
    owner, repo, pr_number_str = match.groups()
    return str(owner), str(repo), int(pr_number_str)


def create_parser() -> argparse.ArgumentParser:
    """
    Create command-line argument parser.

    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description="Extract GitHub Pull Request details to Markdown format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s https://github.com/owner/repo/pull/123
  %(prog)s owner repo 123
  %(prog)s https://github.com/owner/repo/pull/123 -o output.md
  %(prog)s owner repo 123 --output pr-details.md --verbose
        """,
    )

    parser.add_argument(
        "pr_identifier",
        nargs="+",
        help=(
            "GitHub PR URL (https://github.com/owner/repo/pull/123) "
            "or owner repo pr_number"
        ),
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file path (default: stdout)",
        default=None,
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    return parser


def parse_arguments(
    parser: argparse.ArgumentParser,
) -> tuple[str, str, int, Optional[str], bool]:
    """
    Parse command-line arguments and extract PR details.

    Args:
        parser: Argument parser

    Returns:
        Tuple of (owner, repo, pr_number, output_path, verbose)
    """
    args = parser.parse_args()
    logger = logging.getLogger(__name__)

    # Initialize variables to satisfy pylint - they will be assigned in all code paths
    owner: str = ""
    repo: str = ""
    pr_number: int = 0

    # Parse PR identifier
    try:
        pr_args: list[str] = list(args.pr_identifier)
        if len(pr_args) == 1:
            # URL format
            owner, repo, pr_number = parse_pr_url(str(pr_args[0]))
        elif len(pr_args) == 3:
            # owner repo pr_number format
            owner = str(pr_args[0])
            repo = str(pr_args[1])
            pr_number = int(pr_args[2])
        else:
            parser.error(
                "Invalid arguments. Provide either a PR URL or owner repo pr_number"
            )
    except (ValueError, IndexError) as err:
        logger.error("Error parsing PR identifier: %s", err)
        sys.exit(1)

    output_path: Optional[str] = str(args.output) if args.output else None
    verbose: bool = bool(args.verbose)

    return owner, repo, pr_number, output_path, verbose


def extract_pr_data(
    owner: str, repo: str, pr_number: int, verbose: bool
) -> tuple[str, bool]:
    """
    Extract PR data and format as Markdown.

    Args:
        owner: Repository owner
        repo: Repository name
        pr_number: PR number
        verbose: Enable verbose logging

    Returns:
        Tuple of (markdown, success)
    """
    logger = logging.getLogger(__name__)

    # Extract PR data
    try:
        extractor = GitHubPRExtractor(owner, repo, pr_number)
        pull_request, comments, reviews, review_comments, diff = extractor.extract_all()
    except GitHubAPIError as err:
        logger.error("GitHub API error: %s", err)
        return "", False
    except Exception as err:  # pylint: disable=broad-exception-caught
        logger.error("Unexpected error: %s", err)
        if verbose:
            logger.exception("Full traceback:")
        return "", False

    # Format as Markdown
    try:
        markdown = MarkdownFormatter.format_pr(
            pull_request, comments, reviews, review_comments, diff
        )
        return markdown, True
    except Exception as err:  # pylint: disable=broad-exception-caught
        logger.error("Error formatting data: %s", err)
        if verbose:
            logger.exception("Full traceback:")
        return "", False


def write_output(markdown: str, output_path: Optional[str], verbose: bool) -> bool:
    """
    Write markdown output to file or stdout.

    Args:
        markdown: Formatted markdown string
        output_path: Optional output file path
        verbose: Enable verbose logging

    Returns:
        True if successful, False otherwise
    """
    logger = logging.getLogger(__name__)

    try:
        if output_path:
            Path(output_path).write_text(markdown, encoding="utf-8")
            logger.info("Output written to %s", output_path)
        else:
            print(markdown)  # noqa: T201
        return True
    except Exception as err:  # pylint: disable=broad-exception-caught
        logger.error("Error writing output: %s", err)
        if verbose:
            logger.exception("Full traceback:")
        return False


def main() -> None:
    """Main entry point for the CLI."""
    parser = create_parser()
    owner, repo, pr_number, output_path, verbose = parse_arguments(parser)

    setup_logging(verbose)
    logger = logging.getLogger(__name__)

    logger.info("Extracting PR %s/%s #%d", owner, repo, pr_number)

    markdown, success = extract_pr_data(owner, repo, pr_number, verbose)
    if not success:
        sys.exit(1)

    if not write_output(markdown, output_path, verbose):
        sys.exit(1)

    logger.info("Extraction completed successfully")


if __name__ == "__main__":
    main()
