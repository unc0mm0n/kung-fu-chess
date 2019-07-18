from threading import Thread
import uuid
import json
import time
import os
from collections import namedtuple

Env = namedtuple('Env', ["app", "socketio", "q", "db"])

import pytest
import redis
from flask_socketio import SocketIO, join_room, send

from web import create_app
from web.game.queue_reader import poll_game_cnfs, FAIL, SUCCESS

def get_client(env):
    client = env.socketio.test_client(env.app)
    client.connect(namespace="/game")
    return client

@pytest.fixture
def env():
    # start server
    os.environ["KFCHESS_CONFIG"] = os.path.join(os.path.dirname(__file__), "../config.py")
    app = create_app()
    socketio = SocketIO(app)
    def on_join(room):
        join_room(room, namespace="/game")
    socketio.on_event('join', on_join)

    # start polling thread
    game_resps_q = "resps:{}".format(uuid.uuid4())
    redis_db     = redis.StrictRedis()  #Todo: take redis from some configs
    t = Thread(target=poll_game_cnfs, args=(redis_db, game_resps_q, socketio))
    t.daemon = True
    t.start()
    yield Env(app=app, socketio=socketio, q=game_resps_q, db=redis_db)

def test_poll_reads_messages_and_responds(env):
    client = get_client(env)
    game_id = 1
    client.emit("join", game_id)
    env.db.rpush(env.q, json.dumps([game_id, 2, "move-cnf", {"state": "a", "move": "test"}]))
    env.db.expire(env.q, 10)
    time.sleep(0.1)

    assert env.db.llen(env.q) == 0
    received = client.get_received('/game')
    print(received)
    assert len(received) == 1
    assert len(received[0]['args']) == 1
    assert received[0]['args'][0]["move"] == "test"

def test_poll_sends_good_move_to_room(env):
    w_client = get_client(env)
    b_client = get_client(env)
    gid = 1
    wid = 2
    bid = 3
    w_client.emit("join", gid)
    w_client.emit("join", wid)
    b_client.emit("join", gid)
    b_client.emit("join", bid)
    time.sleep(0.01)

    env.db.rpush(env.q, json.dumps([gid, wid, "move-cnf", {"state" : "playing", "move": {"from": "e2", "to": "e4"}} ]))
    env.db.expire(env.q, 10)
    time.sleep(0.1)

    assert env.db.llen(env.q) == 0
    w_received = w_client.get_received('/game')
    b_received = b_client.get_received('/game')
    assert len(w_received) == 1 and len(b_received) == 1
    assert w_received == b_received
    assert w_received[0]['args'][0] == {"result": SUCCESS, "move": {"from": "e2", "to": "e4"}}

def test_poll_sends_bad_move_to_player(env):
    w_client = get_client(env)
    b_client = get_client(env)
    gid = 1
    wid = 2
    bid = 3
    w_client.emit("join", gid)
    w_client.emit("join", wid)
    b_client.emit("join", gid)
    b_client.emit("join", bid)
    time.sleep(0.01)

    env.db.rpush(env.q, json.dumps([gid, wid, "move-cnf", None]))
    env.db.expire(env.q, 10)
    time.sleep(0.1)

    assert env.db.llen(env.q) == 0
    w_received = w_client.get_received('/game')
    b_received = b_client.get_received('/game')
    assert len(w_received) == 1 and len(b_received) == 0
    assert w_received[0]['args'][0] == {"result": FAIL, "reason": "illegal move"}
