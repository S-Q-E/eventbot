from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import random

from db.database import get_db, MVPVote, User, Event, Registration

router = APIRouter()


@router.get("/mvp/{event_id}")
def get_random_candidates(event_id: int, db: Session = Depends(get_db)):
    """
    Возвращает 3 случайных участника (кандидата) из таблицы registrations
    для текущего события.
    """
    # Находим всех участников события
    registrations = db.query(Registration).filter(Registration.event_id == event_id).all()
    if not registrations:
        raise HTTPException(status_code=404, detail="No participants found for this event")

    # Достаём user_id
    user_ids = [reg.user_id for reg in registrations]
    # Получаем пользователей
    users = db.query(User).filter(User.id.in_(user_ids)).all()

    # Если меньше 3 участников, отдадим всех, иначе выберем случайные 3
    if len(users) <= 3:
        selected_users = users
    else:
        selected_users = random.sample(users, 3)

    # Формируем ответ (например, фото и ФИО)
    # Предполагаем, что в User.photo_file_id хранится file_id фото из TG,
    # либо в будущем – url-адрес, если храните где-то на сервере.
    result = []
    for u in selected_users:
        result.append({
            "user_id": u.id,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "photo_file_id": u.photo_file_id  # или любая другая ссылка на фото
        })
    return {"candidates": result}


@router.post("/mvp/vote")
def vote_for_mvp(
    event_id: int,
    voter_id: int,
    candidate_id: int,
    db: Session = Depends(get_db)
):
    """
    Сохраняет голос за MVP в базу.
    """
    # Проверяем, что такой event существует
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Проверяем, что voter и candidate есть в users
    voter = db.query(User).filter(User.id == voter_id).first()
    candidate = db.query(User).filter(User.id == candidate_id).first()
    if not voter or not candidate:
        raise HTTPException(status_code=404, detail="User not found")

    # Можно добавить проверку, что voter != candidate,
    # что voter зарегистрирован на событие, и т.п.

    new_vote = MVPVote(
        event_id=event_id,
        voter_id=voter_id,
        candidate_id=candidate_id
    )
    db.add(new_vote)
    db.commit()

    return {"status": "ok", "message": "Vote accepted"}
