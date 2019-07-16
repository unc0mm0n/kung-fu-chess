from threading import Thread
import json

import redis
from flask import Blueprint

from . import queue_reader

game_bp = Blueprint('game', __name__, static_folder='static', template_folder='templates')

def init_game(i_app, i_socketio):
    global _app
    _app = i_app

    global _game_redis
    _game_redis = redis.StrictRedis(host=_app.config["REDIS_HOSTNAME"],
                                   port=_app.config["REDIS_PORT"])

    _t = Thread(target=queue_reader.poll_game_cnfs, args=(_game_redis, get_cnfs_queue(), i_socketio))
    _t.daemon = True
    _t.start()

#TODO: Move requests to different file.
#TODO: Numbers..
def send_sync_req(game_id):
    push_req("sync-req", None, game_id)

def send_move_req(game_id, move):
    push_req("move-req", move, game_id)

def send_new_game_req(game_id, cd=1000):
    push_req("game-req", {"cd": cd}, game_id)

def get_app():
    return _app

def push_req(req, payload, game_id):
    q_id = get_app().config["REDIS_GAMES_REQ_QUEUE"]
    print("[{}] Requesting {} ({}) in {}".format(game_id, req,payload, q_id))
    _game_redis.rpush (q_id, json.dumps([game_id, req, payload]))
    _game_redis.expire(q_id, 3600)

def get_cnfs_queue():
    """ Get the cnfs queue used by the game manager. """
    return get_app().config["REDIS_GAMES_CNF_QUEUE"]

from . import routes, events
