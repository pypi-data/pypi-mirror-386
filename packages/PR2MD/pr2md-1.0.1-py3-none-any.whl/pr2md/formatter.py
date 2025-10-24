"""Markdown formatter for GitHub PR data."""

import logging
from collections import defaultdict

from pr2md.models import Comment, PullRequest, Review, ReviewComment

logger = logging.getLogger(__name__)


class MarkdownFormatter:
    """Format GitHub PR data as Markdown."""

    @staticmethod
    def format_pr(
        pull_request: PullRequest,
        comments: list[Comment],
        reviews: list[Review],
        review_comments: list[ReviewComment],
        diff: str,
    ) -> str:
        """
        Format all PR data as Markdown.

        Args:
            pull_request: Pull request object
            comments: List of comments
            reviews: List of reviews
            review_comments: List of review comments
            diff: Diff string

        Returns:
            Formatted Markdown string
        """
        logger.info("Formatting PR data as Markdown")
        sections = [
            MarkdownFormatter._format_header(pull_request),
            MarkdownFormatter._format_description(pull_request),
            MarkdownFormatter._format_changes_summary(pull_request),
            MarkdownFormatter._format_diff(diff),
            MarkdownFormatter._format_conversation(comments),
            MarkdownFormatter._format_reviews(reviews),
            MarkdownFormatter._format_review_comments(review_comments),
        ]

        result = "\n\n".join(sections)
        logger.info("Formatted Markdown (%d characters)", len(result))
        return result

    @staticmethod
    def _format_header(pull_request: PullRequest) -> str:
        """Format PR header section."""
        status = pull_request.state.upper()
        if pull_request.merged_at:
            status = "MERGED"

        labels_str = ""
        if pull_request.labels:
            label_names = ", ".join(
                [f"`{label.name}`" for label in pull_request.labels]
            )
            labels_str = f"\n**Labels:** {label_names}"

        closed_str = ""
        if pull_request.closed_at:
            closed_time = pull_request.closed_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            closed_str = f"\n**Closed:** {closed_time}"

        merged_str = ""
        if pull_request.merged_at:
            merged_time = pull_request.merged_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            merged_str = f"\n**Merged:** {merged_time}"

        created_time = pull_request.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        updated_time = pull_request.updated_at.strftime("%Y-%m-%d %H:%M:%S UTC")

        return f"""# {pull_request.title}

**PR Number:** #{pull_request.number}
**Status:** {status}
**Author:** [{pull_request.user.login}]({pull_request.user.html_url})
**Created:** {created_time}
**Updated:** {updated_time}{closed_str}{merged_str}
**URL:** {pull_request.html_url}
**Base:** `{pull_request.base_ref}` (`{pull_request.base_sha[:7]}`)
**Head:** `{pull_request.head_ref}` (`{pull_request.head_sha[:7]}`){labels_str}"""

    @staticmethod
    def _format_description(pull_request: PullRequest) -> str:
        """Format PR description section."""
        if not pull_request.body:
            return "## Description\n\n*No description provided.*"
        return f"## Description\n\n{pull_request.body}"

    @staticmethod
    def _format_changes_summary(pull_request: PullRequest) -> str:
        """Format changes summary section."""
        return f"""## Changes Summary

- **Files changed:** {pull_request.changed_files}
- **Additions:** +{pull_request.additions}
- **Deletions:** -{pull_request.deletions}"""

    @staticmethod
    def _format_diff(diff: str) -> str:
        """Format diff section."""
        if not diff:
            return "## Code Diff\n\n*No diff available.*"

        return f"""## Code Diff

```diff
{diff}
```"""

    @staticmethod
    def _format_conversation(comments: list[Comment]) -> str:
        """Format conversation thread section."""
        if not comments:
            return "## Conversation Thread\n\n*No comments in the conversation thread.*"

        # Sort by creation time
        sorted_comments = sorted(comments, key=lambda c: c.created_at)

        formatted_comments = []
        for comment in sorted_comments:
            comment_time = comment.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            # pylint: disable=line-too-long
            formatted_comment = f"""### [{comment.user.login}]({comment.user.html_url}) commented on {comment_time}

{comment.body}

*[View on GitHub]({comment.html_url})*"""
            # pylint: enable=line-too-long
            formatted_comments.append(formatted_comment)

        return "## Conversation Thread\n\n" + "\n\n---\n\n".join(formatted_comments)

    @staticmethod
    def _format_reviews(reviews: list[Review]) -> str:
        """Format reviews section."""
        if not reviews:
            return "## Reviews\n\n*No reviews submitted.*"

        # Sort by submission time
        sorted_reviews = sorted(
            reviews,
            key=lambda r: r.submitted_at if r.submitted_at else r.user.login,
        )

        formatted_reviews = []
        for review in sorted_reviews:
            submitted_str = (
                review.submitted_at.strftime("%Y-%m-%d %H:%M:%S UTC")
                if review.submitted_at
                else "Unknown date"
            )

            state_emoji: dict[str, str] = {
                "APPROVED": "✅",
                "CHANGES_REQUESTED": "🔴",
                "COMMENTED": "💬",
                "DISMISSED": "🚫",
                "PENDING": "⏳",
            }
            emoji = state_emoji.get(review.state, "")

            body_str = review.body if review.body else "*No comment provided.*"

            # pylint: disable=line-too-long
            formatted_review = f"""### {emoji} [{review.user.login}]({review.user.html_url}) {review.state.replace("_", " ")} on {submitted_str}

{body_str}

*[View on GitHub]({review.html_url})*"""
            # pylint: enable=line-too-long
            formatted_reviews.append(formatted_review)

        return "## Reviews\n\n" + "\n\n---\n\n".join(formatted_reviews)

    @staticmethod
    def _format_review_comments(review_comments: list[ReviewComment]) -> str:
        """Format review comments section."""
        if not review_comments:
            return "## Review Comments (Code Comments)\n\n*No review comments on code.*"

        # Group by file path
        comments_by_file: dict[str, list[ReviewComment]] = defaultdict(list)
        for comment in review_comments:
            comments_by_file[comment.path].append(comment)

        # Sort files alphabetically
        sorted_files = sorted(comments_by_file.keys())

        formatted_files = []
        for file_path in sorted_files:
            file_comments = sorted(
                comments_by_file[file_path], key=lambda c: c.created_at
            )

            formatted_comments = []
            for comment in file_comments:
                # Check if this is a reply
                reply_str = ""
                if comment.in_reply_to_id:
                    reply_str = f" *(in reply to comment #{comment.in_reply_to_id})*"

                comment_time = comment.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
                # pylint: disable=line-too-long
                formatted_comment = f"""#### [{comment.user.login}]({comment.user.html_url}) commented on {comment_time}{reply_str}

**Code context:**
```diff
{comment.diff_hunk}
```

**Comment:**
{comment.body}

*[View on GitHub]({comment.html_url})*"""
                # pylint: enable=line-too-long
                formatted_comments.append(formatted_comment)

            file_section = f"""### File: `{file_path}`

{chr(10).join(formatted_comments)}"""
            formatted_files.append(file_section)

        return "## Review Comments (Code Comments)\n\n" + "\n\n---\n\n".join(
            formatted_files
        )
