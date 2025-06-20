from typing import Annotated

from fastapi import APIRouter, Depends

from app.models.schemas import STask, STaskAdd, STaskId
from app.repository import TaskRepository

router = APIRouter(tags=["Tasks"])


@router.get("/")
async def root():
    return {"message": "Hello World"}


@router.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@router.post("/tasks")
async def add_task(task: Annotated[STaskAdd, Depends()]) -> STaskId:
    task_id = await TaskRepository.add_one(task)
    return STaskId(**{"ok": True, "task_id": task_id})


@router.get("/tasks")
async def get_tasks() -> list[STask]:
    tasks = await TaskRepository.find_all()
    return tasks
