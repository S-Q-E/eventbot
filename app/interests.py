# app/interests.py
from flask import request, flash, redirect, url_for
from flask_admin import BaseView, expose
from sqlalchemy.orm import joinedload
from db.database import get_db, User, Category


class InterestsView(BaseView):
    """Админ-панель: редактирование подписок (interests) пользователей."""

    @expose("/", methods=("GET", "POST"))
    def index(self):
        db = next(get_db())
        try:
            # Заранее загрузим все категории (Interest)
            categories = db.query(Category).order_by(Category.name).all()
            # И всех пользователей сразу с их подписками
            users = db.query(User).options(joinedload(User.interests)).order_by(User.id).all()

            if request.method == "POST":
                # Для каждого пользователя прочитаем что пришло из формы
                for user in users:
                    key = f"interests_{user.id}"
                    selected_ids = request.form.getlist(key)  # список строк
                    # конвертируем их в int и фильтруем категории
                    sel_ints = set(map(int, selected_ids))
                    user.interests = [c for c in categories if c.id in sel_ints]
                db.commit()
                flash("✅ Интересы пользователей обновлены.", "success")
                return redirect(url_for(".index"))

            # GET — просто рисуем шаблон
            return self.render(
                "admin/user_interests.html",
                users=users,
                categories=categories
            )

        except Exception as e:
            db.rollback()
            flash(f"❌ Ошибка при сохранении: {e}", "danger")
            return redirect(url_for(".index"))

        finally:
            db.close()
