import flask
from flask_login import login_user

from web.main import main
from web.main.user import User

@main.route('/')
def index():
    return flask.render_template("main_page.html", games = [1,2,3])

@main.route('/login')
def login():
    login_user(User(3))
    return flask.redirect('/')
