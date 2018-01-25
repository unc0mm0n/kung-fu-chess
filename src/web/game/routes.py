import flask
from web.game import game, manager

@game.route('/')
def index():
    return "start a new game!"

@game.route('/<game_id>')
def view(game_id):
    if 1 not in manager:
        manager.create_game(1, 4000)  # fixed default for now
    return flask.render_template("game/game_page.html", game_id=game_id)