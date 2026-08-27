import sqlite3
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI(
    title="Task API with SQLite",
    version="2.0",
    description="Persistent CRUD API backed by SQLite"
)

DB_PATH = "tasks.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done BOOLEAN NOT NULL DEFAULT 0
            )
        """)
        cursor = conn.execute("SELECT COUNT(*) FROM tasks")
        if cursor.fetchone()[0] == 0:
            sample_tasks = [
                ("Buy groceries", 0),
                ("Review PRs", 1),
                ("Walk the dog", 0)
            ]
            conn.executemany("INSERT INTO tasks (title, done) VALUES (?, ?)", sample_tasks)

init_db()

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1)

class TaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1)
    done: bool | None = None

@app.get("/")
def root():
    return {"name": "Task API", "version": "2.0", "storage": "sqlite"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/tasks")
def get_tasks():
    with get_db() as conn:
        rows = conn.execute("SELECT id, title, done FROM tasks").fetchall()
        return [{"id": r["id"], "title": r["title"], "done": bool(r["done"])} for r in rows]

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    with get_db() as conn:
        row = conn.execute("SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}

@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate):
    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    with get_db() as conn:
        cursor = conn.execute("INSERT INTO tasks (title, done) VALUES (?, 0)", (title,))
        new_id = cursor.lastrowid
        return {"id": new_id, "title": title, "done": False}

@app.put("/tasks/{task_id}")
def update_task(task_id: int, payload: TaskUpdate):
    if payload.title is None and payload.done is None:
        raise HTTPException(status_code=400, detail="Empty update payload")
    
    with get_db() as conn:
        row = conn.execute("SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")
        
        new_title = row["title"]
        new_done = row["done"]

        if payload.title is not None:
            stripped = payload.title.strip()
            if not stripped:
                raise HTTPException(status_code=400, detail="Title cannot be empty")
            new_title = stripped
        if payload.done is not None:
            new_done = int(payload.done)

        conn.execute("UPDATE tasks SET title = ?, done = ? WHERE id = ?", (new_title, new_done, task_id))
        return {"id": task_id, "title": new_title, "done": bool(new_done)}

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Task not found")
        return