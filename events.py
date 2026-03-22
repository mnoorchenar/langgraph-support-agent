import queue, threading
from typing import Dict

_queues: Dict[str, queue.Queue] = {}
_lock = threading.Lock()

def get_queue(session_id: str) -> queue.Queue:
    with _lock:
        if session_id not in _queues:
            _queues[session_id] = queue.Queue()
        return _queues[session_id]

def clear_queue(session_id: str) -> None:
    with _lock:
        _queues[session_id] = queue.Queue()

def emit(session_id: str, event: dict) -> None:
    get_queue(session_id).put(event)