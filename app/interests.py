from flask import request, flash, redirect, url_for
from flask_admin import BaseView, expose
from db.database import get_db, User, Category
from sqlalchemy.orm import joinedload


class InterestsView(BaseView):
    @expose("/", methods=("GET", "POST"))
    def index(self):
        with get_db() as db:
            categories = db.query(Category).order_by(Category.name).all()
            users = db.query(User).options(joinedload(User.interests)).order_by(User.id).all()

            if request.method == "POST":
                for user in users:
                    key = f"interests_{user.id}"
                    selected_ids = request.form.getlist(key)
                    try:
                        selected_int_ids = {int(item) for item in selected_ids}
                    except ValueError:
                        selected_int_ids = set()
                    user.interests = [category for category in categories if category.id in selected_int_ids]

                flash("Интересы пользователей обновлены.", "success")
                return redirect(url_for(".index"))

            return self.render("admin/user_interests.html", users=users, categories=categories)
