from pika import ConnectionParameters, BlockingConnection, PlainCredentials
import models
from database import engine, SessionLocal
from main import LikesBase
import atexit
from logger_config import logger
import os
from dotenv import load_dotenv

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
)

db = SessionLocal()
atexit.register(db.close)


import json


def callback(ch, method, properties, body):
    try:
        data = json.loads(body.decode())
        like = LikesBase(**data)
    except Exception as e:
        logger.warning(f"Ошибка входных данных: {e}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

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
        logger.error(f"Ошибка {e}")


def main():
    with BlockingConnection(connection_params) as conn:
        with conn.channel() as ch:
            ch.queue_declare(queue="likes")

            ch.basic_consume(
                queue="likes",
                on_message_callback=callback,
            )
            ch.start_consuming()


if __name__ == "__main__":
    main()
