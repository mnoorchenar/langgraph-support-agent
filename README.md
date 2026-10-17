---
title: langgraph-support-agent
colorFrom: blue
colorTo: indigo
sdk: docker
---

<div align="center">

<h1>🛍️ TechStore Support Agent</h1>
<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=22&duration=3000&pause=1000&color=4F8EF7&center=true&vCenter=true&width=700&lines=AI-Powered+Customer+Support+Agent;Built+with+LangGraph+ReAct+Pattern;5+Tools+%C2%B7+4+Free+HuggingFace+Models+%C2%B7+Real-time+Streaming" alt="Typing SVG"/>

<br/>

[![Python](https://img.shields.io/badge/Python-3.11+-3b82f6?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-4f46e5?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.x-06b6d4?style=for-the-badge)](https://langchain-ai.github.io/langgraph/)
[![Docker](https://img.shields.io/badge/Docker-Ready-3b82f6?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![HuggingFace](https://img.shields.io/badge/HuggingFace-Spaces-ffcc00?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co/mnoorchenar/spaces)
[![Status](https://img.shields.io/badge/Status-Active-22c55e?style=for-the-badge)](#)

**🛍️ TechStore Support Agent** — An intelligent multi-turn customer support chatbot built with LangGraph's ReAct architecture. Powered by free HuggingFace models (Qwen, Gemma, Mistral, TinyLlama), it processes 5 support tools in real-time with token streaming via Server-Sent Events.

---

</div>

## ✨ Features

<table>
  <tr><td>🧠 <b>ReAct Architecture</b></td><td>LangGraph StateGraph orchestrates Thought → Action → Observation with up to 4 tool calls per turn. Parsed from free HuggingFace model output.</td></tr>
  <tr><td>🔧 <b>5 Support Tools</b></td><td><code>search_faq</code>, <code>check_order_status</code>, <code>create_ticket</code>, <code>get_product_info</code>, <code>escalate_to_human</code> — each with real execution logic</td></tr>
  <tr><td>🤖 <b>4 LLM Models</b></td><td>Qwen 2.5 · Gemma 2 · Mistral 7B · TinyLlama with smart auto-fallback. Switch mid-session via dropdown.</td></tr>
  <tr><td>📡 <b>Real-time Streaming</b></td><td>Server-Sent Events (SSE) stream tokens, tool calls, and graph events simultaneously for live UI updates</td></tr>
  <tr><td>🗺️ <b>Execution Tracing</b></td><td>Live graph visualization showing Router → Agent → Tool Executor → Responder with per-node timing</td></tr>
  <tr><td>🔒 <b>Secure by Design</b></td><td>HF_TOKEN via Space secrets (never in code). Session-based state isolation. In-memory per request.</td></tr>
  <tr><td>🐳 <b>Docker Ready</b></td><td>Containerized with gunicorn gthread workers. HuggingFace Spaces compatible (uid 1000, port 7860)</td></tr>
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
    Qwen 2.5 · Gemma 2 9B · Mistral 7B · TinyLlama
         (with automatic fallback chain)
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

## 📊 Dashboard Features

| Feature | Description | Status |
|---------|-------------|--------|
| 💬 **Chat Interface** | Multi-turn conversation with real-time token streaming | ✅ Live |
| 🤖 **Model Switcher** | Dropdown to switch between Qwen, Gemma, Mistral, TinyLlama | ✅ Live |
| 🗺️ **Graph Trace** | Animated visualization of ReAct loop (Router → Agent → Tools → Response) | ✅ Live |
| 🛠️ **Tool Logger** | Expandable log showing every tool call, input, output, and latency | ✅ Live |
| 📈 **Session Stats** | Real-time analytics: turn count, tool usage, latency, token estimate | ✅ Live |
| 📜 **Chat History** | Full conversation history with timestamps and model attribution | ✅ Live |

## 🧠 ML Models

The agent supports **4 free HuggingFace models** with smart fallback:

| Model | Speed | Quality | Best For |
|-------|-------|---------|----------|
| **Qwen 2.5 7B** | ⚡⚡⚡ Fast | ⭐⭐⭐⭐⭐ | Production (default) |
| **Gemma 2 9B** | ⚡⚡⚡ Fast | ⭐⭐⭐⭐⭐ | High-quality responses |
| **Mistral 7B** | ⚡⚡⚡ Fast | ⭐⭐⭐⭐ | Balanced option |
| **TinyLlama 1.1B** | ⚡⚡⚡⚡⚡ Ultra-fast | ⭐⭐⭐ | Testing & learning |

**Fallback chain:** Qwen → Gemma → Mistral → TinyLlama

```python
agent_config = {
    "type":              "ReAct (Reason + Act)",
    "primary_model":     "Qwen/Qwen2.5-7B-Instruct",
    "fallback_models":   ["google/gemma-2-9b-it", "mistralai/Mistral-7B-Instruct-v0.2", "TinyLlama/TinyLlama-1.1B-Chat-v1.0"],
    "tools":             5,
    "max_tool_calls":    4,
    "streaming":         True,  # token-level SSE via InferenceClient
    "auto_fallback":     True,  # switches models if primary fails
}
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