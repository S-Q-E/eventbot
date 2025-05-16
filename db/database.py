import logging
from datetime import datetime

from sqlalchemy import (
    create_engine, Column, Integer, String, Boolean,
    ForeignKey, DateTime, UniqueConstraint, Table
)
from sqlalchemy.orm import (
    declarative_base, relationship, sessionmaker, scoped_session
)
from sqlalchemy.exc import SQLAlchemyError

# Настройки базы данных
DATABASE_URL = "sqlite:///events.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Важно для SQLite и многопоточности
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800
)

# Настройка сессии
SessionFactory = sessionmaker(bind=engine, expire_on_commit=True)
Session = scoped_session(SessionFactory)

# Базовая модель
Base = declarative_base()

# Генератор доступа к базе данных
def get_db():
    db = Session()
    try:
        db.execute("PRAGMA foreign_keys = ON")  # включаем поддержку внешних ключей
        db.expire_all()  # очищаем кэш (важно для бота и Flask)
        yield db
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logging.error(f"Ошибка при доступе к базе данных: {e}")
        raise
    finally:
        db.close()
        Session.remove()

# Ассоциативная таблица: интересы пользователей
user_interests = Table(
    'user_interests', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id', ondelete='CASCADE'), primary_key=True)
)

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
    votes = Column(Integer, default=0)

    interests = relationship("Category", secondary=user_interests, back_populates="subscribers")
    registrations = relationship("Registration", back_populates="user", cascade="all, delete-orphan")

# Модель события
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
    is_checked = Column(Boolean, default=False)
    is_team_divide = Column(Boolean, default=False)

    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    category = relationship("Category", back_populates="events")

    registrations = relationship("Registration", back_populates="event", cascade="all, delete-orphan")

# Модель регистрации на событие
class Registration(Base):
    __tablename__ = 'registrations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    event_id = Column(Integer, ForeignKey('events.id'))
    reminder_time = Column(String, nullable=True)
    is_paid = Column(Boolean, default=False)

    __table_args__ = (UniqueConstraint('user_id', 'event_id', name='_user_event_uc'),)

    user = relationship("User", back_populates="registrations")
    event = relationship("Event", back_populates="registrations")

# Сессии голосования за MVP
class VotingSession(Base):
    __tablename__ = 'voting_sessions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    poll_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Категории событий
class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)

    events = relationship("Event", back_populates="category", cascade="all, delete-orphan")
    subscribers = relationship("User", secondary=user_interests, back_populates="interests")

# Создание таблиц
Base.metadata.create_all(bind=engine)
