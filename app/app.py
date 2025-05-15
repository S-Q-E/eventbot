import os, sys
from logging.config import dictConfig
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from db.database import User, Event, Registration, VotingSession, Category
from .stats import StatsView
from .interests import InterestsView

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

dictConfig({
    'version': 1,
    'formatters': {
        'default': { 'format': '%(asctime)s - %(levelname)s - %(message)s' }
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'app.log',
            'formatter': 'default'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['file', 'console']
    }
})
# Пути
BASE_DIR = os.path.abspath(os.path.dirname(__file__))      # …/app
PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))   # …/eventbot
DB_PATH = os.path.join(PROJECT_DIR, 'events.db')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_PATH}"
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

db = SQLAlchemy(app)
migrate = Migrate(app, db)


# admin
admin = Admin(app, name="EventBot Admin", template_mode="bootstrap4")
admin.add_view(StatsView(name="Статистика"))
admin.add_view(InterestsView(name="Подписки пользователей"))
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Event, db.session))
admin.add_view(ModelView(Registration, db.session))
admin.add_view(ModelView(Category, db.session))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
