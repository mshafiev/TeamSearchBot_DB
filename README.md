# Messaging and User Service

A FastAPI-based service for managing users, olymp records, and likes. Likes are validated and enqueued to RabbitMQ for asynchronous processing by a consumer which persists them in the database.

## Purpose
- Manage users and olymp entries
- Accept like events via HTTP, validate inputs, and publish to RabbitMQ
- Consume like messages and store them reliably

## Inputs & Outputs
- HTTP JSON payloads validated by Pydantic models in `schemas.py`
- AMQP messages (JSON) on queue `likes` (configurable via `RMQ_QUEUE`)
- Database tables defined in `models.py`

## Usage
- Environment variables for DB and RMQ:
  - DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME
  - RMQ_USER, RMQ_PASS, RMQ_HOST, RMQ_PORT, RMQ_QUEUE
- Run server:
  - `gunicorn main:app -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8005 --workers=4`
- Run consumer:
  - `python consumer.py`

## Testing
- Install dev deps: `pip install -r requirements.txt`
- Run: `pytest -q`

## Key Components
- `main.py`: API endpoints with dependency-injected DB sessions and robust error handling
- `messaging.py`: RabbitMQ publisher with durable queue, publisher confirms, and reconnection
- `services/likes_service.py`: Business logic for creating like records
- `consumer.py`: RabbitMQ consumer with ack/nack strategy and retry on connection loss
- `logger.py`: Unified logging and exception handlers
- `schemas.py`: Pydantic models with field validation

## Changelog (Refactor)
- Added `schemas.py` and migrated all request validation to Pydantic models with constraints
- Introduced `database.get_db()` for per-request sessions and enabled `pool_pre_ping`
- Extracted business logic into `services/likes_service.py` for testability (SRP, DRY)
- Implemented `messaging.py` (publisher confirms, durable queue, reconnection)
- Updated `consumer.py` (session per message, input validation, ack/nack, reconnect loop)
- Fixed bug in `get_last_likes` to filter by `to_user_tg_id`
- Improved error handling and logging across the app
- Added unit tests for API and like service

## Edge Cases & Resilience
- Empty/whitespace text normalized to `None`
- Duplicate user creation prevented
- Likes where `from_user_tg_id == to_user_tg_id` are rejected in consumer
- Publisher retries connection with exponential backoff
- Consumer requeues once on transient DB errors and avoids infinite loops

## Future Optimizations
- Switch to `aio-pika` and async publisher/consumer to avoid blocking
- Add idempotency keys for like events to prevent duplicates
- Implement rate limiting and backpressure (e.g., 429, circuit breaker)
- Add structured logging (JSON) and tracing (OpenTelemetry)
- Add integration tests with ephemeral Postgres and RabbitMQ via docker-compose