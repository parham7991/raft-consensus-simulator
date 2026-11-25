"""لایهٔ شبکه‌ی صریح — صف پیام با ``deliver_at``، تأخیر تصادفی و لینک‌های قابل قطع.

این ماژول زمان‌بندی و تحویل را می‌فهمد ولی Raft را نه. هیچ پیامی در هوا ناپدید
نمی‌شود: هر ارسال‌شده یا ``delivered`` می‌شود یا ``dropped`` (لینک پایین یا
گرهٔ مقصد از کار افتاده) و هر دو با رویداد در آمار می‌آیند.
"""

from __future__ import annotations

import heapq
import itertools
from dataclasses import dataclass
from typing import Any, Callable

DELAY_MIN_MS = 5.0
DELAY_MAX_MS = 20.0

EventCallback = Callable[[dict], None]


@dataclass
class Envelope:
    """پوشه‌ی یک پیام در حال پرواز."""

    from_id: int
    to_id: int
    payload: Any
    sent_at: float
    deliver_at: float


class Network:
    """شبکه‌ی خوشه: لینک‌ها متقارن‌اند (افت لینک دوطرفه اعمال می‌شود)."""

    def __init__(
        self,
        on_event: EventCallback | None = None,
        is_reachable: Callable[[int, int], bool] | None = None,
    ) -> None:
        self._queue: list[tuple[float, int, Envelope]] = []
        self._seq = itertools.count()
        self._down_links: set[frozenset] = set()
        self._on_event = on_event
        self._is_reachable = is_reachable
        self.stats = {"sent": 0, "delivered": 0, "dropped": 0}

    # ---------- ارسال و تحویل ----------
    def send(self, from_id: int, to_id: int, payload: Any, now: float, rng) -> Envelope:
        delay = rng.uniform(DELAY_MIN_MS, DELAY_MAX_MS)
        env = Envelope(from_id=from_id, to_id=to_id, payload=payload,
                       sent_at=now, deliver_at=now + delay)
        heapq.heappush(self._queue, (env.deliver_at, next(self._seq), env))
        self.stats["sent"] += 1
        self._emit({"type": "sent", "from_id": from_id, "to_id": to_id,
                    "deliver_at": env.deliver_at})
        return env

    def deliver_due(self, now: float) -> list[Envelope]:
        """همه‌ی پیام‌های سررسیدشده را به‌ترتیب ``deliver_at`` برمی‌گرداند."""
        delivered: list[Envelope] = []
        while self._queue and self._queue[0][0] <= now:
            _, _, env = heapq.heappop(self._queue)
            if not self._can_deliver(env.from_id, env.to_id):
                self.stats["dropped"] += 1
                self._emit({"type": "dropped", "from_id": env.from_id,
                            "to_id": env.to_id, "payload": env.payload})
                continue
            self.stats["delivered"] += 1
            self._emit({"type": "delivered", "from_id": env.from_id,
                        "to_id": env.to_id, "payload": env.payload})
            delivered.append(env)
        return delivered

    def pending(self) -> int:
        return len(self._queue)

    # ---------- لینک‌ها ----------
    def set_link(self, i: int, j: int, up: bool) -> None:
        pair = frozenset((i, j))
        if up:
            self._down_links.discard(pair)
        else:
            self._down_links.add(pair)
        self._emit({"type": "link_up" if up else "link_down", "i": i, "j": j})

    def link_up(self, i: int, j: int) -> bool:
        return frozenset((i, j)) not in self._down_links

    # ---------- داخلی ----------
    def _can_deliver(self, from_id: int, to_id: int) -> bool:
        if not self.link_up(from_id, to_id):
            return False
        if self._is_reachable is not None and not self._is_reachable(from_id, to_id):
            return False
        return True

    def _emit(self, event: dict) -> None:
        if self._on_event is not None:
            self._on_event(event)
