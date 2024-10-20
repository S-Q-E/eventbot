from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///events.db"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()


def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()


# Пример модели пользователя
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    is_admin = Column(Boolean, default=False)


# Пример модели события
class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    address = Column(String)
    event_time = Column(DateTime)


# Пример модели регистрации на событие
class Registration(Base):
    __tablename__ = 'registrations'
    id = Column(Integer, primary_key=True, index=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    event_id = Column(Integer, ForeignKey('events.id'))
    reminder_time = Column(DateTime)


# Создание таблиц
Base.metadata.create_all(bind=engine)
