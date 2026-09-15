import asyncio
import logging
import os
import sys
import threading
import warnings

# 1. Suppress the USER_AGENT warning
os.environ["USER_AGENT"] = "MultiAgentDataAnalysis/1.0"


# 2. Setup a stream interceptor to filter out unwanted prints from libraries/subprocesses
class OutputFilter:
    def __init__(self, stream, blacklist):
        self.stream = stream
        self.blacklist = blacklist

    def write(self, data):
        if not any(term in data for term in self.blacklist):
            self.stream.write(data)

    def flush(self):
        self.stream.flush()

    def __getattr__(self, name):
        return getattr(self.stream, name)


# Apply filter to stderr where most MCP server noise lives
sys.stderr = OutputFilter(
    sys.stderr,
    [
        "Secure MCP Filesystem Server",
        "Client does not support MCP Roots",
        "USER_AGENT environment variable not set",
        "FutureWarning",
    ],
)

# Configured by setup_logger() in main(). The src modules are imported inside
# main() so the stderr filter above is installed before any of them load.
logger = logging.getLogger("src")


def run_mcp_loop(loop: asyncio.AbstractEventLoop) -> None:
    """Runs an asyncio event loop forever in the current (background) thread.

    Installs ``loop`` as the current thread's event loop and blocks running
    it until it is stopped, keeping persistent MCP client connections alive
    for the lifetime of the process.

    Args:
        loop: The event loop to install and run.
    """
    asyncio.set_event_loop(loop)
    try:
        loop.run_forever()
    except Exception as e:
        logger.error(f"MCP background loop error: {e}")


def main() -> None:
    """Sets up logging and a background MCP event loop, then runs the multi-agent system on a sample data-analysis prompt."""
    from src.core.mcp_manager import get_mcp_manager
    from src.logger import setup_logger

    # Initialize the robust logger first thing
    setup_logger()
    # Silence library warnings (e.g. deprecation/future warnings raised via the
    # warnings module) so they don't clutter the console; the stderr filter
    # above only catches noise libraries print directly to stderr.
    warnings.filterwarnings("ignore")

    from src.system import MultiAgentSystem

    # Create and start a background event loop for persistent MCP connections
    mcp_loop = asyncio.new_event_loop()
    mcp_thread = threading.Thread(target=run_mcp_loop, args=(mcp_loop,), daemon=True)
    mcp_thread.start()

    # Register the loop with the MCP manager
    manager = get_mcp_manager()
    manager._main_loop = mcp_loop

    try:
        system = MultiAgentSystem()

        # Example usage
        user_input = """
        datapath:OnlineSalesData.csv
        Use machine learning to perform data analysis and write complete graphical reports
        """
        system.run(user_input)
    finally:
        # Cleanup
        if mcp_loop.is_running():
            mcp_loop.call_soon_threadsafe(mcp_loop.stop)
        mcp_thread.join(timeout=2)


if __name__ == "__main__":
    main()
