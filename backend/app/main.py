from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db import Base, engine
from .api import tasks, dependencies, workflow, ai

app = FastAPI(title="TaskFlow Pro API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "null",  # allows opening frontend/index.html directly as a file:// URL
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(tasks.router)
app.include_router(dependencies.router)
app.include_router(workflow.router)
app.include_router(ai.router)


@app.get("/")
def root():
    return {"status": "TaskFlow Pro API running"}
