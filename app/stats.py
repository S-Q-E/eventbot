from flask_admin import BaseView, expose
from db.database import get_db, User, Registration
from sqlalchemy import func


class StatsView(BaseView):
    @expose('/')
    def index(self):
        with get_db() as db:
            user_count = db.query(User).count()
            registration_count = db.query(Registration).count()
            
            # Топ игроков по количеству регистраций
            top_players = (
                db.query(User.first_name, User.last_name, func.count(Registration.id).label('total_games'))
                .join(Registration)
                .group_by(User.id)
                .order_by(func.count(Registration.id).desc())
                .limit(10)
                .all()
            )
            
            return self.render('admin/stats.html', 
                               user_count=user_count, 
                               registration_count=registration_count,
                               top_players=top_players)
