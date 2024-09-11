import os
from langchain_core.tools import tool
import pandas as pd
from typing import Dict, Optional, Annotated, List
from logger import setup_logger
from load_cfg import WORKING_DIRECTORY

# Set up logger
logger = setup_logger()

# Ensure the working directory exists
if not os.path.exists(WORKING_DIRECTORY):
    os.makedirs(WORKING_DIRECTORY)
    logger.info(f"Created working directory: {WORKING_DIRECTORY}")

@tool
def collect_data(data_path: Annotated[str, "Path to the CSV file"] = './data.csv'):
    """
    Collect data from a CSV file.

    This function attempts to read a CSV file using different encodings.

    Returns:
    pandas.DataFrame: The data read from the CSV file.

    Raises:
    ValueError: If unable to read the file with any of the provided encodings.
    """
    if WORKING_DIRECTORY not in data_path:
            data_path = os.path.join(WORKING_DIRECTORY, data_path)
    else:
        data_path = data_path
    logger.info(f"Attempting to read CSV file: {data_path}")
    encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
    for encoding in encodings:
        try:
            data = pd.read_csv(data_path, encoding=encoding)
            logger.info(f"Successfully read CSV file with encoding: {encoding}")
            return data
        except Exception as e:
            logger.warning(f"Error with encoding {encoding}: {e}")
    logger.error("Unable to read file with provided encodings")
    raise ValueError("Unable to read file with provided encodings")

@tool
def create_document(
    points: Annotated[List[str], "List of points to be included in the document"],
    file_name: Annotated[str, "Name of the file to save the document"]
) -> str:
    """
    Create and save a text document in Markdown format.

    This function takes a list of points and writes them as numbered items in a Markdown file.
    
    Returns:
    str: A message indicating where the outline was saved or an error message.
    """
    try:
        if WORKING_DIRECTORY not in file_name:
            file_path = os.path.join(WORKING_DIRECTORY, file_name)
        else:
            file_path = file_name
        logger.info(f"Creating document: {file_path}")
        with open(file_path, "w") as file:
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
    start: Annotated[Optional[int], "Starting line number to read from"] = None,
    end: Annotated[Optional[int], "Ending line number to read to"] = None
) -> str:
    """
    Read the specified document.

    This function reads a document from the specified file and returns its content.
    Optionally, it can return a specific range of lines.

    Returns:
    str: The content of the document or an error message.
    """
    try:
        if WORKING_DIRECTORY not in file_name:
            file_path = os.path.join(WORKING_DIRECTORY, file_name)
        else:
            file_path = file_name
        logger.info(f"Reading document: {file_path}")
        with open(file_path, "r") as file:
            lines = file.readlines()
        if start is None:
            start = 0
        content = "\n".join(lines[start:end])
        logger.info(f"Document read successfully: {file_path}")
        return content
    except FileNotFoundError:
        logger.error(f"File not found: {file_name}")
        return f"Error: The file {file_name} was not found."
    except Exception as e:
        logger.error(f"Error while reading document: {str(e)}")
        return f"Error while reading document: {str(e)}"

@tool
def write_document(
    content: Annotated[str, "Content to be written to the document"],
    file_name: Annotated[str, "Name of the file to save the document"]
) -> str:
    """
    Create and save a Markdown document.

    This function takes a string of content and writes it to a file.
    """
    try:
        if WORKING_DIRECTORY not in file_name:
            file_path = os.path.join(WORKING_DIRECTORY, file_name)
        else:
            file_path = file_name
        logger.info(f"Writing document: {file_path}")
        with open(file_path, "w") as file:
            file.write(content)
        logger.info(f"Document written successfully: {file_path}")
        return f"Document saved to {file_path}"
    except Exception as e:
        logger.error(f"Error while saving document: {str(e)}")
        return f"Error while saving document: {str(e)}"

@tool
def edit_document(
    file_name: Annotated[str, "Name of the file to edit"],
    inserts: Annotated[Dict[int, str], "Dictionary of line numbers and text to insert"]
) -> str:
    """
    Edit a document by inserting text at specific line numbers.

    This function reads an existing document, inserts new text at specified line numbers,
    and saves the modified document.

    Args:
        file_name (str): Name of the file to edit.
        inserts (Dict[int, str]): Dictionary where keys are line numbers and values are text to insert.

    Returns:
        str: A message indicating the result of the operation.

    Example:
        file_name = "example.txt"
        inserts = {
            1: "This is the first line to insert.",
            3: "This is the third line to insert."
        }
        result = edit_document(file_name=file_name, inserts=inserts)
        print(result)
        # Output: "Document edited and saved to /path/to/example.txt"
    """
    try:
        if WORKING_DIRECTORY not in file_name:
            file_path = os.path.join(WORKING_DIRECTORY, file_name)
        else:
            file_path = file_name
        logger.info(f"Editing document: {file_path}")
        with open(file_path, "r") as file:
            lines = file.readlines()

        sorted_inserts = sorted(inserts.items())

        for line_number, text in sorted_inserts:
            if 1 <= line_number <= len(lines) + 1:
                lines.insert(line_number - 1, text + "\n")
            else:
                logger.error(f"Line number out of range: {line_number}")
                return f"Error: Line number {line_number} is out of range."

        with open(file_path, "w") as file:
            file.writelines(lines)

        logger.info(f"Document edited successfully: {file_path}")
        return f"Document edited and saved to {file_path}"
    except FileNotFoundError:
        logger.error(f"File not found: {file_name}")
        return f"Error: The file {file_name} was not found."
    except Exception as e:
        logger.error(f"Error while editing document: {str(e)}")
        return f"Error while editing document: {str(e)}"

logger.info("Document management tools initialized")