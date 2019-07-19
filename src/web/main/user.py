import uuid

from flask_login import UserMixin
import MySQLdb
from MySQLdb.cursors import DictCursor

from web import login_manager, mysql, bcrypt


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


class User(UserMixin):

    @classmethod
    def get(cls, id):
        cur = mysql.connection.cursor(DictCursor)
        cur.execute('''SELECT * FROM `user` WHERE `user_id` = {}'''.format(id))
        rv = cur.fetchall()
        if len(rv) != 1:
            print("No users matching ID")
            return None

        return cls(rv[1])

    @classmethod
    def create(cls, username, password, email=None):

        insert_query = "INSERT INTO `user` (`username`, `password`, `password_salt`, `email`) VALUES (%s, %s, %s, %s)"
        password_salt = uuid.uuid4()
        print(password_salt)
        pw_hash = bcrypt.generate_password_hash("{s}{p}{s}".format(s=password_salt, p=password))
        print(pw_hash)
        print(bcrypt.check_password_hash(pw_hash, "{s}{p}{s}".format(s=password_salt, p=password)))
        print(bcrypt.check_password_hash(pw_hash, "{s}{p}{s}".format(s=password_salt, p="aa")))
        try:
            cur = mysql.connection.cursor()
            cur.execute(insert_query, (username, pw_hash, password_salt, email))
            mysql.connection.commit()
        except MySQLdb._exceptions.IntegrityError:
            print("Invalid username or password")

    def __init__(self, user_id, player_token, username, rating):
        self.id = id
        self.name = username
        self.player_token = player_token
        self.rating = rating

