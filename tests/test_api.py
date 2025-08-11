from fastapi.testclient import TestClient
import models
from main import app


client = TestClient(app)


def test_create_user_success(db_session):
    resp = client.post("/user/create/", json={"tg_id": 123})
    assert resp.status_code == 200
    assert resp.json()["status"] == "OK"

    user = db_session.query(models.Users).filter(models.Users.tg_id == 123).first()
    assert user is not None


def test_create_user_duplicate(db_session):
    db_session.add(models.Users(tg_id=456))
    db_session.commit()

    resp = client.post("/user/create/", json={"tg_id": 456})
    assert resp.status_code == 400


def test_create_like_enqueued(monkeypatch, db_session):
    # Prepare users
    db_session.add_all([models.Users(tg_id=1), models.Users(tg_id=2)])
    db_session.commit()

    published = {"count": 0, "payloads": []}

    def fake_publish(like):
        published["count"] += 1
        published["payloads"].append(like.model_dump())

    monkeypatch.setattr("main.publish_like", fake_publish)

    resp = client.post(
        "/like/create/",
        json={
            "from_user_tg_id": 1,
            "to_user_tg_id": 2,
            "text": " hello ",
            "is_like": True,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ENQUEUED"
    assert published["count"] == 1
    assert published["payloads"][0]["text"] == "hello"