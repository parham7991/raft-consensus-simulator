"""تست‌های گرهٔ Raft و ماشین حالت — مرز persisted/volatile و یکنوایی term."""

import pytest

from raft.core.messages import AppendEntries, RequestVote
from raft.core.node import Role
from raft.core.state_machine import StateMachine


class TestPersistedVolatileBoundary:
    def test_initial_role_is_follower(self, cluster):
        assert cluster.nodes[0].role is Role.FOLLOWER
        assert cluster.nodes[0].current_term == 0
        assert cluster.nodes[0].voted_for is None
        assert cluster.nodes[0].log == []

    def test_persisted_state_survives_kill_restart(self, cluster):
        node = cluster.nodes[0]
        node.current_term = 7
        node.voted_for = 3
        node.log = [{"term": 6, "command": "SET x 1"}, {"term": 7, "command": "SET y 2"}]
        cluster.kill(0)
        cluster.restart(0)
        assert node.current_term == 7
        assert node.voted_for == 3
        assert [e["command"] for e in node.log] == ["SET x 1", "SET y 2"]

    def test_volatile_state_resets_on_restart(self, cluster):
        node = cluster.nodes[0]
        node.commit_index = 5
        node.last_applied = 5
        cluster.kill(0)
        assert node.commit_index == 0 and node.last_applied == 0
        node.commit_index = 9  # حتی اگر دوباره پر شود...
        cluster.restart(0)     # ...با restart بعدی باز صفر می‌شود
        assert node.commit_index == 0 and node.last_applied == 0
        assert node.role is Role.FOLLOWER


class TestTermMonotonicity:
    def test_term_never_decreases(self, cluster):
        node = cluster.nodes[0]
        node.observe_term(5)
        assert node.observe_term(3) is False
        assert node.current_term == 5
        assert node.observe_term(9) is True
        assert node.current_term == 9

    def test_higher_term_clears_vote_and_steps_down(self, cluster):
        node = cluster.nodes[0]
        node.current_term = 4
        node.voted_for = 1
        node.role = Role.LEADER
        node.observe_term(6)
        assert node.role is Role.FOLLOWER
        assert node.voted_for is None

    def test_equal_term_keeps_vote(self, cluster):
        node = cluster.nodes[0]
        node.current_term = 4
        node.voted_for = 2
        assert node.observe_term(4) is False
        assert node.voted_for == 2


class TestSubmitAndLog:
    def test_submit_raises_when_not_leader(self, cluster):
        with pytest.raises(RuntimeError):
            cluster.nodes[0].submit("SET x 1")

    def test_submit_on_leader_appends_and_returns_index(self, cluster):
        node = cluster.nodes[0]
        node.role = Role.LEADER
        node.current_term = 3
        first = node.submit("SET a 1")
        second = node.submit("SET b 2")
        assert (first, second) == (1, 2)  # ایندکس لاگ از ۱
        assert [e["term"] for e in node.log] == [3, 3]
        assert node.last_log_index == 2
        assert node.last_log_term == 3

    def test_empty_log_has_sentinel_term_zero(self, cluster):
        node = cluster.nodes[0]
        assert node.last_log_index == 0
        assert node.last_log_term == 0


class TestReceiveTermHandling:
    def test_receive_steps_down_on_higher_term(self, cluster):
        node = cluster.nodes[0]
        node.role = Role.LEADER
        node.current_term = 5
        env = cluster.network.send(1, 0, RequestVote(term=6, candidate_id=1,
                                                     last_log_index=0, last_log_term=0),
                                   now=cluster.now, rng=node.rng)
        node.receive(env)
        assert node.current_term == 6
        assert node.role is Role.FOLLOWER

    def test_receive_ignores_lower_term_message(self, cluster):
        node = cluster.nodes[0]
        node.current_term = 7
        env = cluster.network.send(1, 0, AppendEntries(term=5, leader_id=1,
                                                       prev_log_index=0, prev_log_term=0,
                                                       entries=[], leader_commit=0),
                                   now=cluster.now, rng=node.rng)
        node.receive(env)
        assert node.current_term == 7


class TestStateMachine:
    def test_set_get_del(self):
        sm = StateMachine()
        sm.apply("SET color red")
        assert sm.get("color") == "red"
        sm.apply("DEL color")
        assert sm.get("color") is None

    def test_applied_log_keeps_order(self):
        sm = StateMachine()
        sm.apply("SET a 1")
        sm.apply("SET b 2")
        sm.apply("DEL a")
        assert sm.applied_log == ["SET a 1", "SET b 2", "DEL a"]

    def test_get_command_does_not_change_kv(self):
        sm = StateMachine()
        sm.apply("SET k v")
        sm.apply("GET k")
        assert sm.get("k") == "v"

    def test_reapplying_same_entry_is_harmless(self):
        sm = StateMachine()
        sm.apply("SET k v")
        sm.apply("SET k v")  # idempotent برای SET
        assert sm.get("k") == "v"
