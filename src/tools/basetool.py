import os
import platform
import subprocess
from typing import Annotated

from langchain_core.tools import tool

from ..config import CONDA_ENV, WORKING_DIRECTORY
from ..logger import setup_logger

# Initialize logger
logger = setup_logger()

# Ensure the storage directory exists
if not os.path.exists(WORKING_DIRECTORY):
    os.makedirs(WORKING_DIRECTORY)
    logger.info(f"Created storage directory: {WORKING_DIRECTORY}")


def get_platform_specific_command(command: str) -> tuple:
    """
    Get platform-specific command execution details using conda run.
    Returns a tuple of (shell_command, shell_type, executable)
    """
    conda_command = f"conda run -n {CONDA_ENV} {command}"

    system = platform.system().lower()
    if system == "windows":
        return (conda_command, True, None)
    else:
        return (conda_command, True, "/bin/bash")


@tool
def execute_code(
    input_code: Annotated[str, "The Python code to execute."],
    codefile_name: Annotated[
        str, "The Python code file name or full path."
    ] = "code.py",
    timeout: Annotated[
        int | None, "Execution timeout in seconds. None = no limit."
    ] = None,
    memory_mb: Annotated[
        int | None, "Memory limit in MB (Linux only). None = no limit."
    ] = None,
    progress_timeout: Annotated[
        int | None, "Timeout only if no output for N seconds. Good for ML/DL."
    ] = None,
) -> Annotated[dict, "Execution result including output and file path"]:
    """
    Execute Python code in a specified conda environment and return the result.

    This function takes Python code as input, writes it to a file, executes it in the specified
    conda environment, and returns the output or any errors encountered during execution.

    Security features:
    - Code is scanned for dangerous patterns before execution
    - Optional timeout and memory limits
    - Output is truncated if too large

    Args:
        input_code: The Python code to execute.
        codefile_name: File name to save the code (default: code.py).
        timeout: Fixed timeout in seconds. None = no limit.
        memory_mb: Memory limit in MB (Linux only). None = no limit.
        progress_timeout: Timeout only if no stdout for N seconds (for long-running ML/DL).

    Returns:
        Dictionary with result status, output/error, and file path.
    """
    from .security import ResourceLimiter, SecurityScanner
    from .tool_config import TOOL_CONFIG

    code_file_path = None
    try:
        # === SECURITY SCAN ===
        if TOOL_CONFIG.enable_security_scan:
            scan_result = SecurityScanner.scan_code(input_code)
            if not scan_result.is_safe:
                logger.warning(f"Security scan blocked code: {scan_result.violations}")
                return {
                    "result": "Security violation",
                    "error": f"Code blocked: {'; '.join(scan_result.violations)}",
                    "file_path": None,
                }
            if scan_result.warnings:
                logger.info(f"Security scan warnings: {scan_result.warnings}")

        # Ensure WORKING_DIRECTORY exists
        os.makedirs(WORKING_DIRECTORY, exist_ok=True)

        # Handle codefile_name, ensuring it's a valid path
        if os.path.isabs(codefile_name):
            code_file_path = codefile_name
        else:
            if WORKING_DIRECTORY not in codefile_name:
                code_file_path = os.path.join(WORKING_DIRECTORY, codefile_name)
            else:
                code_file_path = codefile_name

        # Normalize the path for the current platform
        code_file_path = os.path.normpath(code_file_path)

        logger.info(f"Code will be written to file: {code_file_path}")

        # Write the code to the file with UTF-8 encoding
        with open(code_file_path, "w", encoding="utf-8") as code_file:
            code_file.write(input_code)

        logger.info(f"Code has been written to file: {code_file_path}")

        # Get platform-specific command
        python_cmd = f"python {codefile_name}"
        full_command, shell, executable = get_platform_specific_command(python_cmd)

        logger.info(f"Executing command: {full_command}")

        # === EXECUTE WITH RESOURCE LIMITS ===
        limiter = ResourceLimiter(
            timeout=timeout,
            memory_mb=memory_mb,
            progress_timeout=progress_timeout,
        )

        try:
            result = limiter.execute(
                command=full_command,
                cwd=WORKING_DIRECTORY,
                shell=shell,
                executable=executable,
            )
        except TimeoutError as e:
            logger.error(f"Execution timeout: {e}")
            return {"result": "Timeout", "error": str(e), "file_path": code_file_path}

        # Capture standard output and error output
        output = result.stdout
        error_output = result.stderr

        if result.returncode == 0:
            logger.info("Code executed successfully")
            return {
                "result": "Code executed successfully",
                "output": output
                + "\n\nIf you have completed all tasks, respond with FINAL ANSWER.",
                "file_path": code_file_path,
            }
        else:
            logger.error(f"Code execution failed: {error_output}")
            return {
                "result": "Failed to execute",
                "error": error_output,
                "file_path": code_file_path,
            }
    except Exception as e:
        logger.exception("An error occurred while executing code")
        return {
            "result": "Error occurred",
            "error": str(e),
            "file_path": code_file_path if "code_file_path" in locals() else "Unknown",
        }


@tool
def execute_command(
    command: Annotated[str, "Command to be executed."],
) -> Annotated[str, "Output of the command."]:
    """
    Execute a command in a specified Conda environment and return its output.

    This function activates a Conda environment, executes the given command,
    and returns the output or any errors encountered during execution.
    Please use pip to install the package.

    """
    try:
        # Get platform-specific command
        full_command, shell, executable = get_platform_specific_command(command)

        logger.info(f"Executing command: {command}")

        # Execute the command and capture the output
        result = subprocess.run(
            full_command,
            shell=shell,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            executable=executable,
            cwd=WORKING_DIRECTORY,
        )
        logger.info("Command executed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Error executing command: {e.stderr}")
        return f"Error: {e.stderr}"


logger.info("Module initialized successfully")


@tool
def list_directory(
    directory: Annotated[str, "Path to the directory to list."],
) -> Annotated[str, "Contents of the directory"]:
    """List the contents of the specified directory."""
    try:
        if not directory:
            directory = WORKING_DIRECTORY
        logger.info(f"Listing contents of directory: {directory}")
        contents = os.listdir(directory)
        return "Directory contents:\n" + "\n".join(contents)
    except Exception as e:
        return f"Error: {str(e)}"
