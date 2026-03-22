import re, json
from typing import Optional, Callable
from huggingface_hub import InferenceClient

SYSTEM_PROMPT = """You are a professional customer support agent for TechStore, a consumer electronics retailer. You help customers with orders, products, returns, warranties, and technical issues.

You have access to these tools:
1. search_faq(query) — Search FAQ knowledge base
2. check_order_status(order_id) — Get current order status
3. create_ticket(issue, priority) — Open a support ticket (priority: low/medium/high/urgent)
4. get_product_info(product_name) — Get product specs, price, and availability
5. escalate_to_human(reason) — Transfer to a live human agent

To call a tool respond EXACTLY like this:
Thought: [your reasoning]
Action: [exact tool name]
Action Input: {"param": "value"}

When you have enough info and do NOT need another tool:
Thought: [your reasoning]
Final Answer: [your complete friendly reply]

Rules:
- Never invent order IDs, tracking numbers, or product specs — use tools
- If a customer seems very upset or requests a human, use escalate_to_human
- After receiving tool results, always write a Final Answer
- Maximum 4 tool calls per turn"""


def _merge_system_into_user(messages: list) -> list:
    """Fallback: prepend system prompt into the first user message for models
    that reject the system role (e.g. Mistral v0.3 on the free HF tier)."""
    out = []
    sys_content = ""
    for m in messages:
        if m["role"] == "system":
            sys_content = m["content"]
        else:
            out.append(m)
    if sys_content and out:
        first_user_idx = next((i for i, m in enumerate(out) if m["role"] == "user"), None)
        if first_user_idx is not None:
            out[first_user_idx] = {
                "role": "user",
                "content": f"[Instructions]\n{sys_content}\n\n[Customer message]\n{out[first_user_idx]['content']}"
            }
    return out


def build_messages(user_msg: str, history: list, tool_obs: list) -> list:
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in history[-12:]:
        if m.get("role") in ("user", "assistant"):
            msgs.append({"role": m["role"], "content": m["content"]})
    msgs.append({"role": "user", "content": user_msg})
    if tool_obs:
        obs = "\n\n".join(f"[{o['tool']} result]\n{o['result']}" for o in tool_obs)
        msgs.append({"role": "user", "content": f"Tool results:\n{obs}\n\nNow write your Final Answer."})
    return msgs


def parse_tool_call(text: str) -> Optional[tuple]:
    action = re.search(r"Action:\s*(\w+)", text, re.IGNORECASE)
    if not action:
        return None
    name = action.group(1).strip()
    jm = re.search(r"Action Input:\s*(\{.*?\})", text, re.DOTALL)
    if jm:
        try:
            return name, json.loads(jm.group(1))
        except json.JSONDecodeError:
            pass
    raw = re.search(r"Action Input:\s*(.+?)(?:\n\n|$)", text, re.DOTALL)
    if raw:
        r = raw.group(1).strip()
        pairs = re.findall(r'"?(\w+)"?\s*:\s*"([^"]*)"', r)
        if pairs:
            return name, dict(pairs)
        return name, {"query": r}
    return name, {}


def parse_final_answer(text: str) -> Optional[str]:
    m = re.search(r"Final Answer:\s*(.+)", text, re.DOTALL | re.IGNORECASE)
    if m:
        return re.sub(r"\s*---\s*$", "", m.group(1)).strip()
    return None


def _try_stream(client: InferenceClient, model: str, messages: list,
                emit_token: Callable[[str], None], max_tokens: int) -> str:
    full = ""
    for chunk in client.chat_completion(
        messages=messages, model=model,
        max_tokens=max_tokens, temperature=0.25, stream=True
    ):
        delta = chunk.choices[0].delta.content
        if delta:
            full += delta
            emit_token(delta)
    return full


def call_llm_streaming(client: InferenceClient, model: str, messages: list,
                        emit_token: Callable[[str], None], max_tokens: int = 900) -> str:
    """Call LLM with two-stage fallback: system role → merged prompt."""

    # Attempt 1: standard messages with system role
    try:
        return _try_stream(client, model, messages, emit_token, max_tokens)
    except Exception as e:
        err_str = str(e)
        # Check if it's a model/system role error (retry) or other error (fail fast)
        is_model_error = ("Bad request" in err_str or "400" in err_str or
                         "role" in err_str.lower() or "model" in err_str.lower())

        if not is_model_error:
            msg = f"\n[LLM Error: {err_str[:150]}]"
            emit_token(msg)
            return msg

    # Attempt 2: merge system prompt into first user message
    emit_token("\n[Retrying with merged prompt…]\n")
    merged = _merge_system_into_user(messages)
    try:
        return _try_stream(client, model, merged, emit_token, max_tokens)
    except Exception as e2:
        msg = f"\n[LLM Error: Model '{model}' failed: {str(e2)[:100]}]"
        emit_token(msg)
        return msg


def call_llm_with_fallback(client: InferenceClient, primary_model: str,
                           fallback_models: list, messages: list,
                           emit_token: Callable[[str], None], max_tokens: int = 900) -> tuple:
    """Try primary model, then fallback models. Returns (result, model_used)."""

    models_to_try = [primary_model] + fallback_models
    last_error = None

    for attempt, model in enumerate(models_to_try):
        try:
            emit_token(f"\n[Using model: {model.split('/')[-1]}]\n") if attempt > 0 else None
            result = call_llm_streaming(client, model, messages, emit_token, max_tokens)

            # If we got a result without error markers, return it
            if "[LLM Error" not in result:
                return result, model

        except Exception as e:
            last_error = str(e)
            continue

    # All models failed
    msg = f"\n[All models failed. Last error: {str(last_error)[:100]}]"
    emit_token(msg)
    return msg, primary_model