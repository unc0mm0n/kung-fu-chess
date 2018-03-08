import flask

from web.game import game_bp, send_new_game_req

@game_bp.route('/')
def index():
    return "start a new game!"

@game_bp.route('/<game_id>')
def view(game_id):
    send_new_game_req(game_id)
    return flask.render_template("game/game_page.html", game_id=game_id)
