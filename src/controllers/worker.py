import asyncio
import json
import logging
import random
from aio_pika.abc import AbstractIncomingMessage

from src.controllers.rabbitmq import rabbitmq_client
from src.db.database import get_db_context
from src.db.models import TaskStatus
from src.db.repository import TaskRepository

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def process_task(message: AbstractIncomingMessage) -> None:
    try:
        data = json.loads(message.body.decode())
        task_id = data["task_id"]
        payload = data["payload"]
        
        logger.info(f"Processing task {task_id} with payload: {payload[:50]}...")
        
        async with get_db_context() as db:
            repo = TaskRepository(db)
            
            await repo.update_task_status(task_id, TaskStatus.PROCESSING)
            logger.info(f"Task {task_id} status updated to PROCESSING")
            
            processing_time = random.uniform(2, 5)
            await asyncio.sleep(processing_time)
            
            success = random.random() > 0.1
            
            if success:
                result = f"Processed: {payload.upper()} (took {processing_time:.2f}s)"
                await repo.update_task_status(
                    task_id, 
                    TaskStatus.DONE,
                    result=result
                )
                logger.info(f"Task {task_id} completed successfully")
            else:
                error_message = f"Processing failed after {processing_time:.2f}s"
                await repo.update_task_status(
                    task_id,
                    TaskStatus.FAILED,
                    result=error_message
                )
                logger.warning(f"Task {task_id} failed: {error_message}")
    
    except Exception as e:
        logger.error(f"Error processing task: {e}", exc_info=True)
        
        try:
            async with get_db_context() as db:
                repo = TaskRepository(db)
                await repo.update_task_status(
                    task_id,
                    TaskStatus.FAILED,
                    result=f"Error: {str(e)}"
                )
        except Exception as db_error:
            logger.error(f"Failed to update task status: {db_error}")


async def run_worker():
    logger.info("Starting task worker...")
    
    try:
        await rabbitmq_client.connect()
        
        await rabbitmq_client.consume_tasks(process_task)
    
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker error: {e}", exc_info=True)
    finally:
        await rabbitmq_client.disconnect()


if __name__ == "__main__":
    asyncio.run(run_worker())
