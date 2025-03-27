import logging

from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, DateTime, UniqueConstraint, Text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

DATABASE_URL = "sqlite:///events.db"

engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_timeout=30,
    pool_recycle=1800
)

Session = sessionmaker(bind=engine)
Base = declarative_base()


def get_db():
    db = Session()
    try:
        yield db
    except SQLAlchemyError as e:
        logging.info(f"Ошибка при доступе к базе данных {e}")
        db.rollback()
    finally:
        db.close()


# Модель пользователя
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=True)
    first_name = Column(String)
    last_name = Column(String)
    phone_number = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    user_games = Column(Integer, default=0)
    photo_file_path = Column(String, nullable=True)
    photo_file_id = Column(String, nullable=True)
    user_level = Column(String, nullable=True)
    is_registered = Column(Boolean, default=False)
    is_mvp_candidate = Column(Boolean, default=False)

    registrations = relationship("Registration", back_populates="user", cascade="all, delete-orphan")


class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, index=True)
    description = Column(String)
    address = Column(String)
    event_time = Column(DateTime, index=True)
    price = Column(Integer, default=0)
    max_participants = Column(Integer, default=10)
    current_participants = Column(Integer, default=0)
    is_mvp_sent = Column(Boolean, default=False)

    registrations = relationship("Registration", back_populates="event", cascade="all, delete-orphan")


class Registration(Base):
    __tablename__ = 'registrations'
    id = Column(Integer, primary_key=True, index=False, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    event_id = Column(Integer, ForeignKey('events.id'))
    reminder_time = Column(String, nullable=True)
    is_paid = Column(Boolean, default=False)
    __table_args__ = (UniqueConstraint('user_id', 'event_id', name='_user_event_uc'),)

    user = relationship("User", back_populates="registrations")
    event = relationship("Event", back_populates="registrations")


Base.metadata.create_all(bind=engine)
