import flask

from web.game import game_bp, get_game_redis, get_game_manager, get_store_key, get_cnfs_queue, get_reqs_queue
from kfchess.game import KungFuChess, RedisKungFuBoard

@game_bp.route('/')
def index():
    return "start a new game!"

@game_bp.route('/<game_id>')
def view(game_id):
    key = get_store_key(game_id)
    if not get_game_redis().exists(key):
        game_params = {
                    'move_cd': 4000,
                    'nfen': None,
                    'board_class': RedisKungFuBoard,
                    'redis_db': get_game_redis(),
                    'store_key': key,
                    'exp': 3600 * 100 # 1h
                }
        game_ins = KungFuChess.FromNfen(**game_params)
        get_game_manager().manage_game(game_ins, game_id, 0, 1,
                get_reqs_queue(game_id), get_cnfs_queue(game_id))
    return flask.render_template("game/game_page.html", game_id=game_id)
