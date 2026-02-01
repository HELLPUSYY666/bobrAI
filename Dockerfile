FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY src ./src
COPY alembic.ini ./
COPY entrypoint.sh ./

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    fastapi>=0.109.0 \
    uvicorn[standard]>=0.27.0 \
    sqlalchemy>=2.0.25 \
    psycopg2-binary>=2.9 \
    pytest>=8.0 \
    pytest-asyncio>=0.23 \
    alembic>=1.13.1 \
    httpx>=0.26 \
    aiosqlite>=0.20 \
    pytest-asyncio \
    asyncpg>=0.29.0 \
    pydantic>=2.5.3 \
    pydantic-settings>=2.1.0 \
    aio-pika>=9.4.0 \
    python-dotenv>=1.0.0

RUN chmod +x entrypoint.sh

EXPOSE 8001

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]
