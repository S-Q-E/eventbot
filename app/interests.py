from flask import request
from flask_admin import BaseView, expose
from sqlalchemy.orm import joinedload
from db.database import get_db, Registration, Event, User


class InterestsView(BaseView):
    @expose("/")
    def index(self):
        page = request.args.get('page', 1, type=int)
        per_page = 20  # Количество пользователей на странице

        db = next(get_db())
        users_query = db.query(User).options(joinedload(User.interests)).order_by(User.id)
        total_users = users_query.count()
        users = users_query.offset((page - 1) * per_page).limit(per_page).all()
        db.close()

        total_pages = (total_users + per_page - 1) // per_page

        return self.render(
            'admin/user_interests.html',
            users=users,
            page=page,
            total_pages=total_pages
        )


