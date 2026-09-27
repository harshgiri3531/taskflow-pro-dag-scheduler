import pytest
from app.engine.graph import Graph
from app.engine.scheduler import compute_schedule


def test_direct_cycle_rejected():
    g = Graph()
    g.add_edge("A", "B")
    would, path = g.would_create_cycle("B", "A")
    assert would is True


def test_indirect_cycle_rejected():
    g = Graph()
    g.add_edge("A", "B")
    g.add_edge("B", "C")
    would, path = g.would_create_cycle("C", "A")
    assert would is True


def test_self_loop_rejected():
    g = Graph()
    g.add_node("A")
    would, _ = g.would_create_cycle("A", "A")
    assert would is True


def test_valid_edge_not_flagged():
    g = Graph()
    g.add_edge("A", "B")
    would, _ = g.would_create_cycle("A", "C")
    assert would is False


def test_diamond_delay_counted_once():
    g = Graph()
    g.add_edge("A", "B")
    g.add_edge("A", "C")
    g.add_edge("B", "D")
    g.add_edge("C", "D")
    durations = {"A": 2, "B": 5, "C": 1, "D": 3}
    done = {"A": True, "B": False, "C": False, "D": False}
    sched = compute_schedule(g, durations, done)
    assert sched["D"].earliest_start == 7
    assert sched["D"].earliest_finish == 10


def test_critical_path_identified():
    g = Graph()
    g.add_edge("A", "B")
    g.add_edge("A", "C")
    g.add_edge("B", "D")
    g.add_edge("C", "D")
    durations = {"A": 2, "B": 5, "C": 1, "D": 3}
    done = {k: False for k in durations}
    sched = compute_schedule(g, durations, done)
    assert sched["B"].is_critical is True
    assert sched["C"].is_critical is False
    assert sched["C"].slack == pytest.approx(4)


def test_blocked_status():
    g = Graph()
    g.add_edge("A", "B")
    durations = {"A": 1, "B": 1}
    done = {"A": False, "B": False}
    sched = compute_schedule(g, durations, done)
    assert sched["B"].is_blocked is True
    done["A"] = True
    sched2 = compute_schedule(g, durations, done)
    assert sched2["B"].is_blocked is False
