from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI(
    title="Task API",
    version="1.0",
    description="In-memory CRUD API for managing tasks"
)

tasks = [
    {"id": 1, "title": "Buy groceries", "done": False},
    {"id": 2, "title": "Review PRs", "done": True},
    {"id": 3, "title": "Walk the dog", "done": False},
]

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1)

class TaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1)
    done: bool | None = None

@app.get("/")
def root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/tasks")
def get_tasks():
    return tasks

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    for item in tasks:
        if item["id"] == task_id:
            return item
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate):
    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    new_id = max([t["id"] for t in tasks], default=0) + 1
    new_task = {"id": new_id, "title": title, "done": False}
    tasks.append(new_task)
    return new_task

@app.put("/tasks/{task_id}")
def update_task(task_id: int, payload: TaskUpdate):
    if payload.title is None and payload.done is None:
        raise HTTPException(status_code=400, detail="Empty update payload")
    for item in tasks:
        if item["id"] == task_id:
            if payload.title is not None:
                title = payload.title.strip()
                if not title:
                    raise HTTPException(status_code=400, detail="Title cannot be empty")
                item["title"] = title
            if payload.done is not None:
                item["done"] = payload.done
            return item
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    for idx, item in enumerate(tasks):
        if item["id"] == task_id:
            tasks.pop(idx)
            return
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")