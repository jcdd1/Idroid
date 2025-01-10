from sqlalchemy import text
from .entities.users import User


class ModelLog():

    @classmethod
    def login(self, db, user):
        try:
            result = db.session.execute(
            text("SELECT * FROM users WHERE username = :username AND userpassword = crypt(:userpassword, userpassword)"),
            {'username': user.username, 'userpassword': user.userpassword}
        ).fetchone()
            
            if result is not None:
                user_encontrado = User(result[0], result[1], result[2], result[3], result[4], result[5])
                return user_encontrado
            else:
                return None
        except Exception as ex:
            raise Exception(ex)
        
    @classmethod
    def get_by_id(self, db, user_id):
        try:
            result = db.session.execute(
            text("SELECT user_id, role, warehouse_id, username FROM users WHERE user_id = :user_id"),
            {'id': user_id}
        ).fetchone()
            
            if result is not None:
                user_encontrado = User(result[0], "", result[1], result[2], result[3], "")
                return user_encontrado
            else:
                print("No existe")
                return None
        except Exception as ex:
            raise Exception(ex)
