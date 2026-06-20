from collections import defaultdict, deque
from threading import Lock
from typing import Deque


class ConversationMemory:
    """按微信 OpenID 保存最近几轮对话。"""

    def __init__(self, max_turns: int = 10) -> None:
        self._max_messages = max(1, max_turns) * 2
        self._store: dict[str, Deque[dict[str, str]]] = defaultdict(
            lambda: deque(maxlen=self._max_messages)
        )
        self._lock = Lock()

    def get_messages(self, user_id: str) -> list[dict[str, str]]:
        with self._lock:
            return list(self._store[user_id])

    def append(self, user_id: str, role: str, content: str) -> None:
        with self._lock:
            self._store[user_id].append({"role": role, "content": content})

    def clear(self, user_id: str) -> None:
        with self._lock:
            self._store.pop(user_id, None)