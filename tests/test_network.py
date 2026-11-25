"""تست‌های لایهٔ شبکه: تحویل با تأخیر، لینک‌های قطع/وصل، ترتیب تحویل."""

import random

import pytest

from raft.core.network import Network


def quiet_event():
    return []


class TestSendAndDeliver:
    def test_message_not_delivered_before_deliver_at(self):
        net = Network()
        rng = random.Random(42)
        net.send(0, 1, "ping", now=100, rng=rng)
        delivered = net.deliver_due(100)  # قبل از هر deliver_atی
        assert delivered == []

    def test_message_delivered_at_deliver_at(self):
        net = Network()
        rng = random.Random(42)
        net.send(0, 1, "ping", now=100, rng=rng)
        # تأخیر حداکثر ۲۰ میلی‌ثانیه است؛ در t=120 باید حتماً رسیده باشد
        delivered = net.deliver_due(120)
        assert len(delivered) == 1
        env = delivered[0]
        assert env.from_id == 0 and env.to_id == 1
        assert env.payload == "ping"
        assert env.deliver_at >= 105  # حداقل تأخیر ۵
        assert net.deliver_due(1000) == []  # بعد از تحویل، چیزی نمانده

    def test_delay_within_bounds(self):
        net = Network()
        rng = random.Random(1234)
        delays = []
        for _ in range(200):
            net.send(0, 1, "x", now=0, rng=rng)
            env = net.deliver_due(1000)[-1]
            delays.append(env.deliver_at - env.sent_at)
        assert all(5.0 <= d < 20.0 for d in delays)

    def test_delivered_in_deliver_at_order_not_send_order(self):
        net = Network()
        rng = random.Random(7)
        for _ in range(30):
            net.send(0, 1, "x", now=0, rng=rng)
        delivered = net.deliver_due(1000)
        times = [e.deliver_at for e in delivered]
        assert times == sorted(times)


class TestLinks:
    def test_link_down_drops_message_and_emits_event(self):
        events = []
        net = Network(on_event=events.append)
        rng = random.Random(42)
        net.set_link(0, 1, False)
        net.send(0, 1, "ping", now=0, rng=rng)
        delivered = net.deliver_due(1000)
        assert delivered == []
        dropped = [e for e in events if e["type"] == "dropped"]
        assert len(dropped) == 1
        assert dropped[0]["from_id"] == 0 and dropped[0]["to_id"] == 1

    def test_set_link_is_symmetric(self):
        net = Network()
        net.set_link(1, 2, False)
        assert net.link_up(1, 2) is False
        assert net.link_up(2, 1) is False

    def test_link_up_restores_delivery(self):
        net = Network()
        rng = random.Random(9)
        net.set_link(0, 1, False)
        net.send(0, 1, "a", now=0, rng=rng)
        assert net.deliver_due(1000) == []
        net.set_link(0, 1, True)
        net.send(0, 1, "b", now=1000, rng=rng)
        delivered = net.deliver_due(2000)
        assert [e.payload for e in delivered] == ["b"]

    def test_pending_count_drops_after_delivery(self):
        net = Network()
        rng = random.Random(1)
        net.send(0, 1, "x", now=0, rng=rng)
        assert net.pending() == 1
        net.deliver_due(1000)
        assert net.pending() == 0
