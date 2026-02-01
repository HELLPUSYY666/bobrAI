from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Task, TaskStatus


class TaskRepository:
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_task(self, payload: str) -> Task:
        task = Task(payload=payload, status=TaskStatus.PENDING)
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task
    
    async def get_task(self, task_id: int) -> Task | None:
        result = await self.session.execute(
            select(Task).where(Task.id == task_id)
        )
        return result.scalar_one_or_none()
    
    async def update_task_status(
        self, 
        task_id: int, 
        status: TaskStatus,
        result: str | None = None
    ) -> None:
        values = {"status": status}
        if result is not None:
            values["result"] = result
        
        await self.session.execute(
            update(Task)
            .where(Task.id == task_id)
            .values(**values)
        )
        await self.session.commit()
