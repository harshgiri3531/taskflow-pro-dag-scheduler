from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Task, Dependency
from ..schemas import DependencyCreate, DependencyOut
from ..engine.graph import Graph

router = APIRouter(prefix="/dependencies", tags=["dependencies"])


@router.post("", response_model=DependencyOut)
def create_dependency(payload: DependencyCreate, db: Session = Depends(get_db)):
    pred = db.query(Task).filter(Task.id == payload.predecessor_id).first()
    succ = db.query(Task).filter(Task.id == payload.successor_id).first()
    if not pred or not succ:
        raise HTTPException(status_code=404, detail="Task not found")
    if pred.id == succ.id:
        raise HTTPException(status_code=400, detail="A task cannot depend on itself")

    existing = db.query(Dependency).filter(
        Dependency.predecessor_id == pred.id,
        Dependency.successor_id == succ.id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Dependency already exists")

    g = Graph()
    for t in db.query(Task).all():
        g.add_node(t.id)
    for d in db.query(Dependency).all():
        g.add_edge(d.predecessor_id, d.successor_id)

    would_cycle, path = g.would_create_cycle(pred.id, succ.id)
    if would_cycle:
        raise HTTPException(
            status_code=400,
            detail=f"This dependency would create a cycle: {' -> '.join(path)}",
        )

    dep = Dependency(predecessor_id=pred.id, successor_id=succ.id, source="manual")
    db.add(dep)
    db.commit()
    db.refresh(dep)
    return dep


@router.delete("/{dependency_id}")
def delete_dependency(dependency_id: str, db: Session = Depends(get_db)):
    dep = db.query(Dependency).filter(Dependency.id == dependency_id).first()
    if not dep:
        raise HTTPException(status_code=404, detail="Dependency not found")
    db.delete(dep)
    db.commit()
    return {"deleted": dependency_id}
