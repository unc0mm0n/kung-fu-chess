import json

import flask
from flask_login import login_user, current_user, login_required

from web.main import main
from web.main.user import User
from web.game import get_active_game_set, get_waiting_game_set


@main.route('/')
def index():
    db = flask.current_app.redis
    active_games =  db.smembers(get_active_game_set())
    waiting_games = db.smembers(get_waiting_game_set())
    print(active_games)
    print(waiting_games)
    return flask.render_template("main_page.html", a_games=map(json.loads, active_games)
                                                 , w_games=map(json.loads, waiting_games))

@main.route('/user/<user_id>')
def user(user_id):
    User.create('aa', 'bb')
    return "You are searching for the user page. It does not exist yet"

@main.route('/logout')
@login_required
def logout():
    logout_user(current_user)
    return flask.redirect('/')

@main.route('/login', methods=['GET', 'POST'])
def login():
    login_user(User(3))
    return flask.redirect('/')

