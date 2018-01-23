import flask
from app.game import game

@game.route('/')
def index():
    return "start a new game!"

@game.route('/<game_id>')
def view(game_id):
    return flask.render_template("game/game_page.html", game_id = game_id)