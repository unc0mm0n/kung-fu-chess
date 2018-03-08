import redis
import uuid
import time
import json
import itertools
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

def run_rgm(db, in_q, out_q):
    rgm = RedisGamesManager(db, in_q, out_q)
    print("running rgm")
    p = Process(target=rgm.run)
    p.daemon = False  # need children
    p.start()
    return p, rgm.games_queue

def test_manage_game_quits(db, in_q, out_q):
    p, games_in_q = run_rgm(db, in_q, out_q)
    db.rpush(in_q, json.dumps(["exit-req", None]))
    _, res  = db.blpop(out_q, 1)
    _, res2 = db.blpop(out_q, 1)
    assert res is not None and res2 is not None
    r, _ = json.loads(res)
    r2, _ = json.loads(res2)
    assert r == "exit-cnf"
    assert r2 == "exit-cnf"
    p.join(1)

def test_manage_game_cmd_game_req(db, in_q, out_q):
    p, games_in_q = run_rgm(db, in_q, out_q)
    db.rpush(in_q, json.dumps(["game-req", {"game_id": 1, "cd": 1000}]))
    _, res  = db.blpop(out_q, 1)
    print(res)
    r, d = json.loads(res)
    print(r)
    assert r == "game-cnf"
    assert d["in_queue"] == "{}:games".format(in_q)
    assert "1" in d["store_key"]

    db.rpush(in_q, json.dumps(["exit-req", None]))
    p.join(1)

def test_manage_game_invalid_commands(db, in_q, out_q):
    p, games_in_q = run_rgm(db, in_q, out_q)

    db.rpush(in_q, json.dumps(["game_req", {"game_id": 1, "cd": 1000}]))
    _, res  = db.blpop(out_q, 1)
    print(res)
    r, d = json.loads(res)
    assert r == "error-ind"

    db.rpush(in_q, json.dumps(["game-req", {"gameid": 1, "cd": 1000}]))
    _, res  = db.blpop(out_q, 1)
    r, d = json.loads(res)
    assert r == "error-ind"

    db.rpush(in_q, json.dumps(["game-req", {"game_id": 1}]))
    _, res  = db.blpop(out_q, 1)
    r, d = json.loads(res)
    assert r == "error-ind"

    db.rpush(in_q, json.dumps(["game-req", 1]))
    _, res  = db.blpop(out_q, 1)
    r, d = json.loads(res)
    assert r == "error-ind"

    db.rpush(in_q, json.dumps(["game-req", []]))
    _, res  = db.blpop(out_q, 1)
    r, d = json.loads(res)
    assert r == "error-ind"

    db.rpush(in_q, json.dumps(["game-req"]))
    _, res  = db.blpop(out_q, 1)
    r, d = json.loads(res)
    assert r == "error-ind"

    db.rpush(in_q, json.dumps(["exit-req", None]))
    _, res  = db.blpop(out_q, 1)
    _, res2 = db.blpop(out_q, 1)
    assert res is not None and res2 is not None
    r, _ = json.loads(res)
    r2, _ = json.loads(res2)
    assert r == "exit-cnf"
    assert r2 == "exit-cnf"
    p.join(1)

def test_manage_game_make_move(db, in_q, out_q):
    p, games_in_q = run_rgm(db, in_q, out_q)

    db.rpush(in_q, json.dumps(["game-req", {"game_id": 1, "cd": 1000}]))
    _, res  = db.blpop(out_q, 1)
    print(res)
    r, d = json.loads(res)
    g_in_q = d["in_queue"]
    db.rpush(g_in_q, json.dumps([1, "move-req", {"from": "e2", "to": "e4"}]))
    _, res = db.blpop(out_q, 1)
    print(res)
    assert False

    db.rpush(in_q, json.dumps(["exit-req", None]))
    _, res  = db.blpop(out_q, 1)
    _, res2 = db.blpop(out_q, 1)
    assert res is not None and res2 is not None
    r, _ = json.loads(res)
    r2, _ = json.loads(res2)
    assert r == "exit-cnf"
    assert r2 == "exit-cnf"
    p.join(1)
"""
def test_manage_game_correct_response_to_exit():
    rgm = RedisGamesManager(redis_db, out_q)
    kfc = KungFuChess.FromNfen(0, **gen_nfen_args())
    in_q = "in:{}".format(uuid.uuid4())
    rgm.manage_game(kfc, 1, 0, 1, in_q)
    redis_db.rpush(in_q, json.dumps([1, "exit-req", None]))
    _, resp = redis_db.blpop(out_q, timeout=1)
    gid, cmd, data = json.loads(resp)
    assert redis_db.llen(in_q) == 0
    assert redis_db.llen(out_q) == 0
    assert gid == 1
    assert cmd == "exit-cnf"
    assert data is None
    time.sleep(0.1)  # for obvious reasons, exit happens after cnf
    assert not rgm._p[0].is_alive()

def test_manage_game_reads_and_responds_to_move():
    rgm = RedisGamesManager(redis_db, out_q)
    kfc = KungFuChess.FromNfen(0, **gen_nfen_args())
    in_q = "in:{}".format(uuid.uuid4())
    rgm.manage_game(kfc, 1, 0, 1, in_q)
    redis_db.rpush(in_q, json.dumps([1, "move-req", [1, {"from": 3,
                                "to": 2}]]))
    time.sleep(0.1)
    assert redis_db.llen(in_q) == 0
    assert redis_db.llen(out_q) == 1
    redis_db.expire(out_q, 0)
    rgm._p[0].terminate()

def test_manage_game_correct_response_to_move():
    rgm = RedisGamesManager(redis_db, out_q)
    kfc = KungFuChess.FromNfen(0, **gen_nfen_args())
    in_q = "in:{}".format(uuid.uuid4())
    rgm.manage_game(kfc, 1, 0, 1, in_q)

    # Test legal moves
    moves = [(0, 'e2', 'e4', PAWN), (1, 'e7', 'e5', PAWN), (0,'f1', 'c4', BISHOP), (0, 'g1', 'f3', KNIGHT), (0, 'e1', 'g1', KING)]
    for player, fr, to, piece in moves:
        redis_db.rpush(in_q, json.dumps([1, "move-req", [player, {"from": fr,
                                    "to": to}]]))
    for player, fr, to, piece in moves:
        _, resp = redis_db.blpop(out_q, timeout=1)
        print(resp)
        assert resp is not None
        gid, cmd, data = json.loads(resp)
        assert gid == 1
        assert cmd == "move-cnf"
        assert data is not None

        player_id, move = data
        assert player_id == player
        assert "from" in move and "to" in move and "time" in move and "promote" in move
        assert move["from"] == fr and move["to"] == to
        assert kfc[fr].type == EMPTY
        assert kfc[to].type == piece
        assert kfc[to].color == WHITE if player == 0 else BLACK
    assert redis_db.llen(out_q) == 0

    # Test illegal moves
    moves = [(0, 'e4', 'e3', PAWN, EMPTY), (1, 'e5', 'e4', PAWN, PAWN), (1,'c4', 'c5', BISHOP, EMPTY), (1, 'f3', 'g1', KNIGHT, KING), (0, 'f3', 'g1', KNIGHT, KING), (1, 'f3', 'h4', KNIGHT, EMPTY)]
    for player, fr, to, piece, to_piece in moves:
        redis_db.rpush(in_q, json.dumps([1, "move-req", [player, {"from": fr,
                                    "to": to}]]))
        _, resp = redis_db.blpop(out_q, timeout=1)
        print(resp)
        assert resp is not None
        gid, cmd, data = json.loads(resp)
        assert gid == 1
        assert cmd == "move-cnf"
        assert data is not None

        player_id, move = data
        assert player_id == player
        assert move is None
        assert kfc[fr].type == piece
        assert kfc[to].type == to_piece
    assert redis_db.llen(out_q) == 0

    # crazier illegal moves
    sqs = [None, 'a', 'a1', 'e2', -1, 8, 9, '4e', '44', '4', 91987849237498236597123, 'e2e4']
    moves = list(itertools.product((0,1), sqs, sqs))
    ascii = kfc._board.ascii
    for p, f, t in moves:
        redis_db.rpush(in_q, json.dumps([1, "move-req", [p, {"from": f, "to": t}]]))
    for p, f, t in moves:
        _, resp = redis_db.blpop(out_q, timeout=1)
        assert resp is not None
        gid, cmd, data = json.loads(resp)
        assert gid == 1
        assert cmd == "move-cnf"
        assert data is not None

        player_id, move = data
        assert player_id == p
        assert move is None
    assert redis_db.llen(out_q) == 0
    assert ascii == kfc._board.ascii  # make sure board wasn't changed
    # Test illegal moves
    redis_db.expire(out_q, 0)
    rgm._p[0].terminate()
 """
