import os, sys, time, logging
from logging.config import dictConfig
from flask import Flask, request, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from yookassa import Configuration, Payment
from .admin_panel import MyHomeView
from db.database import User, Event, Category, Registration
from .stats import StatsView
from .interests import InterestsView
from dotenv import load_dotenv
from threading import Thread

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Настройка логирования
dictConfig({
    'version': 1,
    'formatters': {
        'default': {'format': '%(asctime)s - %(levelname)s - %(message)s'}
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

logger = logging.getLogger(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))
DB_PATH = os.path.join(PROJECT_DIR, 'events.db')
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_PATH}"
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
Configuration.account_id = os.getenv('YOOKASSA_SHOP_ID')
Configuration.secret_key = os.getenv('YOOKASSA_API_KEY')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


@app.route("/")
def index():
    return render_template("index.html")


# Фоновая проверка статуса платежа
def check_payment_status(payment_id, users_data, event_id):
    logger.info(f"Начало проверки статуса платежа. ID платежа: {payment_id}")
    while True:
        try:
            payment = Payment.find_one(payment_id)
            logger.info(f"Статус платежа {payment_id}: {payment.status}")
            if payment.status == 'succeeded':
                for user_data in users_data:
                    user = User.query.get(user_data['id'])
                    registration = Registration(user_id=user.id, event_id=event_id)
                    db.session.add(registration)
                event = db.session.get(Event, event_id)
                if event:
                    event.current_participants += len(users_data)
                db.session.commit()
                logger.info(f"Платеж {payment_id} завершён. Участники добавлены на событие {event_id}")
                break
            elif payment.status in ['canceled', 'expired']:
                logger.warning(f"Платеж {payment_id} отменён или истёк. Статус: {payment.status}")
                break
        except Exception as e:
            logger.error(f"Ошибка при проверке статуса платежа {payment_id}: {e}")
        time.sleep(30)

@app.route('/event/<int:event_id>/add-participants', methods=['GET', 'POST'])
def add_participants(event_id):
    event = db.session.get(Event, event_id)
    if not event:
        flash("Событие не найдено.", "danger")
        logger.warning(f"Попытка доступа к несуществующему событию ID {event_id}")
        return redirect(url_for('index'))

    if request.method == 'POST':
        logger.info(f"POST-запрос на добавление участников к событию ID {event_id}")
        first_names = request.form.getlist('first_name')
        last_names = request.form.getlist('last_name')
        phone_numbers = request.form.getlist('phone_number')

        num_new_participants = len(first_names)
        available_slots = event.max_participants - event.current_participants

        if num_new_participants > available_slots:
            flash(f"Недостаточно мест. Осталось {available_slots}.", "warning")
            logger.warning(f"Превышение лимита участников на событие ID {event_id}")
            return redirect(request.url)

        users_data = []
        for first_name, last_name, phone in zip(first_names, last_names, phone_numbers):
            user = User(first_name=first_name, last_name=last_name, phone_number=phone)
            db.session.add(user)
            db.session.flush()
            users_data.append({"id": user.id})

        total_price = event.price * num_new_participants

        try:
            logger.info(f"Создание платежа на {total_price} RUB для события {event_id}")
            payment = Payment.create({
                "amount": {"value": str(total_price), "currency": "RUB"},
                "payment_method_data": {"type": "sbp"},
                "confirmation": {"type": "redirect", "return_url": "https://t.me/GuruEvent_bot/"},
                "capture": True,
                "description": f"Оплата участия в событии {event.name}",
                "metadata": {"event_id": event_id, "participants": num_new_participants}
            })
            confirmation_url = payment.confirmation.confirmation_url
            logger.info(f"Платёж создан. ID: {payment.id}, redirect: {confirmation_url}")
            Thread(target=check_payment_status, args=(payment.id, users_data, event_id)).start()
            db.session.commit()
            return redirect(confirmation_url)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка создания платежа: {e}")
            flash(f"Ошибка при создании платежа: {e}", "danger")
            return redirect(request.url)

    return render_template('add_participants.html', event=event)


admin = Admin(app, index_view=MyHomeView(), name='Моя Админка', template_mode='bootstrap3')
admin.add_view(StatsView(name="Статистика"))
admin.add_view(InterestsView(name="Подписки пользователей"))
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Event, db.session))
admin.add_view(ModelView(Category, db.session))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
