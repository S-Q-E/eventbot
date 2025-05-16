from flask_admin import Admin, AdminIndexView, expose


class MyHomeView(AdminIndexView):
    @expose('/')
    def index(self):
        message = 'Добро пожаловать в админ-панель EventBot'

        return self.render('admin/myhome.html', message=message)
