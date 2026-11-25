"""گرهٔ Raft — ماشین حالت سه‌نقشی با مرز دقیق persisted/volatile.

در این تسک (۲٫۳): نقش‌ها، persisted/volatile، ``observe_term``،
``submit`` فقط روی Leader و ``receive`` با قانون طلایی (term کمتر ⇒ نادیده).
منطق انتخابات و复制 لاگ در فازهای ۳ و ۴ اضافه می‌شود.
"""

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

    # ---------- مرز persisted / volatile ----------
    def reset_volatile(self) -> None:
        """با restart: volatileها صفر و نقش follower می‌شود."""
        self.commit_index = 0
        self.last_applied = 0
        self.role = Role.FOLLOWER

    @property
    def is_leader(self) -> bool:
        return self.role is Role.LEADER

    @property
    def last_log_index(self) -> int:
        return len(self.log)  # ایندکس از ۱؛ ۰ یعنی sentinel

    @property
    def last_log_term(self) -> int:
        return self.log[-1]["term"] if self.log else 0

    # ---------- یکنوایی term و قانون طلایی ----------
    def observe_term(self, term: int) -> bool:
        """اگر ``term`` از ``current_term`` بزرگ‌تر بود، persist کن و True برگردان.

        هر جا پیامی با term بالاتر دیدیم (حتی به‌عنوان follower) باید این صدا زده شود.
        """
        if term > self.current_term:
            self.current_term = term
            self.voted_for = None
            self.role = Role.FOLLOWER
            return True
        return False

    # ---------- حلقه ----------
    def tick(self, dt_ms: float) -> None:
        if self.is_down:
            return
        # تایمرهای انتخابات/heartbeat در فاز ۳ اضافه می‌شوند.

    def receive(self, envelope: Any) -> None:
        if self.is_down:
            return
        msg = getattr(envelope, "payload", envelope)
        term = getattr(msg, "term", None)
        if term is None:
            return  # پیام بی‌term بی‌معنی است
        self.observe_term(term)  # قانون طلایی: term کمتر فقط دیده می‌شود، اثر نمی‌کند

    # ---------- کلاینت ----------
    def submit(self, command: str) -> int:
        """فقط روی Leader؛ دستور را به لاگ اضافه می‌کند و ایندکس آن را برمی‌گرداند."""
        if self.role is not Role.LEADER:
            raise RuntimeError("فقط Leader می‌تواند دستور بپذیرد")
        self.log.append({"term": self.current_term, "command": command})
        return len(self.log)
