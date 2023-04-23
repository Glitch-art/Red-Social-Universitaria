from .entities.User import User

class ModelUser():
    
    @classmethod
    def login(self, db, email, password):
        try:
            cursor = db.cursor()
            sql = """
                SELECT * FROM users
                WHERE email = '{}'
            """.format(email)
            cursor.execute(sql)
            row = cursor.fetchone()
            if row != None:
                user = User(row[0], row[1], User.check_password(row[2], password), row[3], row[4], row[5], row[6])
                return user
            else: 
                return None
        except Exception as ex:
            print('Error: ', ex)
            raise Exception(ex)
    
    @classmethod
    def get_by_id(self, db, id):
        try:
            cursor = db.cursor()
            sql = """
                SELECT * FROM users
                WHERE id = {}
            """.format(id)
            cursor.execute(sql)
            row = cursor.fetchone()
            if row != None:
                return User(id=row[0], email=row[1], password=row[2], name=row[3], type_user=row[4], created_at=row[5], updated_at=row[6])
            else: 
                return None
        except Exception as ex:
            print('Error: ', ex)
            raise Exception(ex)