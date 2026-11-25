"""فیکسچرهای مشترک تست — همه با seed ثابت تا سوئیت همیشه بازتولیدپذیر و بی‌flaky باشد."""

import random

import pytest

from raft.core.cluster import Cluster

FIXED_SEED = 1234


@pytest.fixture
def seed() -> int:
    """seed ثابت برای تست‌هایی که مستقیماً با RNG کار می‌کنند."""
    return FIXED_SEED


@pytest.fixture
def rng(seed) -> random.Random:
    return random.Random(seed)


@pytest.fixture
def make_cluster():
    """فکتوری خوشه با seed دلخواه: ``make_cluster(5, seed=1234)``."""
    def _make(n: int = 5, seed: int = FIXED_SEED, on_event=None) -> Cluster:
        return Cluster(n, seed=seed, on_event=on_event)
    return _make


@pytest.fixture
def cluster(make_cluster) -> Cluster:
    """خوشه‌ی ۵ گره‌ای تمیز با seed ثابت."""
    return make_cluster(5, seed=FIXED_SEED)
