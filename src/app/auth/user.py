from flask.ext.login import UserMixin

from .. import login_manager

class User(UserMixin):
    def __init__(self):
        self.id = -1

@login_manager.user_loader
def load_user(id):
    return User()
