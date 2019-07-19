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
    def get(cls, uid):
        cur = mysql.connection.cursor(DictCursor)
        cur.execute('''SELECT `username`, `user_id`, `rating`, `player_token` FROM `user` WHERE `user_id` = %s''', (uid, ))
        rv = cur.fetchall()
        if len(rv) != 1:
            return None

        user_data = rv[0]
        return cls(user_data["user_id"], user_data["player_token"], user_data["username"], user_data["rating"])

    @classmethod
    def create(cls, username, password, email=None):
        insert_query = "INSERT INTO `user` (`username`, `password`, `email`) VALUES (%s, %s, %s)"
        pw_hash = bcrypt.generate_password_hash(password)
        try:
            cur = mysql.connection.cursor()
            cur.execute(insert_query, (username, pw_hash, email))
            mysql.connection.commit()
        except MySQLdb._exceptions.IntegrityError:
            return False
        return True

    @classmethod
    def authenticate(cls, username, password):
        select_query = "SELECT `username`, `user_id`, `rating`, `password` from `user` WHERE `username` = %s"
        update_token_query = "UPDATE `user` SET `player_token` = %s WHERE `username` = %s"

        cur = mysql.connection.cursor(DictCursor)
        cur.execute(select_query, (username))
        rv = cur.fetchall()

        # check username exists
        if len(rv) != 1:
            return None
        user_data = rv[0]

        # check password
        pw_correct = bcrypt.check_password_hash(user_data["password"], password)
        if not pw_correct:
            return None

        # Generate new player-token for sessions
        new_player_token = uuid.uuid4()
        cur.execute(update_token_query, (new_player_token, username))

        return User(user_data["user_id"], new_player_token, user_data["username"], user_data["rating"])

    def __init__(self, user_id, player_token, username, rating):
        self.id = user_id
        self.username = username
        self.player_token = player_token
        self.rating = rating

