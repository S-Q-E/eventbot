from db.database import get_db, User

async def check_admin_rights(user_id):
    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        return user.is_admin if user else False