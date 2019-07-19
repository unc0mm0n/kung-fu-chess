import json

import flask
from flask import request
from flask_login import login_user, current_user, login_required, logout_user

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
    return flask.render_template("main/main_page.html", a_games=map(json.loads, active_games)
                                                 , w_games=map(json.loads, waiting_games))

@main.route('/user/<user_id>')
def user(user_id):
    return "You are searching for the user page. It does not exist yet"

@main.route('/register', methods=['GET', 'POST'])
def register():
    err = ""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        if not username or not password:
            err = "Empty username or password given!"
        elif User.create(username, password, email):
            return flask.redirect("./login")
        else:
            err = "Username already in use"
    return flask.render_template("main/register.html", err=err)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return flask.redirect('/')

@main.route('/login', methods=['GET', 'POST'])
def login():
    err = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.authenticate(username, password)
        if user:
            print("succesfully connected {}".format(user.username))
            login_user(user)
            return flask.redirect("./")
        else:
            err = "Invalid Username or Password"
    return flask.render_template("main/login.html", err=err)

