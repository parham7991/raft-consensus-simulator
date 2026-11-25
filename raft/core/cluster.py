"""خوشهٔ شبیه‌سازی — ساعت ``now``، حلقهٔ ``tick`` و هماهنگی شبکه و گره‌ها."""

from __future__ import annotations

import random
from typing import Callable

from .network import Network
from .node import RaftNode

EventCallback = Callable[[dict], None]


class Cluster:
    def __init__(self, n: int = 5, seed: int = 42, on_event: EventCallback | None = None) -> None:
        if n < 1:
            raise ValueError("تعداد گره‌ها باید حداقل ۱ باشد")
        self.now = 0.0
        self._listeners: list[EventCallback] = []
        if on_event is not None:
            self._listeners.append(on_event)
        self.network = Network(on_event=self._emit,
                               is_reachable=lambda _a, b: not self.nodes[b].is_down)
        self.nodes = [
            RaftNode(node_id=i, cluster=self, rng=random.Random(seed + 1000 + i))
            for i in range(n)
        ]

    # ---------- رویدادها ----------
    def on_event(self, cb: EventCallback) -> None:
        self._listeners.append(cb)

    def _emit(self, event: dict) -> None:
        for cb in list(self._listeners):
            cb(event)

    # ---------- دستورات زمان ----------
    def tick(self, dt_ms: float) -> None:
        if dt_ms < 0:
            raise ValueError("dt_ms نمی‌تواند منفی باشد")
        self.now += dt_ms
        for node in self.nodes:
            if not node.is_down:
                node.tick(dt_ms)
        for env in self.network.deliver_due(self.now):
            target = self.nodes[env.to_id]
            if not target.is_down:
                target.receive(env)

    # ---------- خرابی ----------
    def kill(self, node_id: int) -> None:
        node = self.nodes[node_id]
        node.is_down = True
        node.reset_volatile()
        self._emit({"type": "down", "node_id": node_id})

    def restart(self, node_id: int) -> None:
        node = self.nodes[node_id]
        node.is_down = False
        node.reset_volatile()
        self._emit({"type": "up", "node_id": node_id})

    def set_link(self, i: int, j: int, up: bool) -> None:
        self.network.set_link(i, j, up)

    # ---------- دسترسی ----------
    def majority(self) -> int:
        return len(self.nodes) // 2 + 1

    def alive_nodes(self) -> list[RaftNode]:
        return [n for n in self.nodes if not n.is_down]
