import redis
import uuid
import time
import json
import itertools
import random
import functools
from multiprocessing import Process

import pytest

from kfchess.game import *
from kfchess.redis_games_manager import RedisGamesManager

#Todo: get this from config to be setup dependant
@pytest.fixture
def db():
    _db = redis.StrictRedis()
    return _db

@pytest.fixture
def in_q():
    return "in:{}".format(uuid.uuid4())

@pytest.fixture
def out_q():
    return "out:{}".format(uuid.uuid4())

@pytest.fixture
def rgm(db, in_q, out_q):
    suffix = uuid.uuid4()
    prefix="manager:{}:".format(suffix) + "games:{}"
    print("******", db, in_q, out_q)
    rgm = RedisGamesManager(db, in_q, out_q, key_base_suffix=suffix)
    p = Process(target=rgm.run)
    p.daemon = True
    p.start()
    yield (db, in_q, out_q, prefix)
    db.rpush(in_q, json.dumps([-1, -1, "exit-req", None]))
    try:
        _, res  = db.blpop(out_q, 1)
    except:
        pass
    #p.join(2)
    db.pexpire(in_q, 0)

@pytest.fixture
def game_id():
    return random.randint(1,999999999999999)

def test_manage_game_quits(rgm):
    db, in_q, out_q, prefix = rgm
    db.rpush(in_q, json.dumps([-1, -1, "exit-req", None]))
    _, res  = db.blpop(out_q, 1)
    print(res)
    assert res is not None
    r, _ = json.loads(res)
    assert r == "exit-cnf"

def test_manage_game_cmd_game_req(rgm, game_id):
    db, in_q, out_q, prefix = rgm

    db.rpush(in_q, json.dumps([game_id, 0, "game-req", {"cd": 1000}]))
    _, res  = db.blpop(out_q, 1)
    print(res)
    i, p, r, d = json.loads(res)
    print(r)
    assert r == "game-cnf"
    assert i == game_id

def test_manage_game_invalid_commands(rgm, game_id):
    db, in_q, out_q, prefix = rgm

    db.rpush(in_q, json.dumps([game_id, 0, "game_req", {"cd": 1000}]))
    _, res  = db.blpop(out_q, 1)
    print(res)
    i, p, r, d = json.loads(res)
    assert i == -1
    assert r == "error-ind"

    db.rpush(in_q, json.dumps(["game-req", 0, {"gameid": 1, "cd": 1000}]))
    _, res  = db.blpop(out_q, 1)
    _, _, r, d = json.loads(res)
    assert r == "error-ind"

    db.rpush(in_q, json.dumps(["game-req", 0, {"game_id": 1, "cd": 1000}]))
    _, res  = db.blpop(out_q, 1)
    _, _, r, d = json.loads(res)
    assert r == "error-ind"

    db.rpush(in_q, json.dumps([game_id, 0, "game-req", {}]))
    _, res  = db.blpop(out_q, 1)
    _, _, r, d = json.loads(res)
    assert r == "error-ind"

    db.rpush(in_q, json.dumps(["game-req", 1]))
    _, res  = db.blpop(out_q, 1)
    _, _, r, d = json.loads(res)
    assert r == "error-ind"

    db.rpush(in_q, json.dumps(["game-req", []]))
    _, res  = db.blpop(out_q, 1)
    _, _, r, d = json.loads(res)
    assert r == "error-ind"

    db.rpush(in_q, json.dumps(["game-req"]))
    _, res  = db.blpop(out_q, 1)
    _, _, r, d = json.loads(res)
    assert r == "error-ind"

    db.rpush(in_q, json.dumps(["game-req", game_id, 0, {"cd": 1000}]))
    _, res  = db.blpop(out_q, 1)
    _, _, r, d = json.loads(res)
    assert r == "error-ind"

def test_manage_game_make_move(rgm, game_id):
    db, in_q, out_q, prefix = rgm

    db.rpush(in_q, json.dumps([game_id, 0, "game-req", {"cd": 1000}]))
    db.rpush(in_q, json.dumps([game_id, 1, "join-req", {"cd": 1000}]))

    _, res = db.blpop(out_q, 1)
    _, res = db.blpop(out_q, 1)

    db.rpush(in_q, json.dumps([game_id, 0, "move-req", {"from": "e2", "to": "e4"}]))
    _, res = db.blpop(out_q, 1)
    res = json.loads(res)
    assert len(res) == 4
    assert res[0] == game_id
    assert res[2] == "move-cnf"

def test_manage_game_make_move_illegal(rgm, game_id):
    db, in_q, out_q, prefix = rgm

    db.rpush(in_q, json.dumps([game_id, 0, "game-req", {"cd": 1000}]))
    db.rpush(in_q, json.dumps([game_id, 1, "join-req", {"cd": 1000}]))
    _, res  = db.blpop(out_q, 1)
    _, res  = db.blpop(out_q, 1)

    db.rpush(in_q, json.dumps([game_id, 0, "move-req", {"from": "e2", "to": "e1"}]))
    _, res = db.blpop(out_q, 1)
    res = json.loads(res)
    print(res)
    assert len(res) == 4
    assert res[0] == game_id
    assert res[2] == "move-cnf"
    assert res[3] == None
    
    db.rpush(in_q, json.dumps([game_id, 1, "move-req", {"from": "e2", "to": "e4"}]))
    _, res = db.blpop(out_q, 1)
    res = json.loads(res)
    assert len(res) == 4
    assert res[0] == game_id
    assert res[2] == "move-cnf"
    assert res[3] == None

def test_manage_game_sync_req(rgm, game_id):
    db, in_q, out_q, prefix = rgm

    db.rpush(in_q, json.dumps([game_id, 0, "game-req", {"cd": 1000}]))
    db.rpush(in_q, json.dumps([game_id, 1, "join-req", {"cd": 1000}]))
    _, res  = db.blpop(out_q, 1)
    _, res  = db.blpop(out_q, 1)

    db.rpush(in_q, json.dumps([game_id, 0, "sync-req", None]))
    _, res = db.blpop(out_q, 1)
    res = json.loads(res)
    print(res)
    assert len(res) == 4
    assert res[0] == game_id
    assert res[2] == "sync-cnf"
    assert not res[3]["board"]["times"]

    db.rpush(in_q, json.dumps([game_id, 0, "move-req", {"from": "e2", "to": "e4"}]))
    db.blpop(out_q, 1)

    db.rpush(in_q, json.dumps([game_id, 0, "sync-req", None]))
    _, res = db.blpop(out_q, 1)
    res = json.loads(res)
    assert len(res) == 4
    assert res[0] == game_id
    assert res[2] == "sync-cnf"
    assert "e4" in res[3]["board"]["times"]


    db.rpush(in_q, json.dumps([game_id-1, 0, "sync-req", None]))
    _, res = db.blpop(out_q, 1)
    res = json.loads(res)
    print(res)
    assert len(res) == 4
    assert res[0] == game_id-1
    assert res[2] == "sync-cnf"
    assert res[3] == None

    db.rpush(in_q, json.dumps(["exit-req", None]))

def test_manage_game_correct_response_to_move(game_id, rgm):
    db, in_q, out_q, prefix = rgm

    db.rpush(in_q, json.dumps([game_id, 0, "game-req", {"cd": 1000}]))
    db.rpush(in_q, json.dumps([game_id, 1, "join-req", {"cd": 1000}]))

    print(prefix.format(game_id))
    kfc = get_board(db, prefix.format(game_id))
    _, res  = db.blpop(out_q, 1)
    _, res  = db.blpop(out_q, 1)

    # Test legal moves
    moves = [(0, 'e2', 'e4', PAWN), (1, 'e7', 'e5', PAWN), (0,'f1', 'c4', BISHOP), (0, 'g1', 'f3', KNIGHT), (0, 'e1', 'g1', KING)]
    for player, fr, to, piece in moves:
        db.rpush(in_q, json.dumps([game_id, player, "move-req", {"from": fr,
                                    "to": to}]))
        _, resp = db.blpop(out_q, timeout=1)
        print(resp)
        assert resp is not None
        gid, pid, cmd, data = json.loads(resp)
        assert gid == game_id
        assert pid == player
        assert cmd == "move-cnf"
        assert data is not None

        state = data["state"]
        move = data["move"]
        assert state == PLAYING
        assert "from" in move and "to" in move and "time" in move and "promote" in move
        assert move["from"] == fr and move["to"] == to
        print(fr, to)
        print(kfc.ascii)
        assert kfc[Square.FromSan(fr)].type == EMPTY
        assert kfc[Square.FromSan(to)].type == piece
        assert kfc[Square.FromSan(to)].color == WHITE if player == 0 else BLACK
    assert db.llen(out_q) == 0

    # Test illegal moves
    moves = [(0, 'e4', 'e3', PAWN, EMPTY), (1, 'e5', 'e4', PAWN, PAWN), (1,'c4', 'c5', BISHOP, EMPTY), (1, 'f3', 'g1', KNIGHT, KING), (0, 'f3', 'g1', KNIGHT, KING), (1, 'f3', 'h4', KNIGHT, EMPTY), (1, 'e4', 'e5', PAWN, PAWN)]
    for player, fr, to, piece, to_piece in moves:
        db.rpush(in_q, json.dumps([game_id, player, "move-req", {"from": fr,
                                    "to": to}]))
        _, resp = db.blpop(out_q, timeout=1)
        assert resp is not None
        gid, pid, cmd, data = json.loads(resp)
        assert gid == game_id
        assert pid == player
        assert cmd == "move-cnf"
        assert data is None

    assert db.llen(out_q) == 0

    # crazier illegal moves
    sqs = [None, 'a', 'a1', 'e2', -1, 8, 9, '4e', '44', '4', 91987849237498236597123, 'e2e4']
    moves = list(itertools.product((0,1,2), sqs, sqs))
    for p, f, t in moves:
        print(p, f, t)
        db.rpush(in_q, json.dumps([game_id, p, "move-req", {"from": f, "to": t}]))
        _, resp = db.blpop(out_q, timeout=1)
        assert resp is not None
        print(resp)
        gid, pid, cmd, data = json.loads(resp)
        assert gid == game_id
        assert pid == p
        assert cmd == "move-cnf"
        assert data is None

    assert db.llen(out_q) == 0
