"""Forward/backward pass scheduling on top of Graph. Pure Python."""
from dataclasses import dataclass
from typing import Dict
from .graph import Graph


@dataclass
class TaskSchedule:
    task_id: str
    duration: float
    earliest_start: float = 0.0
    earliest_finish: float = 0.0
    latest_start: float = 0.0
    latest_finish: float = 0.0
    slack: float = 0.0
    is_critical: bool = False
    is_blocked: bool = False


def compute_schedule(graph: Graph, durations: Dict[str, float],
                      done_status: Dict[str, bool]) -> Dict[str, TaskSchedule]:
    """
    Forward pass: earliest_start = max(earliest_finish of all predecessors), 0 if none.
    This prevents diamond-dependency double counting: each node's earliest_start is
    computed exactly once, from already-finalized predecessors, using MAX not SUM.
    Backward pass: latest_finish from project end backwards -> slack -> critical path.
    Blocked flag: any predecessor not marked Done.
    """
    order = graph.topological_order()  # raises CycleError if invalid
    schedules: Dict[str, TaskSchedule] = {
        tid: TaskSchedule(task_id=tid, duration=durations.get(tid, 0))
        for tid in graph.nodes
    }

    for tid in order:
        preds = graph.reverse.get(tid, set())
        es = max((schedules[p].earliest_finish for p in preds), default=0.0)
        schedules[tid].earliest_start = es
        schedules[tid].earliest_finish = es + schedules[tid].duration
        schedules[tid].is_blocked = any(not done_status.get(p, False) for p in preds)

    project_end = max((s.earliest_finish for s in schedules.values()), default=0.0)

    for tid in reversed(order):
        succs = graph.edges.get(tid, set())
        lf = min((schedules[s].latest_start for s in succs), default=project_end)
        schedules[tid].latest_finish = lf
        schedules[tid].latest_start = lf - schedules[tid].duration
        schedules[tid].slack = schedules[tid].latest_start - schedules[tid].earliest_start
        schedules[tid].is_critical = schedules[tid].slack <= 1e-9

    return schedules


def recompute_affected(graph: Graph, durations: Dict[str, float],
                        done_status: Dict[str, bool], changed_node: str
                        ) -> Dict[str, TaskSchedule]:
    """Only the changed node and its descendants are returned as 'affected',
    even though the full schedule is recomputed (O(V+E), fast enough here)."""
    affected = graph.descendants(changed_node) | {changed_node}
    full = compute_schedule(graph, durations, done_status)
    return {tid: sched for tid, sched in full.items() if tid in affected}
