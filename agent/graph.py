from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes import router_node, agent_node, tool_executor_node, responder_node

def _route_agent(state: AgentState) -> str:
    return "responder" if (state.get("should_end") or not state.get("pending_tool")) else "tool_executor"

def build_graph():
    g = StateGraph(AgentState)
    g.add_node("router", router_node)
    g.add_node("agent", agent_node)
    g.add_node("tool_executor", tool_executor_node)
    g.add_node("responder", responder_node)
    g.set_entry_point("router")
    g.add_edge("router","agent")
    g.add_conditional_edges("agent", _route_agent, {"responder":"responder","tool_executor":"tool_executor"})
    g.add_edge("tool_executor","agent")
    g.add_edge("responder",END)
    return g.compile()