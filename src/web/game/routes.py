import flask
from web.game import game, manager

@game.route('/')
def index():
    return "start a new game!"

@game.route('/<game_id>')
def view(game_id):
    try:
        game_id = int(game_id)
    except ValueError:
        flask.abort(404)
    if game_id not in manager:
        manager.create_game(game_id, 4000)  # fixed default for now
    return flask.render_template("game/game_page.html", game_id=game_id)