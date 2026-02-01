import asyncio
import json
import logging
from typing import Callable
from aio_pika import connect_robust, Message, Connection, Channel
from aio_pika.abc import AbstractIncomingMessage

from src.config import settings

logger = logging.getLogger(__name__)


class RabbitMQClient:
    
    def __init__(self):
        self.connection: Connection | None = None
        self.channel: Channel | None = None
    
    async def connect(self) -> None:
        max_retries = 5
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                self.connection = await connect_robust(settings.rabbitmq_url)
                self.channel = await self.connection.channel()
                await self.channel.declare_queue(
                    settings.rabbitmq_queue,
                    durable=True
                )
                
                logger.info("Successfully connected to RabbitMQ")
                return
            except Exception as e:
                logger.warning(
                    f"Failed to connect to RabbitMQ (attempt {attempt + 1}/{max_retries}): {e}"
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                else:
                    raise
    
    async def disconnect(self) -> None:
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("Disconnected from RabbitMQ")
    
    async def publish_task(self, task_id: int, payload: str) -> None:
        if not self.channel:
            raise RuntimeError("RabbitMQ channel not initialized")
        
        message_body = json.dumps({
            "task_id": task_id,
            "payload": payload
        })
        
        message = Message(
            body=message_body.encode(),
            delivery_mode=2,  
        )
        
        await self.channel.default_exchange.publish(
            message,
            routing_key=settings.rabbitmq_queue,
        )
        
        logger.info(f"Published task {task_id} to queue")
    
    async def consume_tasks(self, callback: Callable) -> None:
        if not self.channel:
            raise RuntimeError("RabbitMQ channel not initialized")
        
        queue = await self.channel.declare_queue(
            settings.rabbitmq_queue,
            durable=True
        )
        
        await self.channel.set_qos(prefetch_count=1)
        
        logger.info(f"Starting to consume from queue: {settings.rabbitmq_queue}")
        
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    await callback(message)


rabbitmq_client = RabbitMQClient()
