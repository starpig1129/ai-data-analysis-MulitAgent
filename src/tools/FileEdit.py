import os
from typing import Annotated

import pandas as pd
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from ..config import WORKING_DIRECTORY
from ..logger import setup_logger

# Set up logger
logger = setup_logger()

# Ensure the working directory exists
if not os.path.exists(WORKING_DIRECTORY):
    os.makedirs(WORKING_DIRECTORY)
    logger.info(f"Created working directory: {WORKING_DIRECTORY}")


def normalize_path(file_path: str) -> str:
    """
    Normalize file path for cross-platform compatibility.

    Args:
    file_path (str): The file path to normalize

    Returns:
    str: Normalized file path
    """
    if WORKING_DIRECTORY not in file_path:
        file_path = os.path.join(WORKING_DIRECTORY, file_path)
    return os.path.normpath(file_path)


@tool
def collect_data(
    data_path: Annotated[str, "Path to the CSV file"] = "./data.csv",
    nrows: Annotated[int | None, "Number of rows to read"] = None,
    usecols: Annotated[list[str] | None, "List of column names to read"] = None,
    skiprows: Annotated[int | None, "Number of rows to skip at the beginning"] = None,
) -> Annotated[pd.DataFrame, "The collected data from the CSV file"]:
    """
    Collect data from a CSV file with selective reading options.
    """
    data_path = normalize_path(data_path)
    logger.info(f"Attempting to read CSV file: {data_path}")
    encodings = ["utf-8", "latin1", "iso-8859-1", "cp1252"]
    for encoding in encodings:
        try:
            data = pd.read_csv(
                data_path,
                encoding=encoding,
                nrows=nrows,
                usecols=usecols,
                skiprows=skiprows,
            )
            logger.info(f"Successfully read CSV file with encoding: {encoding}")
            return data
        except Exception as e:
            logger.warning(f"Error with encoding {encoding}: {e}")
    logger.error("Unable to read file with provided encodings")
    raise ValueError("Unable to read file with provided encodings")


@tool
def create_document(
    points: Annotated[list[str], "List of points to be included in the document"],
    file_name: Annotated[str, "Name of the file to save the document"],
) -> Annotated[str, "Message indicating where the document was saved"]:
    """
    Create and save a text document in Markdown format.

    This function takes a list of points and writes them as numbered items in a Markdown file.

    """
    try:
        file_path = normalize_path(file_name)
        logger.info(f"Creating document: {file_path}")
        with open(file_path, "w", encoding="utf-8") as file:
            for i, point in enumerate(points):
                file.write(f"{i + 1}. {point}\n")
        logger.info(f"Document created successfully: {file_path}")
        return f"Outline saved to {file_path}"
    except Exception as e:
        logger.error(f"Error while saving outline: {str(e)}")
        return f"Error while saving outline: {str(e)}"


@tool
def read_document(
    file_name: Annotated[str, "Name of the file to read"],
    start: Annotated[int, "Starting line number (use 0 for beginning)"] = 0,
    end: Annotated[int, "Ending line number (use -1 for end of file)"] = -1,
) -> Annotated[str, "Content of the document"]:
    """
    Read the specified document with security validation.

    This function reads a document from the specified file and returns its content.
    Security features:
    - Path validation (blocked paths check)
    - File size validation
    - Line count limiting

    Args:
        file_name: Name of the file to read.
        start: Starting line number (0-indexed, default: 0).
        end: Ending line number (-1 for end of file, default: -1).

    Returns:
        Content of the document or error message.
    """
    from .tool_config import TOOL_CONFIG
    from .validators import PathValidator

    try:
        file_path = normalize_path(file_name)

        # === VALIDATION ===
        try:
            PathValidator.validate_read(file_path)
        except (PermissionError, ValueError) as e:
            logger.warning(f"Read validation failed for {file_path}: {e}")
            return f"Error: {e}"

        with open(file_path, encoding="utf-8") as file:
            lines = file.readlines()

        # Apply line limit
        max_lines = TOOL_CONFIG.file_ops.max_read_lines
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            truncated_notice = f"\n\n... [TRUNCATED: showing first {max_lines} lines]"
        else:
            truncated_notice = ""

        # Handle special values
        if start == 0 and end == -1:
            content = "".join(lines)
        elif end == -1:
            content = "".join(lines[start:])
        else:
            content = "".join(lines[start:end])

        return content + truncated_notice
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def write_document(
    content: Annotated[str, "Content to be written to the document"],
    file_name: Annotated[str, "Name of the file to save the document"],
) -> Annotated[str, "Message indicating where the document was saved"]:
    """
    Create and save a Markdown document with validation.

    This function takes a string of content and writes it to a file.
    Security features:
    - Path validation (blocked paths check)
    - Content size validation
    - Content quality warnings (TODO/FIXME detection)

    Args:
        content: Content to write to the file.
        file_name: Name of the file to save.

    Returns:
        Success message or error.
    """
    from .validators import ContentValidator, PathValidator

    try:
        file_path = normalize_path(file_name)

        # === PATH VALIDATION ===
        try:
            PathValidator.validate_write(file_path)
        except PermissionError as e:
            logger.warning(f"Write path validation failed: {e}")
            return f"Error: {e}"

        # === CONTENT VALIDATION ===
        is_valid, message = ContentValidator.validate_and_log(content, file_path)
        if not is_valid:
            return f"Error: {message}"

        logger.info(f"Writing document: {file_path}")
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)
        logger.info(f"Document written successfully: {file_path}")

        result = f"Document saved to {file_path}"
        if message:  # Warnings
            result += f" ({message})"
        return result
    except Exception as e:
        logger.error(f"Error while saving document: {str(e)}")
        return f"Error while saving document: {str(e)}"


class LineInsert(BaseModel):
    line_number: int = Field(description="Line number to insert at")
    text: str = Field(description="Text to insert")


@tool
def edit_document(
    file_name: Annotated[str, "Name of the file to edit"],
    inserts: Annotated[list[LineInsert], "List of line insertions"],
) -> Annotated[str, "Message indicating where the document was saved"]:
    """Edit a document by inserting text at specific line numbers."""
    try:
        file_path = normalize_path(file_name)
        with open(file_path, encoding="utf-8") as file:
            lines = file.readlines()

        inserts_dict = {insert.line_number: insert.text for insert in inserts}
        sorted_inserts = sorted(inserts_dict.items())

        for line_number, text in sorted_inserts:
            if 1 <= line_number <= len(lines) + 1:
                lines.insert(line_number - 1, text + "\n")

        with open(file_path, "w", encoding="utf-8") as file:
            file.writelines(lines)

        return f"Document edited and saved to {file_path}"
    except Exception as e:
        return f"Error while editing document: {str(e)}"


logger.info("Document management tools initialized")
