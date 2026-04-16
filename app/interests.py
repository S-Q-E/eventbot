from flask import render_template
from flask_admin import BaseView, expose
from db.database import get_db, User, Category
from sqlalchemy.orm import joinedload


class InterestsView(BaseView):
    @expose('/')
    def index(self):
        with get_db() as db:
            users = db.query(User).options(joinedload(User.interests)).all()
            return self.render('admin/user_interests.html', users=users)
