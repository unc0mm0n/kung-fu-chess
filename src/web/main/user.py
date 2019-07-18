from flask_login import UserMixin
from web import login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


class User(UserMixin):

    @classmethod
    def get(cls, id):
        return cls(3)

    def __init__(self, id):
        self.id = id
        self.name = "YuvalW"
