import json
import os
import threading
import time
from typing import Optional

from pika import BlockingConnection, ConnectionParameters, PlainCredentials
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import BasicProperties
from pika.exceptions import AMQPConnectionError, NackError
from schemas import LikeCreate
from logger import logger

_RMQ_LOCK = threading.Lock()
_CONNECTION: Optional[BlockingConnection] = None
_CHANNEL: Optional[BlockingChannel] = None
_QUEUE_NAME = os.getenv("RMQ_QUEUE", "likes")


def _connect_if_needed() -> None:
    global _CONNECTION, _CHANNEL
    if _CHANNEL and _CHANNEL.is_open:
        return

    rmq_user = os.getenv("RMQ_USER")
    rmq_pass = os.getenv("RMQ_PASS")
    rmq_host = os.getenv("RMQ_HOST")
    rmq_port = int(os.getenv("RMQ_PORT", 5672))

    credentials = PlainCredentials(rmq_user, rmq_pass) if rmq_user else None
    params = ConnectionParameters(host=rmq_host, port=rmq_port, credentials=credentials)

    backoff = 1.0
    for attempt in range(6):
        try:
            _CONNECTION = BlockingConnection(params)
            _CHANNEL = _CONNECTION.channel()
            _CHANNEL.confirm_delivery()
            _CHANNEL.queue_declare(queue=_QUEUE_NAME, durable=True)
            _CHANNEL.basic_qos(prefetch_count=50)
            return
        except AMQPConnectionError as exc:
            logger.warning(f"RabbitMQ connect attempt {attempt+1} failed: {exc}")
            time.sleep(backoff)
            backoff = min(backoff * 2, 30)
    raise RuntimeError("Failed to connect to RabbitMQ after multiple attempts")


def publish_like(like: LikeCreate) -> None:
    payload = json.dumps(like.model_dump()).encode("utf-8")
    with _RMQ_LOCK:
        _connect_if_needed()
        assert _CHANNEL is not None
        try:
            _CHANNEL.basic_publish(
                exchange="",
                routing_key=_QUEUE_NAME,
                body=payload,
                properties=BasicProperties(content_type="application/json", delivery_mode=2),
                mandatory=True,
            )
        except (NackError, AMQPConnectionError) as exc:
            logger.error(f"Failed to publish like message: {exc}")
            # Reset connection; it will reconnect on next call
            try:
                if _CHANNEL and _CHANNEL.is_open:
                    _CHANNEL.close()
            except Exception:
                pass
            try:
                if _CONNECTION and _CONNECTION.is_open:
                    _CONNECTION.close()
            except Exception:
                pass
            raise