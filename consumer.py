from pika import ConnectionParameters, BlockingConnection, PlainCredentials
import models
from database import engine, SessionLocal
from schemas import LikesBase
from logger import logger
import os
from dotenv import load_dotenv
import json
import time

load_dotenv()

RMQ_USER = os.getenv("RMQ_USER")
RMQ_PASS = os.getenv("RMQ_PASS")
RMQ_HOST = os.getenv("RMQ_HOST")
RMQ_PORT = int(os.getenv("RMQ_PORT", 5672))

credentials = PlainCredentials(RMQ_USER, RMQ_PASS)

connection_params = ConnectionParameters(
    host=RMQ_HOST,
    port=RMQ_PORT,
    credentials=credentials,
    heartbeat=30,
    blocked_connection_timeout=300,
)

def callback(ch, method, properties, body):
    try:
        data = json.loads(body.decode())
        # Проверяем, что id не передаётся в LikesBase (и не попадёт в insert)
        if "id" in data:
            data.pop("id")
        like = LikesBase(**data)
    except Exception as e:
        logger.warning(f"Ошибка входных данных: {e}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    db = SessionLocal()
    try:
        from_user = (
            db.query(models.Users)
            .filter(models.Users.tg_id == like.from_user_tg_id)
            .first()
        )
        to_user = (
            db.query(models.Users)
            .filter(models.Users.tg_id == like.to_user_tg_id)
            .first()
        )
        if not from_user or not to_user:
            logger.error("Один из пользователей не найден")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        # Явно не передаём id при создании лайка
        db_like = models.Likes(
            from_user_tg_id=like.from_user_tg_id,
            to_user_tg_id=like.to_user_tg_id,
            text=like.text,
            is_like=like.is_like,
            is_readed=like.is_readed,
        )
        db.add(db_like)
        db.commit()
        db.refresh(db_like)
        logger.info(f"Лайк сохранён: id {db_like.id}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при сохранении лайка: {e}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    finally:
        db.close()

def main():
    while True:
        try:
            with BlockingConnection(connection_params) as conn:
                with conn.channel() as ch:
                    ch.queue_declare(queue="likes", durable=True)
                    ch.basic_qos(prefetch_count=50)
                    ch.basic_consume(
                        queue="likes",
                        on_message_callback=callback,
                    )
                    logger.info("Started consuming from 'likes' queue")
                    ch.start_consuming()
        except Exception as exc:
            logger.error(f"RabbitMQ connection error: {exc}. Reconnecting in 5s...")
            time.sleep(5)


if __name__ == "__main__":
    main()
