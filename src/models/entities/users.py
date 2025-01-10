from flask_login import UserMixin
class User(UserMixin):

    def __init__(self, user_id,name, role, warehouse_id, username, userpassword) -> None:
        self.user_id = user_id
        self.name = name
        self.role = role
        self.warehouse_id = warehouse_id
        self.username = username
        self.userpassword = userpassword

    def get_by_id(self):
        # Flask-Login necesita que esto devuelva una cadena
        return str(self.user_id)