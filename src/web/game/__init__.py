from threading import Thread
import json

import redis
from flask import Blueprint

from . import queue_reader

game_bp = Blueprint('game', __name__, static_folder='static')

def init_game(i_app, i_socketio):
    global _app
    _app = i_app

    global _game_redis
    _game_redis = redis.StrictRedis(host=_app.config["REDIS_HOSTNAME"],
                                   port=_app.config["REDIS_PORT"])

    from kfchess.redis_games_manager import RedisGamesManager
    global _game_manager
    _game_manager = RedisGamesManager(_game_redis, get_cnfs_queue(0))

    _t = Thread(target=queue_reader.poll_game_cnfs, args=(_game_redis, get_cnfs_queue(0), i_socketio))
    _t.daemon = True
    _t.start()

def get_game_redis():
    return _game_redis

def get_game_manager():
    return _game_manager

def get_app():
    return _app

def push_req(req, payload, game_id):
    q_id = get_reqs_queue(game_id)
    print("[{}] Requesting {} in {}".format(game_id, req, q_id))
    _game_redis.rpush (q_id, json.dumps([game_id, req, payload]))
    _game_redis.expire(q_id, 3600)

def get_store_key(game_id):
    """ Gets the store key for given game id. """
    return "{}:{}".format(get_app().config["REDIS_GAMES_STORE"], game_id)

def get_reqs_queue(game_id):
    """ Get the reqs queue for given game id. """
    return "{}:{}".format(get_store_key(game_id), get_app().config["REDIS_GAMES_REQ_QUEUE"])

def get_cnfs_queue(game_id):
    """ Get the cnfs queue of given id. If id is 0 returns the default cnfs queue. (actually now always returns the default one). """
    return "{}:{}".format(get_app().config["REDIS_GAMES_STORE"], get_app().config["REDIS_GAMES_CNF_QUEUE"])

from . import routes, events
