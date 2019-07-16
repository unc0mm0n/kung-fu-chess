import flask

from web.game import game_bp, send_new_game_req

@game_bp.route('/')
def index():
    return "start a new game!"

@game_bp.route('/<game_id>')
def view(game_id):
    print(game_bp.root_path, game_bp.template_folder)
    send_new_game_req(game_id)
    return flask.render_template("game_page.html", game_id=game_id)
