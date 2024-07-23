from langchain_core.messages import BaseMessage
from typing import Sequence,TypedDict
from dataclasses import dataclass,field
class State(TypedDict):
    """Pydantic model for the entire state structure."""
    # The sequence of messages exchanged in the conversation
    messages: Sequence[BaseMessage]

    # The complete content of the research hypothesis
    hypothesis: str = ""
    
    # The complete content of the research process
    process: str = ""
    
    # next process
    process_decision: str = ""
    
    # The current state of data visualization planning and execution
    visualization_state: str = ""
    
    # The current state of the search process, including queries and results
    searcher_state: str = ""
    
    # The current state of Coder development, including scripts and outputs
    code_state: str = ""
    
    # The content of the report sections being written
    report_section: str = ""
    
    # The feedback and comments from the quality review process
    quality_review: str = ""
    
    # A boolean flag indicating if the current output requires revision
    needs_revision: bool = False
    
    # The identifier of the agent who sent the last message
    sender: str = ""
    
from langchain_core.pydantic_v1 import BaseModel, Field
class NoteState(BaseModel):
    """Pydantic model for the entire state structure."""
    messages: Sequence[BaseMessage] = Field(default_factory=list,description="List of message dictionaries")
    hypothesis: str = Field(default="", description="Current research hypothesis")
    process: str = Field(default="", description="Current research process")
    process_decision: str = Field(default="", description="Decision about the next process step")
    visualization_state: str = Field(default="", description="Current state of data visualization")
    searcher_state: str = Field(default="", description="Current state of the search process")
    code_state: str = Field(default="", description="Current state of code development")
    report_section: str = Field(default="", description="Content of the report sections")
    quality_review: str = Field(default="", description="Feedback from quality review")
    needs_revision: bool = Field(default=False, description="Flag indicating if revision is needed")
    sender: str = Field(default="", description="Identifier of the last message sender")
