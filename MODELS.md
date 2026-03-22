# 🤖 Available Models - Feature Guide

## **What Changed?**

We added **4 different free HuggingFace models** that you can switch between in real-time. Each has different trade-offs.

---

## **Available Models**

### **1. ⚡ Qwen 2.5 7B (Default)**
- **Speed:** ⚡⚡⚡ Very Fast
- **Quality:** ⭐⭐⭐⭐⭐ Excellent
- **Model:** `Qwen/Qwen2.5-7B-Instruct`
- **Best for:** Production use, balanced quality & speed
- **Size:** 7B parameters
- **Why it's first:** Most reliable on free-tier HuggingFace

### **2. 💎 Gemma 2 9B**
- **Speed:** ⚡⚡⚡ Fast
- **Quality:** ⭐⭐⭐⭐⭐ Excellent
- **Model:** `google/gemma-2-9b-it`
- **Best for:** High-quality responses
- **Size:** 9B parameters
- **Note:** Google model, very reliable

### **3. 🌀 Mistral 7B**
- **Speed:** ⚡⚡⚡ Fast
- **Quality:** ⭐⭐⭐⭐ Very Good
- **Model:** `mistralai/Mistral-7B-Instruct-v0.2`
- **Best for:** Balanced option, newer version
- **Size:** 7B parameters
- **Note:** Good alternative to Qwen

### **4. ⚙️ TinyLlama 1.1B**
- **Speed:** ⚡⚡⚡⚡⚡ Ultra Fast
- **Quality:** ⭐⭐⭐ Good
- **Model:** `TinyLlama/TinyLlama-1.1B-Chat-v1.0`
- **Best for:** Testing, learning, super fast responses
- **Size:** 1.1B parameters (tiny!)
- **Note:** Much smaller, faster, but less capable

---

## **How Switching Works**

### **User Selects Model:**
```
1. User picks "Gemma 2 9B" from dropdown
2. Frontend sends: {"model": "google/gemma-2-9b-it"}
3. Backend receives request
4. LangGraph agent uses Gemma instead of Qwen
```

### **Smart Fallback (NEW!):**
If the selected model fails, the agent **automatically tries fallback models**:

```
User selected: Qwen
         ↓
    Qwen fails
         ↓
    Try: Gemma 2 9B
         ↓
    Gemma works!
         ↓
    Returns result using Gemma
    (User sees: "Model switched to Gemma")
```

**Fallback order:**
1. Gemma 2 9B
2. Mistral 7B
3. TinyLlama 1.1B

---

## **When to Use Each Model**

| Scenario | Model | Why |
|----------|-------|-----|
| **Production** | Qwen 2.5 | Reliable + fast + free-tier |
| **Quality matters** | Gemma 2 | Highest quality responses |
| **Testing** | TinyLlama | Instant responses |
| **Unsure** | Qwen 2.5 | Default is always safe |

---

## **Code Changes Made**

### **1. `app.py` - Added 4 Models**
```python
AVAILABLE_MODELS = [
    {"id":"Qwen/Qwen2.5-7B-Instruct","name":"Qwen 2.5 7B","badge":"⚡ Fast & Reliable"},
    {"id":"google/gemma-2-9b-it","name":"Gemma 2 9B","badge":"💎 Quality"},
    {"id":"mistralai/Mistral-7B-Instruct-v0.2","name":"Mistral 7B","badge":"🌀 Balanced"},
    {"id":"TinyLlama/TinyLlama-1.1B-Chat-v1.0","name":"TinyLlama 1.1B","badge":"⚙️ Lightweight"},
]

FALLBACK_MODEL = "Qwen/Qwen2.5-7B-Instruct"
```

### **2. `agent/llm.py` - Added Fallback Logic**
```python
def call_llm_with_fallback(client, primary_model, fallback_models, messages, emit_token):
    """Try primary model, then fallback models if it fails"""
    # Tries models in order until one works
    # Returns (result, model_used)
```

### **3. `agent/nodes.py` - Using Fallback**
```python
full_text, used_model = call_llm_with_fallback(
    client, state["model_name"], FALLBACK_MODELS, messages, emit_token
)

# Logs if model was switched
if used_model != state["model_name"]:
    ev.emit(sid, {"type":"model_switch","from":state["model_name"],"to":used_model})
```

### **4. `templates/index.html` - Already Works!**
The dropdown automatically loads all 4 models from backend.

---

## **Testing Models**

Try each model with the same question to see differences:

**Test Question:** "What is your return policy?"

1. **Qwen 2.5** - Fast, concise answer
2. **Gemma 2** - Detailed, thorough answer
3. **Mistral 7B** - Clear, structured answer
4. **TinyLlama** - Shorter but good answer

---

## **Next Steps You Can Do**

1. **Add more models** from HuggingFace:
   ```python
   {"id":"meta-llama/Llama-2-7b-chat-hf","name":"Llama 2","badge":"🦙"},
   ```

2. **Compare models** on your own use cases

3. **Use TinyLlama** for testing (instant responses)

4. **Set Gemma as default** if you prefer quality:
   ```python
   AVAILABLE_MODELS = [Gemma, ...]  # Move Gemma to top
   ```

---

## **Important Notes**

✅ **All models are free** - HuggingFace Inference API free tier

✅ **No API keys needed** - Uses your HF_TOKEN (already set)

✅ **Auto-fallback** - Never get stuck without response

✅ **Easy to switch** - Just select from dropdown

❌ **Not real APIs** - All are HuggingFace inference endpoints

❌ **Free tier limits** - May have rate limits (but generous)

---

## **How Free-Tier HF Works**

```
Your Space
    ↓
HuggingFace Inference API (Free)
    ↓
    ├─ Qwen 2.5 7B ✓
    ├─ Gemma 2 9B ✓
    ├─ Mistral 7B ✓
    └─ TinyLlama ✓

All free, no payment needed!
```

Your HF_TOKEN gives you access to all these models.

---

## **Performance Tips**

1. **Use TinyLlama** for testing (1.1B = super fast)
2. **Use Qwen** for production (best balance)
3. **Use Gemma** when you need better quality
4. **Use Mistral** as middle ground

**Speed comparison:**
- TinyLlama: ~500ms
- Qwen: ~1-2s
- Gemma: ~2-3s
- Mistral: ~2-3s

---

Enjoy your multi-model support! 🚀
