import json, queue, threading, time, uuid
from datetime import datetime
from flask import Flask, render_template, request, Response, jsonify
from dotenv import load_dotenv
import os
import events

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY","lgsa-2025-dev-secret")

AVAILABLE_MODELS = [
    {"id":"meta-llama/Meta-Llama-3.1-8B-Instruct","name":"Llama 3.1 8B Instruct","badge":"🦙 Recommended"},
    {"id":"Qwen/Qwen2.5-7B-Instruct","name":"Qwen 2.5 7B Instruct","badge":"⚡ Fast"},
    {"id":"mistralai/Mistral-7B-Instruct-v0.3","name":"Mistral 7B Instruct v0.3","badge":"🌀 Mistral"},
    {"id":"google/gemma-2-9b-it","name":"Gemma 2 9B Instruct","badge":"💎 Google"},
]

_sessions: dict = {}
_lock = threading.Lock()

class Session:
    def __init__(self, sid, model):
        self.session_id = sid
        self.model_name = model
        self.messages: list = []
        self.tool_calls: list = []
        self.node_traces: list = []
        self.turn_count = 0
        self.total_tokens = 0
        self.latency_history: list = []

def _get(sid, model=""):
    with _lock:
        if sid not in _sessions:
            _sessions[sid] = Session(sid, model or AVAILABLE_MODELS[0]["id"])
        elif model:
            _sessions[sid].model_name = model
        return _sessions[sid]

def _analytics(s):
    usage = {}
    for tc in s.tool_calls:
        usage[tc["tool_name"]] = usage.get(tc["tool_name"],0) + 1
    avg = round(sum(s.latency_history)/max(len(s.latency_history),1),1)
    return {"turn_count":s.turn_count,"total_tokens":s.total_tokens,"avg_latency_ms":avg,
            "latency_history":s.latency_history[-20:],"tool_call_count":len(s.tool_calls),
            "tool_usage":usage,"node_traces":s.node_traces[-30:]}

def _tok(text): return max(1, int(len(text.split())*1.35))

@app.route("/")
def index():
    return render_template("index.html", models=AVAILABLE_MODELS)

@app.route("/api/models")
def api_models():
    return jsonify(AVAILABLE_MODELS)

@app.route("/api/chat", methods=["POST"])
def api_chat():
    body = request.get_json(force=True) or {}
    user_message = (body.get("message") or "").strip()
    model_name = body.get("model") or AVAILABLE_MODELS[0]["id"]
    session_id = body.get("session_id") or str(uuid.uuid4())
    if not user_message:
        return jsonify({"error":"Message cannot be empty."}), 400
    hf_token = os.getenv("HF_TOKEN","").strip()

    def generate():
        if not hf_token:
            yield f"data: {json.dumps({'type':'error','message':'HF_TOKEN not set. Add it as a Space secret under Settings → Variables and Secrets.'})}\n\n"
            return
        s = _get(session_id, model_name)
        s.turn_count += 1
        t_start = time.time()
        user_entry = {"role":"user","content":user_message,"token_count":_tok(user_message),"timestamp":datetime.utcnow().isoformat()+"Z"}
        s.messages.append(user_entry)
        events.clear_queue(session_id)
        prior = list(s.messages[:-1])
        from agent.state import AgentState
        from agent.graph import build_graph
        from langchain_core.messages import HumanMessage
        initial: AgentState = {"messages":[HumanMessage(content=user_message)],"current_node":"router",
                               "model_name":model_name,"session_id":session_id,"hf_token":hf_token,
                               "iteration_count":0,"should_end":False,"final_answer":None,"error":None,
                               "conversation_history":prior,"pending_tool":None}
        result_box: dict = {}
        def run():
            try:
                result_box["result"] = build_graph().invoke(initial)
            except Exception as exc:
                result_box["error"] = str(exc)
            finally:
                events.emit(session_id, {"type":"_done"})
        threading.Thread(target=run, daemon=True).start()
        q = events.get_queue(session_id)
        buf: list = []
        while True:
            try:
                ev = q.get(timeout=90)
            except queue.Empty:
                yield f"data: {json.dumps({'type':'error','message':'Response timed out.'})}\n\n"
                return
            if ev["type"] == "_done":
                break
            if ev["type"] == "token":
                buf.append(ev["content"])
            elif ev["type"] == "node_enter":
                s.node_traces.append({"node_name":ev["node"],"entered_at":ev["timestamp"],"exited_at":None,"duration_ms":None,"status":"running"})
            elif ev["type"] == "node_exit":
                for tr in reversed(s.node_traces):
                    if tr["node_name"] == ev["node"] and tr["status"] == "running":
                        tr.update({"exited_at":ev["timestamp"],"duration_ms":ev.get("duration_ms"),"status":"completed"})
                        break
            elif ev["type"] == "tool_call":
                s.tool_calls.append({"tool_name":ev["name"],"tool_input":ev.get("input",{}),"tool_output":"","timestamp":ev["timestamp"],"latency_ms":0})
            elif ev["type"] == "tool_result":
                for tc in reversed(s.tool_calls):
                    if tc["tool_name"] == ev["name"] and tc["tool_output"] == "":
                        tc.update({"tool_output":ev.get("output",""),"latency_ms":ev.get("latency_ms",0)})
                        break
            yield f"data: {json.dumps(ev)}\n\n"
        if "error" in result_box:
            yield f"data: {json.dumps({'type':'error','message':result_box['error']})}\n\n"
            return
        final = ((result_box.get("result") or {}).get("final_answer") or "".join(buf)).strip()
        if not final:
            final = "I'm sorry, I wasn't able to generate a response. Please try again."
        elapsed = round((time.time()-t_start)*1000,1)
        tok = _tok(final)
        s.total_tokens += tok + user_entry["token_count"]
        s.latency_history.append(elapsed)
        asst = {"role":"assistant","content":final,"token_count":tok,"timestamp":datetime.utcnow().isoformat()+"Z"}
        s.messages.append(asst)
        yield f"data: {json.dumps({'type':'done','session_id':session_id,'message':asst,'latency_ms':elapsed,'analytics':_analytics(s)})}\n\n"

    resp = Response(generate(), mimetype="text/event-stream")
    resp.headers.update({"Cache-Control":"no-cache","X-Accel-Buffering":"no","X-Session-ID":session_id})
    return resp

@app.route("/api/session/<session_id>")
def api_session(session_id):
    with _lock:
        s = _sessions.get(session_id)
    if not s:
        return jsonify({"error":"Session not found"}), 404
    return jsonify({"session_id":session_id,"model_name":s.model_name,"messages":s.messages,"tool_calls":s.tool_calls,"node_traces":s.node_traces,"analytics":_analytics(s)})

@app.route("/api/reset", methods=["POST"])
def api_reset():
    body = request.get_json(force=True) or {}
    sid = body.get("session_id") or str(uuid.uuid4())
    model = body.get("model") or AVAILABLE_MODELS[0]["id"]
    with _lock:
        _sessions[sid] = Session(sid, model)
    events.clear_queue(sid)
    return jsonify({"status":"ok","session_id":sid})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860, debug=False, threaded=True)

