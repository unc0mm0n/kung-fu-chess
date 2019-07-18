import json

from flask import Blueprint

from . import queue_reader

game_bp = Blueprint('game', __name__, static_folder='static', template_folder='templates')

def init_game(i_app, i_socketio):
    global _app
    _app = i_app

    _t = i_socketio.start_background_task(queue_reader.poll_game_cnfs, _app.redis,
            "{}:games".format(_app.config["REDIS_STORE_KEY"]),
            get_cnfs_queue(),
            i_socketio)

def next_game_id():
    key = "{}:games:game_id".format(_app.config["REDIS_STORE_KEY"])
    cid = _app.redis.get(key)
    print(cid)
    if not cid:
        cid = 0
    cid = int(cid) + 1
    _app.redis.set(key, cid)
    return cid

def get_active_game_set():
    return "{}:games:playing".format(_app.config["REDIS_STORE_KEY"])

def get_waiting_game_set():
    return "{}:games:waiting".format(_app.config["REDIS_STORE_KEY"])

@property
def redis_game_store():
    return "{}:games".format(_app.config["REDIS_STORE_KEY"])

def get_app():
    return _app

def push_req(req, payload, game_id, player_id):
    q_id = get_app().config["REDIS_GAMES_REQ_QUEUE"]
    print("[{}, {}] Requesting {} ({}) in {}".format(game_id, player_id, req,payload, q_id))
    _app.redis.rpush (q_id, json.dumps([game_id, player_id, req, payload]))
    _app.redis.expire(q_id, 3600)

def get_cnfs_queue():
    """ Get the cnfs queue used by the game manager. """
    return get_app().config["REDIS_GAMES_CNF_QUEUE"]

from . import routes, events
