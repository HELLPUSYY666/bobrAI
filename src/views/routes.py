from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.controllers.rabbitmq import rabbitmq_client
from src.db.database import get_db
from src.db.repository import TaskRepository
from src.views.schemas import TaskCreateRequest, TaskCreateResponse, TaskResponse

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskCreateResponse, status_code=201)
async def create_task(
    request: TaskCreateRequest,
    db: AsyncSession = Depends(get_db)
) -> TaskCreateResponse:
    repo = TaskRepository(db)
    
    task = await repo.create_task(request.payload)
    
    await rabbitmq_client.publish_task(task.id, task.payload)
    
    return TaskCreateResponse(task_id=task.id)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
) -> TaskResponse:
    repo = TaskRepository(db)
    task = await repo.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskResponse.model_validate(task)
