from state import State
from typing import Literal
from langchain_core.messages import AIMessage
import logging
import json

# Set up logger
logger = logging.getLogger(__name__)

# Define types for node routing
NodeType = Literal['Visualization', 'Search', 'Coder', 'Report', 'Process', 'NoteTaker', 'Hypothesis', 'QualityReview']
ProcessNodeType = Literal['Coder', 'Search', 'Visualization', 'Report', 'Process', 'END']

def hypothesis_router(state: State) -> NodeType:
    """
    Route based on the presence of a hypothesis in the state.

    Args:
    state (State): The current state of the system.

    Returns:
    NodeType: 'Hypothesis' if no hypothesis exists, otherwise 'Process'.
    """
    logger.info("Entering hypothesis_router")
    hypothesis = state.get("hypothesis")
    
    if isinstance(hypothesis, AIMessage):
        hypothesis_content = hypothesis.content
        logger.debug("Hypothesis is an AIMessage")
    elif isinstance(hypothesis, str):
        hypothesis_content = hypothesis
        logger.debug("Hypothesis is a string")
    else:
        hypothesis_content = ""
        logger.warning(f"Unexpected hypothesis type: {type(hypothesis)}")
    
    result = "Hypothesis" if not hypothesis_content.strip() else "Process"
    logger.info(f"hypothesis_router decision: {result}")
    return result

def QualityReview_router(state: State) -> NodeType:
    """
    Route based on the quality review outcome and process decision.

    Args:
    state (State): The current state of the system.

    Returns:
    NodeType: The next node to route to based on the quality review and process decision.
    """
    logger.info("Entering QualityReview_router")
    messages = state.get("messages", [])
    last_message = messages[-1] if messages else None
    
    # Check if revision is needed
    if (last_message and 'REVISION' in str(last_message.content)) or state.get("needs_revision", False):
        previous_node = state.get("last_sender", "")
        revision_routes = {
            "Visualization": "Visualization",
            "Search": "Search",
            "Coder": "Coder",
            "Report": "Report"
        }
        result = revision_routes.get(previous_node, "NoteTaker")
        logger.info(f"Revision needed. Routing to: {result}")
        return result
    
    process_decision = state.get("process_decision", "")
    
    if isinstance(process_decision, AIMessage):
        process_decision = process_decision.content
        logger.debug("Process decision is an AIMessage")
    
    if not process_decision or process_decision == "Error":
        logger.info("No valid process decision. Routing to NoteTaker")
        return "NoteTaker"
    
    valid_decisions = {"Visualization", "Search", "Coder", "Report", "QualityReview"}
    if process_decision in valid_decisions:
        logger.info(f"Valid process decision: {process_decision}")
        return process_decision
    
    logger.warning(f"Unexpected QualityReview_router decision: {process_decision}. Defaulting to 'NoteTaker'.")
    return "NoteTaker"

def process_router(state: State) -> ProcessNodeType:
    """
    Route based on the process decision in the state.

    Args:
    state (State): The current state of the system.

    Returns:
    ProcessNodeType: The next process node to route to based on the process decision.
    """
    logger.info("Entering process_router")
    process_decision = state.get("process_decision", "")
    
    # Handle AIMessage object
    if isinstance(process_decision, AIMessage):
        logger.debug("Process decision is an AIMessage")
        try:
            # Attempt to parse JSON in content
            decision_dict = json.loads(process_decision.content.replace("'", '"'))
            process_decision = decision_dict.get('next', '')
            logger.debug(f"Parsed process decision from JSON: {process_decision}")
        except json.JSONDecodeError:
            # If JSON parsing fails, use content directly
            process_decision = process_decision.content
            logger.warning("Failed to parse process decision as JSON. Using content directly.")
    elif isinstance(process_decision, dict):
        process_decision = process_decision.get('next', '')
        logger.debug(f"Process decision is a dictionary. Using 'next' value: {process_decision}")
    elif not isinstance(process_decision, str):
        process_decision = str(process_decision)
        logger.warning(f"Unexpected process decision type. Converting to string: {process_decision}")
    
    # Define valid decisions
    valid_decisions = {"Coder", "Search", "Visualization", "Report"}
    
    if process_decision in valid_decisions:
        logger.info(f"Valid process decision: {process_decision}")
        return process_decision
    
    if process_decision == "FINISH":
        logger.info("Process decision is FINISH. Ending process.")
        return "END"
    
    # If process_decision is empty or not a valid decision, return "Process"
    if not process_decision or process_decision not in valid_decisions:
        logger.warning(f"Invalid or empty process decision: {process_decision}. Defaulting to 'Process'.")
        return "Process"
    
    # Default to "Process"
    logger.info("Defaulting to 'Process'")
    return "Process"

logger.info("Router module initialized")