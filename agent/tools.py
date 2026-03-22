import json, os, random, string
from datetime import datetime, timedelta
from typing import Optional

_FAQ_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "faq.json")
_faq_cache: Optional[dict] = None

def _faq() -> dict:
    global _faq_cache
    if _faq_cache is None:
        with open(_FAQ_PATH) as f:
            _faq_cache = json.load(f)
    return _faq_cache

def search_faq(query: str) -> str:
    """Search the FAQ knowledge base."""
    q = query.lower()
    scored = sorted(
        [(sum(1 for kw in e["keywords"] if kw in q), e) for e in _faq()["entries"]],
        key=lambda x: x[0], reverse=True
    )
    hits = [e for score, e in scored if score > 0][:2]
    if not hits:
        return "No FAQ entries matched. Consider opening a support ticket."
    return "\n\n".join(f"Q: {e['question']}\nA: {e['answer']}" for e in hits)

def check_order_status(order_id: str) -> str:
    """Check the status of a customer order by order ID."""
    oid = order_id.upper().strip()
    if len(oid) < 4:
        return f"Invalid order ID '{oid}'. Expected format: ORD-XXXXXX."
    seed = sum(ord(c) for c in oid)
    statuses = ["Processing","Shipped","Out for Delivery","Delivered","Return Requested"]
    carriers = ["FedEx","UPS","USPS","DHL"]
    status = statuses[seed % len(statuses)]
    carrier = carriers[seed % len(carriers)]
    eta = (datetime.now() + timedelta(days=seed % 5 + 1)).strftime("%B %d, %Y")
    tracking = "".join(str(seed * i % 10) for i in range(1, 13))
    if status == "Delivered":
        return f"Order {oid}: {status}. Delivered on {eta} via {carrier}."
    if status == "Processing":
        return f"Order {oid}: {status}. Estimated ship date: {eta}. Your order is being prepared."
    return f"Order {oid}: {status}. Carrier: {carrier}. Tracking #{tracking}. ETA: {eta}."

def create_ticket(issue: str, priority: str = "medium") -> str:
    """Create a customer support ticket."""
    priority = priority.lower() if priority.lower() in ("low","medium","high","urgent") else "medium"
    tid = "TKT-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    sla = {"low":72,"medium":24,"high":8,"urgent":2}[priority]
    return (f"Ticket {tid} created.\nPriority: {priority.upper()}\nIssue: {issue[:200]}\n"
            f"Created: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\nExpected response: within {sla} hours.")

def get_product_info(product_name: str) -> str:
    """Get product details, pricing, and availability."""
    catalog = {
        "laptop": ("ProBook X15","$1,299","In Stock","2 years","Intel i7-13th, 16GB RAM, 512GB NVMe SSD"),
        "phone": ("SmartPhone Pro 14","$899","Limited (8 units)","1 year","6.7\" OLED, 256GB, 5G, 200MP camera"),
        "headphones": ("AudioMax Pro","$249","In Stock","1 year","ANC, 30hr battery, Bluetooth 5.3"),
        "tablet": ("TabPro 12","$699","Out of Stock","1 year","12\" display, M2 chip, 256GB"),
        "monitor": ("ViewMax 27\" 4K","$549","In Stock","3 years","27\" IPS, 4K, 144Hz, USB-C 90W"),
        "keyboard": ("MechType Pro","$149","In Stock","2 years","Mechanical, per-key RGB, wireless 2.4GHz"),
        "mouse": ("PrecisionPro X","$89","In Stock","1 year","8000 DPI, wireless, 70hr battery"),
        "charger": ("PowerBlock 65W","$49","In Stock","1 year","USB-C PD 65W, GaN tech, 2-port"),
    }
    pn = product_name.lower()
    for key, (name, price, stock, warranty, specs) in catalog.items():
        if key in pn or pn in key:
            return f"Product: {name}\nPrice: {price}\nAvailability: {stock}\nWarranty: {warranty}\nSpecs: {specs}"
    return f"Product '{product_name}' not found. Available: laptop, phone, headphones, tablet, monitor, keyboard, mouse, charger."

def escalate_to_human(reason: str) -> str:
    """Escalate to a live human support agent."""
    eid = "ESC-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    q = random.randint(2, 7)
    return (f"Escalation {eid} initiated.\nReason: {reason[:150]}\nQueue position: {q} | Est. wait: {q*5} minutes.\nA human agent will join this chat shortly.")

TOOLS = {
    "search_faq": {"fn": search_faq, "desc": "Search FAQ knowledge base", "icon": "🔍"},
    "check_order_status": {"fn": check_order_status, "desc": "Look up order by ID", "icon": "📦"},
    "create_ticket": {"fn": create_ticket, "desc": "Open a support ticket", "icon": "🎫"},
    "get_product_info": {"fn": get_product_info, "desc": "Get product details", "icon": "🛍️"},
    "escalate_to_human": {"fn": escalate_to_human, "desc": "Transfer to live agent", "icon": "👤"},
}

def execute_tool(tool_name: str, tool_input: dict) -> str:
    tool = TOOLS.get(tool_name)
    if not tool:
        return f"Unknown tool '{tool_name}'. Available: {', '.join(TOOLS)}"
    try:
        return tool["fn"](**tool_input)
    except TypeError as e:
        return f"Tool parameter error: {e}"
    except Exception as e:
        return f"Tool execution error: {e}"