import redis
import uuid
import time
import json
import itertools

import pytest

from kfchess.game import *
from kfchess.redis_games_manager import RedisGamesManager

#Todo: get this from config to be setup dependant
redis_db = redis.StrictRedis()
out_q = "out:{}".format(uuid.uuid4())

def gen_nfen_args(exp=100):
    return {
        'board_class': RedisKungFuBoard,
        'redis_db': redis_db,
        'store_key': "board_tmp:{}".format(uuid.uuid4()),
        'exp': exp
}

def test_manage_game_creates_process():
    rgm = RedisGamesManager(redis_db, out_q)
    kfc = KungFuChess.FromNfen(0, **gen_nfen_args())
    in_q = "in:{}".format(uuid.uuid4())
    rgm.manage_game(kfc, 1, 0, 1, in_q)
    assert len(rgm._p) == 1
    assert rgm._p[0].name == "game:1"
    assert rgm._p[0].is_alive()
    rgm._p[0].terminate()

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
