"""پیام‌های RPC Raft — فقط داده، بدون منطق (دقیقاً طبق مقاله‌ی Raft §5)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RequestVote:
    term: int
    candidate_id: int
    last_log_index: int
    last_log_term: int


@dataclass
class VoteResponse:
    term: int
    vote_granted: bool


@dataclass
class AppendEntries:
    term: int
    leader_id: int
    prev_log_index: int
    prev_log_term: int
    entries: list[dict] = field(default_factory=list)
    leader_commit: int = 0


@dataclass
class AppendResponse:
    term: int
    success: bool
    match_index: int = 0
