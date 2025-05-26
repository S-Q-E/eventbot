import os, sys
from logging.config import dictConfig
from flask import Flask, request, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

from .admin_panel import MyHomeView
from db.database import User, Event, Category, Registration
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


@app.route("/")
def index():
    return render_template("index.html")


@app.route('/event/<int:event_id>/add-participants', methods=['GET', 'POST'])
def add_participants(event_id):
    event = db.session.get(Event, event_id)
    if not event:
        flash("Событие не найдено.", "error")
        return redirect(url_for('admin.index'))

    if request.method == 'POST':
        first_names = request.form.getlist('first_name')
        last_names = request.form.getlist('last_name')
        phone_numbers = request.form.getlist('phone_number')

        num_new_participants = len(first_names)
        available_slots = event.max_participants - event.current_participants

        if num_new_participants > available_slots:
            flash(f"Недостаточно свободных мест. Осталось только {available_slots} мест(а).", "warning")
            return redirect(request.url)

        total_price = 0
        for first_name, last_name, phone in zip(first_names, last_names, phone_numbers):
            user = User(first_name=first_name, last_name=last_name, phone_number=phone)
            db.session.add(user)
            db.session.flush()

            registration = Registration(user_id=user.id, event_id=event_id)
            db.session.add(registration)
            total_price += event.price

        event.current_participants += num_new_participants
        db.session.commit()

        return render_template('participants_added.html', event=event, total_price=total_price)

    return render_template('add_participants.html', event=event)


admin = Admin(app, index_view=MyHomeView(), name='Моя Админка', template_mode='bootstrap3')
admin.add_view(StatsView(name="Статистика"))
admin.add_view(InterestsView(name="Подписки пользователей"))
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Event, db.session))
admin.add_view(ModelView(Category, db.session))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
