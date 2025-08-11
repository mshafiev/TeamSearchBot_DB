import json
import os
from pika import ConnectionParameters, BlockingConnection, PlainCredentials
from pika.exceptions import AMQPConnectionError
from schemas import LikeCreate
from services.likes_service import create_like_record
from database import SessionLocal
from logger import logger
from dotenv import load_dotenv

load_dotenv()

RMQ_USER = os.getenv("RMQ_USER")
RMQ_PASS = os.getenv("RMQ_PASS")
RMQ_HOST = os.getenv("RMQ_HOST")
RMQ_PORT = int(os.getenv("RMQ_PORT", 5672))
RMQ_QUEUE = os.getenv("RMQ_QUEUE", "likes")

credentials = PlainCredentials(RMQ_USER, RMQ_PASS) if RMQ_USER else None
connection_params = ConnectionParameters(host=RMQ_HOST, port=RMQ_PORT, credentials=credentials)


def callback(ch, method, properties, body):
    try:
        data = json.loads(body.decode("utf-8"))
        like = LikeCreate(**data)
    except Exception as e:
        logger.warning(f"Invalid incoming message, drop: {e}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    # Drop clearly invalid business input early
    if like.from_user_tg_id == like.to_user_tg_id:
        logger.warning("from_user_tg_id equals to_user_tg_id; dropping message")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    db = SessionLocal()
    try:
        created = create_like_record(db, like)
        logger.info(f"Like stored: id {created.id}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except ValueError as e:
        logger.error(f"Business validation failed, drop: {e}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        db.rollback()
        # Attempt one retry by requeueing if not redelivered
        if getattr(method, "redelivered", False):
            logger.error(f"DB error after redelivery; acking to avoid loop: {e}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
        else:
            logger.error(f"DB error; requeue once: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    finally:
        db.close()


def main():
    while True:
        try:
            with BlockingConnection(connection_params) as conn:
                with conn.channel() as ch:
                    ch.queue_declare(queue=RMQ_QUEUE, durable=True)
                    ch.basic_qos(prefetch_count=50)
                    ch.basic_consume(queue=RMQ_QUEUE, on_message_callback=callback)
                    logger.info("Consumer started, waiting for messages...")
                    ch.start_consuming()
        except AMQPConnectionError as exc:
            logger.warning(f"Connection lost, retrying: {exc}")
