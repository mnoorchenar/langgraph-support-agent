import time
from datetime import datetime
from huggingface_hub import InferenceClient
from langchain_core.messages import AIMessage, ToolMessage
import events as ev
from agent.state import AgentState
from agent.tools import execute_tool
from agent.llm import build_messages, call_llm_streaming, parse_tool_call, parse_final_answer

def _ts(): return datetime.utcnow().isoformat() + "Z"
def _enter(sid, node):
    ev.emit(sid, {"type":"node_enter","node":node,"timestamp":_ts()})
    return time.time()
def _exit(sid, node, t0):
    ev.emit(sid, {"type":"node_exit","node":node,"duration_ms":round((time.time()-t0)*1000,1),"timestamp":_ts()})

def router_node(state: AgentState) -> dict:
    t0 = _enter(state["session_id"], "router")
    time.sleep(0.04)
    _exit(state["session_id"], "router", t0)
    return {"current_node":"agent","iteration_count":0}

def agent_node(state: AgentState) -> dict:
    sid = state["session_id"]
    t0 = _enter(sid, "agent")
    user_msg, tool_obs = "", []
    for msg in state["messages"]:
        cname = type(msg).__name__
        if cname == "HumanMessage":
            user_msg = msg.content
        elif cname == "ToolMessage":
            tool_obs.append({"tool":getattr(msg,"name","tool"),"result":msg.content})
    client = InferenceClient(api_key=state["hf_token"], provider="auto")
    messages = build_messages(user_msg, state.get("conversation_history",[]), tool_obs)
    full_text = call_llm_streaming(client, state["model_name"], messages,
                                   emit_token=lambda t: ev.emit(sid,{"type":"token","content":t}))
    _exit(sid, "agent", t0)
    itr = state["iteration_count"] + 1
    final = parse_final_answer(full_text)
    if final:
        return {"messages":[AIMessage(content=full_text)],"should_end":True,
                "final_answer":final,"iteration_count":itr,"pending_tool":None}
    tool_call = parse_tool_call(full_text)
    if tool_call and itr <= 4:
        tool_name, tool_input = tool_call
        ev.emit(sid,{"type":"tool_call","name":tool_name,"input":tool_input,"timestamp":_ts()})
        return {"messages":[AIMessage(content=full_text)],"should_end":False,
                "iteration_count":itr,"pending_tool":{"name":tool_name,"input":tool_input},"current_node":"tool_executor"}
    return {"messages":[AIMessage(content=full_text)],"should_end":True,
            "final_answer":full_text.strip(),"iteration_count":itr,"pending_tool":None}

def tool_executor_node(state: AgentState) -> dict:
    sid = state["session_id"]
    t0 = _enter(sid, "tool_executor")
    pending = state.get("pending_tool") or {}
    name = pending.get("name","")
    inp = pending.get("input",{})
    result = execute_tool(name, inp)
    elapsed = round((time.time()-t0)*1000,1)
    ev.emit(sid,{"type":"tool_result","name":name,"output":result,"latency_ms":elapsed,"timestamp":_ts()})
    _exit(sid, "tool_executor", t0)
    return {"messages":[ToolMessage(content=result,tool_call_id=name,name=name)],"current_node":"agent","pending_tool":None}

def responder_node(state: AgentState) -> dict:
    sid = state["session_id"]
    t0 = _enter(sid, "responder")
    _exit(sid, "responder", t0)
    return {"current_node":"end"}