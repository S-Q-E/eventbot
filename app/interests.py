from flask import request, flash, redirect, url_for
from flask_admin import BaseView, expose
from sqlalchemy.orm import joinedload
from db.database import get_db, User, Category

class InterestsView(BaseView):
    @expose("/", methods=["GET", "POST"])
    def index(self):
        db = next(get_db())
        try:
            if request.method == "POST":
                form_data = request.form
                user_ids = [key.split("_")[1] for key in form_data.keys() if key.startswith("interests_")]
                updated_users = 0

                for user_id_str in user_ids:
                    try:
                        user_id = int(user_id_str)
                        selected_ids = form_data.getlist(f"interests_{user_id}[]")
                        selected_ids = list(map(int, selected_ids))
                        user = db.query(User).filter_by(id=user_id).first()
                        if user:
                            selected_categories = db.query(Category).filter(Category.id.in_(selected_ids)).all()
                            user.interests = selected_categories
                            updated_users += 1
                    except Exception as e:
                        flash(f"Ошибка при обработке пользователя ID {user_id_str}: {e}", "error")

                db.commit()
                flash(f"Интересы обновлены для {updated_users} пользователей.", "success")
                return redirect(url_for("interestsview.index"))

            users = db.query(User).options(joinedload(User.interests)).order_by(User.id).all()
            all_categories = db.query(Category).order_by(Category.name).all()
            return self.render("admin/user_interests.html", users=users, all_categories=all_categories)
        except Exception as e:
            db.rollback()
            flash(f"Произошла ошибка: {e}", "error")
            return redirect(url_for("interestsview.index"))
        finally:
            db.close()
