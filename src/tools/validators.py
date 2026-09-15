"""Path and content validators for file operations.

This module provides:
- PathValidator: Validate file paths for security
- ContentValidator: Validate content before writing
"""

import os
import re
from pathlib import Path

from ..logger import setup_logger
from .tool_config import TOOL_CONFIG

logger = setup_logger()


class PathValidator:
    """Validate file paths for security.

    Checks:
    - Path is not in blocked directories
    - File extension is in allowed list
    - File size is within limits
    """

    @classmethod
    def check_path(cls, file_path: str) -> None:
        """Ensure path is not in blocked directories.

        Args:
            file_path: Path to validate.

        Raises:
            PermissionError: If path is in a blocked directory.
        """
        try:
            resolved = Path(file_path).resolve()
        except (OSError, ValueError) as e:
            raise PermissionError(f"Invalid path: {file_path}") from e

        for blocked in TOOL_CONFIG.file_ops.blocked_paths:
            try:
                blocked_resolved = Path(os.path.expanduser(blocked)).resolve()
            except (OSError, ValueError):
                # Skip invalid blocked paths
                continue

            if str(resolved).startswith(str(blocked_resolved)):
                raise PermissionError(
                    f"Access denied: {file_path} is in blocked path '{blocked}'"
                )

    @classmethod
    def check_extension(cls, file_path: str) -> None:
        """Ensure file extension is allowed.

        Args:
            file_path: Path to validate.

        Raises:
            PermissionError: If extension is not in allowed list.
        """
        ext = Path(file_path).suffix.lower()
        allowed = TOOL_CONFIG.file_ops.allowed_extensions

        # Allow files without extension
        if not ext:
            return

        if ext not in allowed:
            raise PermissionError(
                f"File type '{ext}' not allowed. Allowed: {', '.join(allowed)}"
            )

    @classmethod
    def check_file_size(cls, file_path: str) -> None:
        """Ensure file is within size limit for reading.

        Args:
            file_path: Path to check.

        Raises:
            ValueError: If file exceeds max_read_bytes.
        """
        if not os.path.exists(file_path):
            return

        size = os.path.getsize(file_path)
        max_size = TOOL_CONFIG.file_ops.max_read_bytes

        if size > max_size:
            raise ValueError(
                f"File too large: {size:,} bytes (max: {max_size:,} bytes = {max_size // 1024 // 1024}MB)"
            )

    @classmethod
    def validate_read(cls, file_path: str) -> None:
        """Run all read validations.

        Args:
            file_path: Path to validate.

        Raises:
            PermissionError: If path or extension is not allowed.
            ValueError: If file is too large.
        """
        cls.check_path(file_path)
        cls.check_extension(file_path)
        cls.check_file_size(file_path)

    @classmethod
    def validate_write(cls, file_path: str) -> None:
        """Run all write validations for path.

        Args:
            file_path: Path to validate.

        Raises:
            PermissionError: If path or extension is not allowed.
        """
        cls.check_path(file_path)
        cls.check_extension(file_path)


class ContentValidator:
    """Validate content before writing.

    Checks for:
    - Content size limits
    - Incomplete content markers (TODO, FIXME, etc.)
    - Potential sensitive data (API keys, passwords)
    """

    # Minimum content length to avoid "very short" warning
    MIN_CONTENT_LENGTH = 10

    # Markers that suggest incomplete content
    INCOMPLETE_MARKERS = ["TODO", "FIXME", "XXX", "TBD", "HACK", "（待補）", "..."]

    # Patterns for detecting sensitive data
    SENSITIVE_PATTERNS = [
        (r"['\"]sk-[a-zA-Z0-9]{32,}['\"]", "OpenAI API key"),
        (r"['\"]AKIA[A-Z0-9]{16}['\"]", "AWS access key"),
        (r"password\s*=\s*['\"][^'\"]+['\"]", "Hardcoded password"),
        (r"['\"][a-f0-9]{32}['\"]", "Potential API key/hash"),
    ]

    @classmethod
    def validate_content(
        cls,
        content: str,
        file_path: str,
    ) -> tuple[bool, list[str]]:
        """Validate content before writing.

        Args:
            content: Content to validate.
            file_path: Target file path (for context).

        Returns:
            Tuple of (is_valid, warnings).
            is_valid is False only if content exceeds size limits.
            warnings are non-blocking issues found.
        """
        warnings = []

        # Check size limit
        content_bytes = len(content.encode("utf-8"))
        max_bytes = TOOL_CONFIG.file_ops.max_write_bytes

        if content_bytes > max_bytes:
            return False, [
                f"Content too large: {content_bytes:,} bytes (max: {max_bytes:,} bytes)"
            ]

        # Skip further validation if disabled
        if not TOOL_CONFIG.enable_write_validation:
            return True, []

        # Check for incomplete markers
        for marker in cls.INCOMPLETE_MARKERS:
            if marker in content:
                warnings.append(f"Found incomplete marker: '{marker}'")
                break  # Only report first marker

        # Check for sensitive data patterns
        for pattern, description in cls.SENSITIVE_PATTERNS:
            if re.search(pattern, content):
                warnings.append(
                    f"Potential {description} detected - review before commit"
                )
                break  # Only report first match

        # Check for empty or nearly empty content
        stripped = content.strip()
        if not stripped:
            warnings.append("Content is empty")
        elif len(stripped) < cls.MIN_CONTENT_LENGTH:
            warnings.append("Content is very short - verify completeness")

        return True, warnings

    @classmethod
    def validate_and_log(
        cls,
        content: str,
        file_path: str,
    ) -> tuple[bool, str]:
        """Validate content and return formatted result.

        Args:
            content: Content to validate.
            file_path: Target file path.

        Returns:
            Tuple of (is_valid, message).
        """
        is_valid, warnings = cls.validate_content(content, file_path)

        if not is_valid:
            error_msg = f"Validation failed: {warnings[0]}"
            logger.error(error_msg)
            return False, error_msg

        if warnings:
            warning_msg = f"Warnings: {'; '.join(warnings)}"
            logger.warning(f"Write validation for {file_path}: {warning_msg}")
            return True, warning_msg

        return True, ""
