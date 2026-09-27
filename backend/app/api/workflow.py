from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Task, Dependency
from ..schemas import WorkflowOut, ScheduledTaskOut, DependencyOut
from ..engine.graph import Graph
from ..engine.scheduler import compute_schedule

router = APIRouter(prefix="/workflow", tags=["workflow"])


def build_graph_and_schedule(db: Session):
    """Reads current state from DB, builds a Graph, and computes the schedule.
    Rebuilding on every request is simple and fast enough at this project size."""
    tasks = db.query(Task).all()
    deps = db.query(Dependency).all()

    g = Graph()
    for t in tasks:
        g.add_node(t.id)
    for d in deps:
        g.add_edge(d.predecessor_id, d.successor_id)

    durations = {t.id: t.duration for t in tasks}
    done_status = {t.id: (t.column == "Done") for t in tasks}

    schedule = compute_schedule(g, durations, done_status)
    return tasks, deps, schedule


@router.get("", response_model=WorkflowOut)
def get_workflow(db: Session = Depends(get_db)):
    tasks, deps, schedule = build_graph_and_schedule(db)

    scheduled_tasks = []
    for t in tasks:
        s = schedule[t.id]
        scheduled_tasks.append(ScheduledTaskOut(
            id=t.id, title=t.title, description=t.description,
            duration=t.duration, column=t.column,
            earliest_start=s.earliest_start, earliest_finish=s.earliest_finish,
            slack=s.slack, is_critical=s.is_critical, is_blocked=s.is_blocked,
        ))

    dep_out = [DependencyOut.model_validate(d) for d in deps]
    return WorkflowOut(tasks=scheduled_tasks, dependencies=dep_out)
