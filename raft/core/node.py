"""گرهٔ Raft — در تسک ۲٫۱ فقط اسکلت؛ منطق کامل در تسک ۲٫۳ و فازهای ۳–۵."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # جلوگیری از import چرخشی در زمان اجرا
    from .cluster import Cluster


class Role(str, Enum):
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"


class RaftNode:
    """یک گرهٔ Raft.

    مرز حالت:
      - persisted (بعد از kill/restart می‌ماند): ``current_term``, ``voted_for``, ``log``
      - volatile (با restart ریست می‌شود): ``commit_index``, ``last_applied`` و تایمرها
    """

    def __init__(self, node_id: int, cluster: "Cluster", rng) -> None:
        self.node_id = node_id
        self.cluster = cluster
        self.rng = rng

        # --- persisted ---
        self.current_term = 0
        self.voted_for: int | None = None
        self.log: list[dict] = []  # هر ورودی: {"term": int, "command": str}

        # --- volatile ---
        self.commit_index = 0
        self.last_applied = 0
        self.role = Role.FOLLOWER
        self.is_down = False

    # ---------- چرخهٔ عمر ----------
    def reset_volatile(self) -> None:
        self.commit_index = 0
        self.last_applied = 0
        self.role = Role.FOLLOWER

    @property
    def is_leader(self) -> bool:
        return self.role is Role.LEADER

    # ---------- حلقه ----------
    def tick(self, dt_ms: float) -> None:
        if self.is_down:
            return
        # تایمرهای انتخابات/heartbeat در فاز ۳ اضافه می‌شوند.

    def receive(self, envelope: Any) -> None:
        if self.is_down:
            return
        # پردازش RPC در تسک ۲٫۳ و فاز ۳ اضافه می‌شود.
