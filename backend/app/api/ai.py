from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Task, Dependency, Suggestion
from ..schemas import SuggestionOut
from ..engine.graph import Graph
from ..services.llm_client import suggest_dependencies
from ..services.suggestion_validator import validate_suggestions

router = APIRouter(prefix="/suggestions", tags=["ai"])


@router.post("/generate/{task_id}", response_model=list[SuggestionOut])
def generate_suggestions(task_id: str, db: Session = Depends(get_db)):
    new_task = db.query(Task).filter(Task.id == task_id).first()
    if not new_task:
        raise HTTPException(status_code=404, detail="Task not found")

    all_tasks = db.query(Task).all()
    task_dicts = [{"id": t.id, "title": t.title, "description": t.description} for t in all_tasks]

    raw = suggest_dependencies(
        {"id": new_task.id, "title": new_task.title, "description": new_task.description},
        task_dicts,
    )

    g = Graph()
    for t in all_tasks:
        g.add_node(t.id)
    for d in db.query(Dependency).all():
        g.add_edge(d.predecessor_id, d.successor_id)

    existing_ids = {t.id for t in all_tasks}
    valid = validate_suggestions(raw, task_id, existing_ids, g)

    saved = []
    for v in valid:
        existing = db.query(Suggestion).filter(
            Suggestion.predecessor_id == v["predecessor_id"],
            Suggestion.successor_id == v["successor_id"],
            Suggestion.status == "pending",
        ).first()
        if existing:
            saved.append(existing)
            continue
        sug = Suggestion(
            predecessor_id=v["predecessor_id"],
            successor_id=v["successor_id"],
            reason=v["reason"],
            confidence=v["confidence"],
            status="pending",
        )
        db.add(sug)
        db.commit()
        db.refresh(sug)
        saved.append(sug)

    return saved


@router.get("/pending/{task_id}", response_model=list[SuggestionOut])
def get_pending_suggestions(task_id: str, db: Session = Depends(get_db)):
    return db.query(Suggestion).filter(
        Suggestion.successor_id == task_id, Suggestion.status == "pending"
    ).all()


@router.post("/{suggestion_id}/accept")
def accept_suggestion(suggestion_id: str, db: Session = Depends(get_db)):
    sug = db.query(Suggestion).filter(Suggestion.id == suggestion_id).first()
    if not sug:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    g = Graph()
    for t in db.query(Task).all():
        g.add_node(t.id)
    for d in db.query(Dependency).all():
        g.add_edge(d.predecessor_id, d.successor_id)

    would_cycle, path = g.would_create_cycle(sug.predecessor_id, sug.successor_id)
    if would_cycle:
        sug.status = "dismissed"
        db.commit()
        raise HTTPException(status_code=400, detail=f"Would create a cycle: {' -> '.join(path)}")

    dep = Dependency(predecessor_id=sug.predecessor_id, successor_id=sug.successor_id, source="ai")
    db.add(dep)
    sug.status = "accepted"
    db.commit()
    return {"accepted": suggestion_id}


@router.post("/{suggestion_id}/dismiss")
def dismiss_suggestion(suggestion_id: str, db: Session = Depends(get_db)):
    sug = db.query(Suggestion).filter(Suggestion.id == suggestion_id).first()
    if not sug:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    sug.status = "dismissed"
    db.commit()
    return {"dismissed": suggestion_id}
