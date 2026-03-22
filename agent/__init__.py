
# ══════════════════════════════════════════════════════════════════════════════
# FILE: agent/state.py
# ══════════════════════════════════════════════════════════════════════════════

from typing import TypedDict, Annotated, List, Optional
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    current_node: str
    model_name: str
    session_id: str
    hf_token: str
    iteration_count: int
    should_end: bool
    final_answer: Optional[str]
    error: Optional[str]
    conversation_history: List[dict]
    pending_tool: Optional[dict]