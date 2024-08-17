from typing import Any, Dict
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from openai import InternalServerError
from state import State
import logging
import json
import re

# Set up logger
logger = logging.getLogger(__name__)

def agent_node(state: State, agent: Any, name: str) -> dict[str, Any]:
    """
    Process an agent's action and update the state accordingly.
    """
    logger.info(f"Processing agent: {name}")
    try:
        result = agent.invoke(state)
        logger.debug(f"Agent {name} result: {result}")
        
        output = result["output"] if isinstance(result, dict) and "output" in result else str(result)
        
        ai_message = AIMessage(content=output, name=name)
        state["messages"].append(ai_message)
        state["sender"] = name
        
        if name == "hypothesis_agent" and not state["hypothesis"]:
            state["hypothesis"] = ai_message
            logger.info("Hypothesis updated")
        elif name == "process_agent":
            state["process_decision"] = ai_message
            logger.info("Process decision updated")
        elif name == "visualization_agent":
            state["visualization_state"] = ai_message
            logger.info("Visualization state updated")
        elif name == "searcher_agent":
            state["searcher_state"] = ai_message
            logger.info("Searcher state updated")
        elif name == "report_agent":
            state["report_section"] = ai_message
            logger.info("Report section updated")
        elif name == "quality_review_agent":
            state["quality_review"] = ai_message
            state["needs_revision"] = "revision needed" in output.lower()
            logger.info(f"Quality review updated. Needs revision: {state['needs_revision']}")
        
        logger.info(f"Agent {name} processing completed")
        return state
    except Exception as e:
        logger.error(f"Error occurred while processing agent {name}: {str(e)}", exc_info=True)
        error_message = AIMessage(content=f"Error: {str(e)}", name=name)
        return {"messages": [error_message]}

def human_choice_node(state: State) -> dict[str, Any]:
    """
    Handle human input to choose the next step in the process.
    """
    logger.info("Prompting for human choice")
    print("Please choose the next step:")
    print("1. Regenerate hypothesis")
    print("2. Continue the research process")
    
    while True:
        choice = input("Please enter your choice (1 or 2): ")
        if choice in ["1", "2"]:
            break
        logger.warning(f"Invalid input received: {choice}")
        print("Invalid input, please try again.")
    
    content = "Regenerate hypothesis" if choice == "1" else "Continue the research process"
    human_message = HumanMessage(content=content)
    
    state["messages"].append(human_message)
    state["sender"] = 'human'
    
    if choice == "1":
        state["hypothesis"] = ""
        logger.info("Hypothesis cleared for regeneration")
    else:
        state["process"] = "Continue the research process"
        logger.info("Continuing research process")
    
    logger.info("Human choice processed")
    return state

def create_message(message: dict[str], name: str) -> BaseMessage:
    """
    Create a BaseMessage object based on the message type.
    """
    content = message.get("content", "")
    message_type = message.get("type", "").lower()
    
    logger.debug(f"Creating message of type {message_type} for {name}")
    return HumanMessage(content=content) if message_type == "human" else AIMessage(content=content, name=name)

def note_agent_node(state: State, agent: Any, name: str) -> State:
    """
    Process the note agent's action and update the entire state.
    """
    logger.info(f"Processing note agent: {name}")
    try:
        current_messages = state.get("messages", [])
        
        head_messages, tail_messages = [], []
        
        if len(current_messages) > 6:
            head_messages = current_messages[:2] 
            tail_messages = current_messages[-2:]
            state = {**state, "messages": current_messages[2:-2]}
            logger.debug("Trimmed messages for processing")
        
        result = agent.invoke(state)
        logger.debug(f"Note agent {name} result: {result}")
        output = result["output"] if isinstance(result, dict) and "output" in result else str(result)

        cleaned_output = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', output)
        parsed_output = json.loads(cleaned_output)
        logger.debug(f"Parsed output: {parsed_output}")

        new_messages = [create_message(msg, name) for msg in parsed_output.get("messages", [])]
        
        messages = new_messages if new_messages else current_messages
        
        combined_messages = head_messages + messages + tail_messages
        
        updated_state: State = {
            "messages": combined_messages,
            "hypothesis": str(parsed_output.get("hypothesis", state.get("hypothesis", ""))),
            "process": str(parsed_output.get("process", state.get("process", ""))),
            "process_decision": str(parsed_output.get("process_decision", state.get("process_decision", ""))),
            "visualization_state": str(parsed_output.get("visualization_state", state.get("visualization_state", ""))),
            "searcher_state": str(parsed_output.get("searcher_state", state.get("searcher_state", ""))),
            "code_state": str(parsed_output.get("code_state", state.get("code_state", ""))),
            "report_section": str(parsed_output.get("report_section", state.get("report_section", ""))),
            "quality_review": str(parsed_output.get("quality_review", state.get("quality_review", ""))),
            "needs_revision": bool(parsed_output.get("needs_revision", state.get("needs_revision", False))),
            "sender": 'note_agent'
        }
        
        logger.info("Updated state successfully")
        return updated_state

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}", exc_info=True)
        return _create_error_state(state, AIMessage(content=f"Error parsing output: {output}", name=name), name, "JSON decode error")

    except InternalServerError as e:
        logger.error(f"OpenAI Internal Server Error: {e}", exc_info=True)
        return _create_error_state(state, AIMessage(content=f"OpenAI Error: {str(e)}", name=name), name, "OpenAI error")

    except Exception as e:
        logger.error(f"Unexpected error in note_agent_node: {e}", exc_info=True)
        return _create_error_state(state, AIMessage(content=f"Unexpected error: {str(e)}", name=name), name, "Unexpected error")

def _create_error_state(state: State, error_message: AIMessage, name: str, error_type: str) -> State:
    """
    Create an error state when an exception occurs.
    """
    logger.info(f"Creating error state for {name}: {error_type}")
    error_state:State = {
            "messages": state.get("messages", []) + [error_message],
            "hypothesis": str(state.get("hypothesis", "")),
            "process": str(state.get("process", "")),
            "process_decision": str(state.get("process_decision", "")),
            "visualization_state": str(state.get("visualization_state", "")),
            "searcher_state": str(state.get("searcher_state", "")),
            "code_state": str(state.get("code_state", "")),
            "report_section": str(state.get("report_section", "")),
            "quality_review": str(state.get("quality_review", "")),
            "needs_revision": bool(state.get("needs_revision", False)),
            "sender": 'note_agent'
        }
    return error_state

def human_review_node(state: State) -> State:
    """
    Display current state to the user and update the state based on user input.
    Includes error handling for robustness.
    """
    try:
        print("Current research progress:")
        print(state)
        print("\nDo you need additional analysis or modifications?")
        
        while True:
            user_input = input("Enter 'yes' to continue analysis, or 'no' to end the research: ").lower()
            if user_input in ['yes', 'no']:
                break
            print("Invalid input. Please enter 'yes' or 'no'.")
        
        if user_input == 'yes':
            while True:
                additional_request = input("Please enter your additional analysis request: ").strip()
                if additional_request:
                    state["messages"].append(HumanMessage(content=additional_request))
                    state["needs_revision"] = True
                    break
                print("Request cannot be empty. Please try again.")
        else:
            state["needs_revision"] = False
        
        state["sender"] = "human"
        logger.info("Human review completed successfully.")
        return state
    
    except KeyboardInterrupt:
        logger.warning("Human review interrupted by user.")
        return None
    
    except Exception as e:
        logger.error(f"An error occurred during human review: {str(e)}", exc_info=True)
        return None
    
logger.info("Agent processing module initialized")