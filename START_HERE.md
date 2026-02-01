cd /mnt/user-data/outputs/bobrAI && cat > START_HERE.md << 'EOF'
# START HERE - BOBR AI 


---


```bash
cd bobrAI

docker-compose up --build

curl -X POST http://localhost:8001/tasks \
  -H "Content-Type: application/json" \
  -d '{"payload": "Я точно хочу работать с продуктом Bobr и понимаю формат стартапа"}'

curl http://localhost:8001/tasks/1
```

**Expected Output:**
```json
{
  "id": 1,
  "payload": "Я точно хочу работать с продуктом Bobr и понимаю формат стартапа",
  "status": "done",
  "result": "Processed: Я точно хочу работать с продуктом Bobr и понимаю формат стартапа (took 3.45s)",
  "created_at": "datetime.now()",
  "updated_at": "datetime.now()"
}
```

The system is:
- Creating tasks via API
- Queueing them in RabbitMQ
- Processing asynchronously by workers
- Storing results in PostgreSQL

---


## Testing

```bash
docker-compose run --rm api pytest -v

python test_api.py

# Manual test
curl -X POST http://localhost:8001/tasks \
  -H "Content-Type: application/json" \
  -d '{"payload": "test"}'
```

---

### Database
```bash
docker-compose exec postgres psql -U postgres -d taskdb
SELECT * FROM tasks;
```

### Logs
```bash
docker-compose logs -f api     
docker-compose logs -f worker  
```

---

## Common Commands

```bash
# Start everything
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop everything
docker-compose down

# Clean restart
docker-compose down -v && docker-compose up --build

# Scale workers
docker-compose up -d --scale worker=5
