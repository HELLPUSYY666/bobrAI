# bobrAI
```bash
cd bobrAI

docker-compose up --build
'''
# API будет доступно на http://localhost:8001
# RabbitMQ Management UI на http://localhost:15672 (guest/guest)
```

## Использование API

### Создать задачу
```bash
curl -X POST http://localhost:8001/tasks \
  -H "Content-Type: application/json" \
  -d '{"payload": "test task"}'

# Ответ: {"task_id": 1}
```

### Получить статус задачи
```bash
curl http://localhost:8001/tasks/1

# Ответ:
{
  "id": 1,
  "payload": "test task",
  "status": "done",
  "result": "processed: test task (1sec)",
  "created_at": "datetime.datetime",
  "updated_at": "datetime.datetime"
}
```

### Health check
```bash
curl http://localhost:8001/health
```

## Архитектура

```
┌─────────────┐      ┌──────────────┐      ┌──────────────┐
│   Client    │─────>│  FastAPI API │─────>│  PostgreSQL  │
└─────────────┘      └──────────────┘      └──────────────┘
                            │
                            │ publish
                            ▼
                     ┌──────────────┐
                     │   RabbitMQ   │
                     └──────────────┘
                            │
                            │ consume
                            ▼
                     ┌──────────────┐      ┌──────────────┐
                     │    Worker    │─────>│  PostgreSQL  │
                     └──────────────┘      └──────────────┘
```

## Технические решения

### 1. Почему выбрал RabbitMQ

1. **Простота для данной задачи**: 
   - RabbitMQ легче настроить и поддерживать
   - Нет нужны в формировании больших батчей для передачи их
   - Чаше использовал кролика 

2. **Гарантии доставки**:
   - кролик гарантировано доставит сообщение 

3. **Особенности задачи**:
   - Нам нужна очередь задачек, а не ивент стриминг
   - Не требуется повторения задачек их реплей
   - Важна гарантия обработки каждой задачки ровно один раз

**Когда стоило бы выбрать Kafka:**
- Высокая нагрузка много сообщений + они большие
- Нужен event sourcing или event streaming
- Множество consumers с разной логикой

### 2. Как масштабировать решение

#### Горизонтальное масштабирование воркеров
```bash
# Запустить 5 воркеров
docker-compose up --scale worker=5
```

**Преимущества:**
- RabbitMQ автоматически распределит задачи между воркерами
- Prefetch count = 1 гарантирует равномерное распределение

#### Вертикальное масштабирование
- **PostgreSQL**: Connection pooling 
- **RabbitMQ**: Кластеризация (3+ ноды)
- **API**: Несколько инстансов за load balancer (nginx/traefik)

#### Оптимизации для продакшена
1. **Batch processing**: Обрабатывать задачи пачками (если позволяет логика)(тут возможно лучше кафку если данных много)
2. **Priority queues**: Разные очереди для разных приоритетов задач
3. **Мониторинг**: Prometheus + Grafana для метрик, ELK для логов
4. **Кэширование**: Redis для статусов часто запрашиваемых задач
5. **Дисковери**: Сделать api gateway если много сервисов на каждый запрос от клиента уникальный uuid
6. **Троттлинг**: Добавить троттлинг в gateway можно и сюда чтобы защитться от додос атак 

#### Архитектура для высоких нагрузок

```
                    ┌──────────────┐
                    │ Load Balancer│
                    └──────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │  API #1  │    │  API #2  │    │  API #3  │
    └──────────┘    └──────────┘    └──────────┘
           │               │               │
           └───────────────┼───────────────┘
                           ▼
                  ┌─────────────────┐
                  │  RabbitMQ Cluster │
                  │   (3 nodes)     │
                  └─────────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ Worker 1 │    │ Worker 2 │    │ Worker N │
    └──────────┘    └──────────┘    └──────────┘
           │               │               │
           └───────────────┼───────────────┘
                           ▼
                  ┌─────────────────┐
                  │   PostgreSQL    │
                  │  (PgBouncer)    │
                  │                 │
                  └─────────────────┘
```

### 3. Потенциальные точки отказа

#### Текущие проблемы:

1. **Single Point of Failure (SPOF)**:
   - PostgreSQL в single-node режиме
   - RabbitMQ в single-node режиме
   - При падении любого сервиса вся система останавливается


2. **Переполнение очереди**:
   - Если воркеры не справляются очередь может бесконечно расти
   - Нет лимитов на очередь

3. **Memory leaks в воркерах**:
   - Long-running процессы могут накапливать memory
   - Нет автоматического перезапуска воркеров

4. **Отсутствие retry логики**:
   - Если задача failed она просто помечается как failed
   - Нет механизма повторной попытки

5. **Database connection exhaustion**:
   - Нет ограничения на количество одновременных connections

7. **Нет мониторинга и алертинга**:
   - Невозможно отследить проблемы в реальном времени
   - Нет метрик по производительности

#### Решения:

1. **High Availability**:
   - PostgreSQL: PGBouncer 
   - RabbitMQ: Кластер из 3+ нод с mirrored queues
   - Kubernetes для оркестрации с auto-restart

2. **Данные**:
   -  Делать бэкапы + репликация

3. **Защита от перегрузки**:
   - Max queue length в RabbitMQ
   - Троттлинг 

4. **Retry механизм**:
   - Max retry count

5. **Мониторинг**:
   - Хелс чеки для всех компонентов
   - Prometheus metrics 
   - Alertmanager (Телеграмм, почта) вроде можно в графане настроить такое 

### 4. Что улучшить для продакшена

#### Критичные улучшения:

1. **Observability** (мониторинг и логирование):
   ```python
   import structlog
   
   from opentelemetry import trace
   
   from prometheus_client import Counter, Histogram
   ```

2. **Retry механизм с экспоненциальной задержкой**:
   ```python
   from tenacity import retry, stop_after_attempt, wait_exponential
   
   @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
   async def process_task_with_retry(task_id):
       pass
   ```

3. **Валидация и санитизация payload**:
   ```python
   class TaskCreateRequest(BaseModel):
       payload: str = Field(..., min_length=1, max_length=10000)
       priority: int = Field(default=0, ge=0, le=10)
   ```

4. **Authentication & Authorization**:
Api-gateway + auth-service

6. **Task timeout**:
   ```python
   import asyncio
   
   try:
       await asyncio.wait_for(process_task(task_id), timeout=300)
   except asyncio.TimeoutError:
       pass
   ```



7. **API versioning**:
    ```python
    app.include_router(tasks_router, prefix="/api/v1")
    ```

8. **Database migrations в CI/CD**:
    ```yaml
    - name: Run migrations
      run: alembic upgrade head
    ```
    или инит контейнеры 

9. **Health checks для всех компонентов**:
    ```python
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "checks": {...}}
    ```

## Структура проекта

```
bobrAI/
├── src/
│   ├── alembic/              
│   │   ├── versions/
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── controllers/          
│   │   ├── rabbitmq.py      
│   │   └── worker.py        
│   ├── db/                   
│   │   ├── models.py        
│   │   ├── database.py      
│   │   └── repository.py    
│   ├── views/                
│   │   ├── routes.py        
│   │   └── schemas.py       
│   ├── config.py            
│   └── main.py              
├── docker-compose.yml        
├── Dockerfile               
├── pyproject.toml           
├── alembic.ini             
└── README.md               
```

## Технологический стек

- **FastAPI**;
- **SQLAlchemy**; 
- **Alembic**;
- **RabbitMQ**; 
- **PostgreSQL**;
- **aio-pika**; 
- **asyncpg**;
- **Pydantic**;

## Тестирование

```bash
# Запустить тесты
docker-compose run --rm api pytest
```

## Полезные команды

```bash
# Подключение к БД
docker-compose exec postgres psql -U postgres -d taskdb

# Создание новой миграции
docker-compose exec api alembic revision --autogenerate -m "description"

# Применение миграций
docker-compose exec api alembic upgrade head
```


## Автор
Polevchshikov Zakariya
