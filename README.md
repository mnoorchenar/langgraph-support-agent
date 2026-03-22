---
title: langgraph-support-agent
colorFrom: blue
colorTo: indigo
sdk: docker
---

<div align="center">

<h1>🤖 LangGraph Support Agent Studio</h1>
<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=22&duration=3000&pause=1000&color=4F8EF7&center=true&vCenter=true&width=700&lines=Multi-turn+Customer+Support+Agent+powered+by+LangGraph;5+AI+Tools+%C2%B7+4+HuggingFace+Models+%C2%B7+ReAct+Architecture;Live+Graph+Tracing+%C2%B7+Tool+Logs+%C2%B7+Session+Analytics" alt="Typing SVG"/>

<br/>

[![Python](https://img.shields.io/badge/Python-3.11+-3b82f6?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-4f46e5?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.x-06b6d4?style=for-the-badge)](https://langchain-ai.github.io/langgraph/)
[![Docker](https://img.shields.io/badge/Docker-Ready-3b82f6?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![HuggingFace](https://img.shields.io/badge/HuggingFace-Spaces-ffcc00?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co/mnoorchenar/spaces)
[![Status](https://img.shields.io/badge/Status-Active-22c55e?style=for-the-badge)](#)

**🤖 LangGraph Support Agent Studio** — A production-grade multi-turn customer support agent built with LangGraph's ReAct architecture, powered entirely by free HuggingFace Inference API models, with live graph tracing, tool call logging, and session analytics streamed in real time via SSE.

---

</div>

## ✨ Features

<table>
  <tr><td>🧠 <b>ReAct Agent Loop</b></td><td>LangGraph StateGraph orchestrates Thought → Action → Observation with up to 4 tool calls per turn, parsed from free-tier HuggingFace model output</td></tr>
  <tr><td>🔧 <b>5 Live Tools</b></td><td>search_faq, check_order_status, create_ticket, get_product_info, escalate_to_human — each with real logic and mock data</td></tr>
  <tr><td>🗺️ <b>Live Graph Trace</b></td><td>Animated node visualizer showing Router → Agent → Tool Executor → Responder with per-node timing via SSE</td></tr>
  <tr><td>📡 <b>Token Streaming</b></td><td>Server-Sent Events stream LLM tokens and graph events simultaneously, updating chat, trace, and tool log in real time</td></tr>
  <tr><td>🔒 <b>Secure by Design</b></td><td>HF_TOKEN injected via HuggingFace Space secrets, never committed to source. All state is in-memory per session</td></tr>
  <tr><td>🐳 <b>Containerized Deployment</b></td><td>Docker-first with gunicorn gthread workers, HuggingFace Spaces-compatible (uid 1000, port 7860)</td></tr>
</table>

## 🏗️ Architecture

```
Browser (SSE) ◀──▶ Flask + gunicorn
                         │
                  LangGraph StateGraph
                  ┌──────────────────┐
                  │ Router → Agent   │
                  │   ↓       ↑      │
                  │ Tool Exec ←┘     │
                  │   ↓              │
                  │ Responder → END  │
                  └──────────────────┘
                         │
                HuggingFace Inference API
          Mistral 7B · Zephyr 7B · Phi-3 · Llama 3
```

## 🚀 Getting Started

```bash
git clone https://github.com/mnoorchenar/langgraph-support-agent.git
cd langgraph-support-agent
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add your HF_TOKEN
python app.py                 # open http://localhost:7860
```

## 🐳 Docker

```bash
docker build -t langgraph-support-agent .
docker run -p 7860:7860 -e HF_TOKEN=hf_your_token_here langgraph-support-agent
```

For HuggingFace Spaces: push this repo and add `HF_TOKEN` as a Space secret under **Settings → Variables and Secrets**.

## 📊 Dashboard Modules

| Module | Description | Status |
|--------|-------------|--------|
| 💬 Chat Interface | Multi-turn streaming chat with SSE token delivery | ✅ Live |
| 🗺️ Graph Trace | Animated LangGraph node visualizer with per-node timing | ✅ Live |
| 🛠️ Tool Call Log | Expandable log of every tool invocation with input/output | ✅ Live |
| 📈 Session Analytics | Chart.js charts — tool usage frequency and latency history | ✅ Live |
| 📜 Conversation History | Full chat history with timestamps and estimated token counts | ✅ Live |
| 🤖 Model Selector | Switch between 4 HuggingFace-hosted LLMs mid-session | ✅ Live |

## 🧠 ML Models

```python
models = {
    "mistral":  "mistralai/Mistral-7B-Instruct-v0.3",
    "zephyr":   "HuggingFaceH4/zephyr-7b-beta",
    "phi3":     "microsoft/Phi-3-mini-4k-instruct",
    "llama3":   "meta-llama/Meta-Llama-3-8B-Instruct",
}
agent_type   = "ReAct (Reason + Act)"
tool_count   = 5
max_iters    = 4
streaming    = True   # token-level SSE via InferenceClient
```

## 📁 Project Structure

```
langgraph-support-agent/
├── app.py                    # Flask app, SSE endpoints, session management
├── events.py                 # Thread-safe per-session SSE event queue
├── agent/
│   ├── state.py              # AgentState TypedDict for LangGraph
│   ├── tools.py              # 5 tool functions + execute_tool dispatcher
│   ├── llm.py                # HF InferenceClient wrapper, ReAct prompt, parsers
│   ├── nodes.py              # Router, Agent, ToolExecutor, Responder node functions
│   └── graph.py              # StateGraph builder with conditional routing
├── data/
│   └── faq.json              # 15-entry FAQ knowledge base
├── templates/
│   └── index.html            # Single-page UI, 4-panel layout, SSE client
├── static/
│   └── app.js                # SSE client, Chart.js, node trace UI, analytics
├── requirements.txt
├── Dockerfile
├── .env.example
└── docs/
    └── project-template.html # Portfolio page
```

## 👨‍💻 Author

<div align="center">
<img src="https://avatars.githubusercontent.com/mnoorchenar" width="100" style="border-radius:50%"/>

**Mohammad Noorchenarboo** — Data Scientist | AI Researcher | Biostatistician

📍 Ontario, Canada · [LinkedIn](https://www.linkedin.com/in/mnoorchenar) · [Website](https://mnoorchenar.github.io/) · [HuggingFace](https://huggingface.co/mnoorchenar/spaces) · [GitHub](https://github.com/mnoorchenar)
</div>

## Disclaimer

This project is developed strictly for educational and research purposes. All datasets are synthetically generated — no real user data is stored. Provided "as is" without warranty of any kind.

## 📜 License

MIT License. See `LICENSE` for details.