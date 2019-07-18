import flask
from flask_login import login_required, current_user

from web.game import game_bp, next_game_id, push_req

def send_new_game_req(game_id, player_id, cd=10000):
    push_req("game-req", {"cd": cd}, game_id, player_id)

@game_bp.route('/')
@login_required
def index():
    game_id = next_game_id()
    sid = current_user.get_id()
    send_new_game_req(game_id, sid)
    return flask.redirect("./{}".format(game_id))

@game_bp.route('/<game_id>')
def view(game_id):
    return flask.render_template("game_page.html", game_id=game_id)
