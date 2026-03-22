# 🏗️ TechStore Support Agent - Architecture Guide

## **Project Overview**

This is an **AI-powered customer support chatbot** that uses **LangGraph** (ReAct pattern) and **HuggingFace models** to answer customer questions about TechStore products and services.

**Goal:** Automate customer support by intelligently routing questions to the right tools and providing instant answers.

---

## **How It Works: The ReAct Loop**

### **Step 1: User Sends Message**
```
User: "What is your return policy?"
         ↓
    Flask Backend (/api/chat)
         ↓
    Creates LangGraph session
```

### **Step 2: Agent Thinks**
The **Qwen AI Model** receives the question and decides:
- "I need to search the FAQ for 'return policy'"
- Outputs in this format:
  ```
  Thought: The user is asking about return policy
  Action: search_faq
  Action Input: {"query": "return policy"}
  ```

### **Step 3: Tool Execution**
The agent's decision is parsed and a **tool is executed**:
```python
search_faq("return policy")
→ Returns best matching FAQ entries
→ "You may return items within 30 days..."
```

### **Step 4: Agent Responds**
The tool result is fed back to the AI, which writes:
```
Thought: I have the information needed
Final Answer: You may return most items within 30 days...
```

### **Step 5: Stream to User**
Response is streamed via **Server-Sent Events (SSE)** in real-time:
```
Browser receives: "You may return most items within 30 days..."
Shows on screen instantly
```

---

## **Project Structure**

```
langgraph-support-agent/
├── app.py                 # Main Flask server
├── events.py              # Event streaming system
├── requirements.txt       # Python dependencies
├── Dockerfile             # Container config
├── agent/
│   ├── __init__.py
│   ├── state.py          # Agent state definition
│   ├── tools.py          # 5 support tools
│   ├── llm.py            # Qwen integration
│   ├── nodes.py          # ReAct nodes
│   └── graph.py          # LangGraph definition
├── data/
│   └── faq.json          # FAQ knowledge base
├── templates/
│   └── index.html        # Web UI
├── static/
│   └── app.js            # Frontend logic
└── docs/
    └── project-template.html
```

---

## **The 5 Tools**

### **1. 🔍 search_faq(query)**
- **What:** Searches the FAQ knowledge base
- **Use Case:** User asks "What's your return policy?"
- **Example:**
  ```
  search_faq("return policy")
  → Returns matching FAQ entries
  ```

### **2. 📦 check_order_status(order_id)**
- **What:** Looks up order status and tracking
- **Use Case:** User asks "Where is my order ORD-482910?"
- **Example:**
  ```
  check_order_status("ORD-482910")
  → Order: ORD-482910: Shipped. Tracking #1234567890. ETA: March 25, 2026
  ```

### **3. 🛍️ get_product_info(product_name)**
- **What:** Returns product specs, price, availability
- **Use Case:** User asks "Do you have laptops in stock?"
- **Example:**
  ```
  get_product_info("laptop")
  → Product: ProBook X15
     Price: $1,299
     Availability: In Stock
     Specs: Intel i7-13th, 16GB RAM, 512GB NVMe SSD
  ```

### **4. 🎫 create_ticket(issue, priority)**
- **What:** Creates a support ticket
- **Use Case:** User says "I need to report a broken product"
- **Example:**
  ```
  create_ticket("Screen is broken", "high")
  → Ticket TKT-ABC123 created
     Priority: HIGH
     Expected response: within 8 hours
  ```

### **5. 👤 escalate_to_human(reason)**
- **What:** Transfers conversation to human agent
- **Use Case:** User says "I want to talk to someone"
- **Example:**
  ```
  escalate_to_human("Unhappy customer")
  → Escalation ESC-XYZ initiated
     Queue position: 3 | Est. wait: 15 minutes
  ```

---

## **Key Technologies**

| Component | Purpose |
|-----------|---------|
| **Flask** | Web server & API |
| **LangGraph** | Agent orchestration (ReAct pattern) |
| **Qwen 2.5 7B** | AI Model (HuggingFace Inference API) |
| **Server-Sent Events** | Real-time streaming |
| **Threading** | Async task processing |
| **LangChain** | Message handling & parsing |

---

## **The ReAct Pattern**

**ReAct** = **Reasoning + Acting**

```
┌─────────────────────────────────────────┐
│  1. Router Node                         │
│     ↓                                   │
│  2. Agent Loop (Reasoning)              │
│     - Qwen thinks about question        │
│     - Decides which tool to use         │
│     ↓                                   │
│  3. Tool Executor (Acting)              │
│     - Executes the chosen tool          │
│     - Returns result                    │
│     ↓                                   │
│  4. Back to Agent (Loop)                │
│     - Has tool result                   │
│     - Decides: use another tool or end? │
│     ↓                                   │
│  5. Responder Node                      │
│     - Final answer sent to user         │
│     ↓                                   │
│  6. END                                 │
└─────────────────────────────────────────┘
```

**Max 4 tool calls per turn** (to prevent infinite loops)

---

## **UI Layout (60% Chat Focus)**

```
┌─────────────────────────────────────────────────────┐
│ 🛍️ TechStore Support Agent  │ Orders · FAQs · Tickets │
├──────────────────────────────────────────────────────┤
│          │                              │            │
│          │                              │            │
│  20%     │         60% Chat             │   20%      │
│ Sidebar  │  (Messages & Input)          │  Panel     │
│          │                              │ (Tools &   │
│ • Model  │  User: "What is return      │  Trace)    │
│ • Status │         policy?"             │            │
│ • Stats  │                              │ • Tool     │
│          │  Agent: "You may return     │   Calls    │
│          │  items within 30 days..."   │ • Execution│
│          │                              │  Trace     │
│          │                              │            │
└──────────────────────────────────────────────────────┘
```

---

## **Data Flow**

```
┌────────────┐
│   User     │
└──────┬─────┘
       │ "What is your return policy?"
       ↓
┌──────────────────────────────────┐
│   Flask API /api/chat            │
│   - Validates input              │
│   - Gets HF_TOKEN from .env      │
└──────┬───────────────────────────┘
       │
       ↓
┌──────────────────────────────────┐
│   LangGraph StateGraph           │
│   - Manages Agent State          │
│   - Orchestrates nodes           │
└──────┬───────────────────────────┘
       │
       ├─ Router Node → sends to Agent
       │
       ├─ Agent Node
       │   - Calls Qwen AI model
       │   - Parses: "Action: search_faq"
       │
       ├─ Tool Executor Node
       │   - Executes tool
       │   - search_faq("return policy")
       │
       ├─ Agent Node (again)
       │   - Decides: Final Answer or more tools?
       │
       └─ Responder Node
           - Finalizes response
           - Emits events via SSE
           │
           ↓
    ┌─────────────────────┐
    │  Browser (SSE)      │
    │  Receives events    │
    │  in real-time       │
    └─────────────────────┘
           │
           ↓
    ┌─────────────────────┐
    │  User sees answer   │
    │  "You may return... │
    └─────────────────────┘
```

---

## **How to Extend This**

### **Add a New Tool**
1. Create function in `agent/tools.py`:
   ```python
   def my_tool(param: str) -> str:
       """My new tool."""
       return "result"
   ```

2. Add to TOOLS dict:
   ```python
   TOOLS = {
       ...
       "my_tool": {"fn": my_tool, "desc": "My tool", "icon": "🔧"},
   }
   ```

3. Update system prompt in `agent/llm.py` to mention it

### **Change AI Model**
Edit `app.py`:
```python
AVAILABLE_MODELS = [
    {"id":"different-model/name","name":"Display Name","badge":"✓"},
]
```

### **Update FAQ**
Edit `data/faq.json` - add/modify entries

---

## **Deployment**

This is designed for **HuggingFace Spaces**:

1. Set `HF_TOKEN` in Space Secrets
2. Push code to repo
3. Space auto-deploys with Docker
4. Runs on port 7860

---

## **Summary**

- **What:** Customer support chatbot for TechStore
- **How:** LangGraph orchestrates an AI agent through a ReAct loop
- **Why:** Automate support & provide instant answers
- **Tech:** Flask + LangGraph + Qwen + SSE streaming
- **Scalable:** Can add more tools/FAQs without changing architecture
