"""تست‌های خوشه‌بندي headless: ساعت شبیه‌سازی، tick و رویدادها."""

from raft.core.cluster import Cluster


def test_tick_advances_simulated_clock():
    c = Cluster(5, seed=42)
    assert c.now == 0
    c.tick(100)
    assert c.now == 100
    c.tick(50)
    assert c.now == 150


def test_headless_tick_loses_no_message_accounting():
    """sent == delivered + dropped — هیچ RPCای در هوا ناپدید نمی‌شود."""
    events = []
    c = Cluster(5, seed=42, on_event=events.append)
    # چند پیام بین گره‌های سالم رد و بدل می‌کنیم
    import random

    rng = random.Random(1234)
    for _ in range(25):
        c.network.send(0, 1, "ping", now=c.now, rng=rng)
    c.tick(1000)
    sent = 25
    delivered = len([e for e in events if e["type"] == "delivered"])
    dropped = len([e for e in events if e["type"] == "dropped"])
    assert delivered + dropped == sent


def test_killed_node_does_not_tick_and_restart_recovers():
    c = Cluster(5, seed=42)
    c.kill(2)
    assert c.nodes[2].is_down
    c.tick(100)  # گرهٔ ۲ در حلقه مشارکت نمی‌کند (خطا نمی‌دهد)
    c.restart(2)
    assert not c.nodes[2].is_down


def test_network_link_down_blocks_delivery_end_to_end():
    events = []
    c = Cluster(5, seed=42, on_event=events.append)
    c.set_link(0, 1, False)
    import random

    rng = random.Random(5)
    c.network.send(0, 1, "x", now=c.now, rng=rng)
    c.tick(1000)
    assert not any(e["type"] == "delivered" for e in events)
    assert any(e["type"] == "dropped" for e in events)
