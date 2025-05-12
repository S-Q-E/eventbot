from flask_admin import BaseView, expose
from sqlalchemy import func
from datetime import datetime, timedelta
from db.database import get_db, Registration, Event, User


class StatsView(BaseView):
    @expose('/')
    def index(self):
        db = next(get_db())
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # Посещения за последнюю неделю
        weekly_attendance = (
            db.query(func.count(Registration.id))
              .join(Event, Registration.event_id == Event.id)
              .filter(
                  Registration.is_paid == True,
                  Event.event_time >= week_ago
              )
              .scalar()
        )

        # Посещения за последний месяц
        monthly_attendance = (
            db.query(func.count(Registration.id))
              .join(Event, Registration.event_id == Event.id)
              .filter(
                  Registration.is_paid == True,
                  Event.event_time >= month_ago
              )
              .scalar()
        )

        # Топ-5 участников по числу посещений
        top_users = (
            db.query(
                User.first_name,
                User.last_name,
                func.count(Registration.id).label('visits')
            )
              .join(Registration, User.id == Registration.user_id)
              .filter(Registration.is_paid == True)
              .group_by(User.id)
              .order_by(func.count(Registration.id).desc())
              .limit(5)
              .all()
        )

        return self.render(
            'admin/stats.html',
            weekly_attendance=weekly_attendance,
            monthly_attendance=monthly_attendance,
            top_users=top_users
        )
