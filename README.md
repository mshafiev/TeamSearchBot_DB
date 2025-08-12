# Service: Users, Olymps, Likes API

A FastAPI service for managing users, olymp records, and likes, with a RabbitMQ consumer that persists likes from a queue.

## Endpoints (selected)
- `GET /users/all`: list all users
- `POST /user/create/`: create user by `tg_id`
- `PUT /user/update/`: update fields by `tg_id`
- `POST /olymp/create/`: create olymp record
- `GET /like/get_incoming/`: incoming likes for a user
- `POST /like/create/`: create like
- `GET /like/get_last/`: last likes for a user
- `GET /like/exists/`: like existence check

## Inputs/Outputs
- Request/response schemas are defined in `schemas.py` with validation (lengths, ranges, and cross-field checks).
- Responses are ORM-compatible via `from_attributes=True`.

## Message-sending logic (likes persistence)
- Producer: push JSON messages to RabbitMQ queue `likes`.
- Consumer: `consumer.py` reads messages, validates with `LikesBase`, persists via SQLAlchemy.
- Ordering and idempotency: DB commit only after validation; message ack after successful commit or safe rejection.

## How to run
- Local: `uvicorn main:app --reload --port 8005`
- Docker: `docker compose up --build`

Required env vars (DB, RMQ): see `database.py` and `consumer.py`.

## Testing
```
pip install -r requirements.txt pytest
pytest -q
```

## Changelog (key refactors)
- Introduced `schemas.py` for Pydantic validation
- Added `services/likes_service.py` to separate business logic from I/O
- Fixed `/like/get_last/` filter (use `to_user_tg_id`)
- Unified logging via `logger.py`; removed `logger_config` in API and consumer
- Improved consumer resiliency (reconnect loop, durable queue, prefetch)
- Added unit tests for likes service

## Future optimizations
- Add rate limiting and retry/backoff patterns for external calls
- Introduce background tasks for heavy operations (FastAPI `BackgroundTasks`)
- Add pagination for list endpoints
- Add OpenAPI descriptions and examples for all endpoints
- Add Alembic migrations and CI