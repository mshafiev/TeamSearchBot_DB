# logger.py

import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import os

# Создание директории для логов, если не существует
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "app_server.log")
os.makedirs(LOG_DIR, exist_ok=True)

# Настройка логгера
logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

# Формат логов
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# Файл
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)

# Консоль
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)

# Добавляем хендлеры (если ещё не добавлены)
if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

# Хендлер ошибок валидации (422)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = await request.body()
    logger.warning(
        f"Ошибка валидации запроса: {request.method} {request.url} | Body: {body.decode('utf-8') or '—'} | Ошибки: {exc.errors()}"
    )
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

# Хендлер HTTP ошибок (404, 500 и т.д.)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning(
        f"HTTP ошибка {exc.status_code} при запросе {request.method} {request.url}: {exc.detail}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
