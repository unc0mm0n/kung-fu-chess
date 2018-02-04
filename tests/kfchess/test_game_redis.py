from itertools import product
import time
import redis
import uuid
import pytest

from kfchess.game import *

# Todo: Get this from config to be setup dependant
redis_db = redis.StrictRedis()

def gen_nfen_args(exp=100):
    return {
        'board_class': RedisKungFuBoard,
        'redis_db': redis_db,
        'store_key': "board_tmp:{}".format(uuid.uuid4()),
        'exp': exp
}


def test_FromNfen():
    kfc = KungFuChess.FromNfen(0, **gen_nfen_args())
    assert kfc._board.ascii == "rnbqkbnr\npppppppp\n........\n........\n........\n........\nPPPPPPPP\nRNBQKBNR\n"

    kfc = KungFuChess.FromNfen(0, "3b4/NP6/rp2k1B1/2R3P1/3K4/2B2Q2/P1P3P1/4r3 - 1", **gen_nfen_args())
    assert kfc._board.ascii == "...b....\nNP......\nrp..k.B.\n..R...P.\n...K....\n..B..Q..\nP.P...P.\n....r...\n"

    with pytest.raises(ValueError):
       KungFuChess.FromNfen(1000, "r6r/pbppqppp/1pn2n2/4p3/1bB5/2NPPN2/PPPBQPPP/R6R KQkq 8", **gen_nfen_args())

    with pytest.raises(ValueError):
        KungFuChess.FromNfen(1000, "r3K2r/pbppqppp/1pn2n2/4p3/1bB5/2NPPN2/PPPBQPPP/R3K2R KQkq 8", **gen_nfen_args())

    with pytest.raises(ValueError):
        KungFuChess.FromNfen(1000, "r3k2r/pbppqppp/1pn1Kn2/4p3/1bB5/2NPPN2/PPPBQPPP/R3K2R KQkq 8", **gen_nfen_args())

def test_board_fen():
    kfc = KungFuChess.FromNfen(0, **gen_nfen_args())
    assert kfc._board.fen == "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"

    kfc = KungFuChess.FromNfen(1000, "r3k2r/pbppqppp/1pn2n2/4p3/1bB5/2NPPN2/PPPBQPPP/R3K2R KQkq 8", **gen_nfen_args())
    assert kfc._board.fen == "r3k2r/pbppqppp/1pn2n2/4p3/1bB5/2NPPN2/PPPBQPPP/R3K2R"

    kfc = KungFuChess.FromNfen(1000, "r3k2r/pbppqppp/1pn2n2/4p3/1bB5/2NPPN2/PPPBQPPP/R6R KQkq 8", **gen_nfen_args())
    assert kfc._board.fen == "r3k2r/pbppqppp/1pn2n2/4p3/1bB5/2NPPN2/PPPBQPPP/R6R"

    kfc = KungFuChess.FromNfen(1000, "r6r/pbppqppp/1pn2n2/4p3/1bB5/2NPPN2/PPPBQPPP/R3K2R KQkq 8", **gen_nfen_args())
    assert kfc._board.fen == "r6r/pbppqppp/1pn2n2/4p3/1bB5/2NPPN2/PPPBQPPP/R3K2R"

    kfc = KungFuChess.FromNfen(0, "3b4/NP6/rp2k1B1/2R3P1/3K4/2B2Q2/P1P3P1/4r3 - 1", **gen_nfen_args())
    assert kfc._board.fen == "3b4/NP6/rp2k1B1/2R3P1/3K4/2B2Q2/P1P3P1/4r3"

def test_board_get_piece():
    board = KungFuChess.FromNfen(0, **gen_nfen_args())._board
    sq = Square.FromSan('e2')
    assert board.get_piece(sq).type == PAWN

def test_expires():
    kwargs = gen_nfen_args()
    key = kwargs['store_key']
    game = KungFuChess.FromNfen(0, **kwargs)
    assert redis_db.pttl(key) > 0
    time.sleep(0.1)
    assert redis_db.pttl(key) == -2

def test_move_refresh_expire():
    kwargs = gen_nfen_args(exp=200)
    key = kwargs['store_key']
    game = KungFuChess.FromNfen(0, **kwargs)
    time.sleep(0.1)
    ttl = redis_db.pttl(key)
    assert ttl > 0
    game.move('e2', 'e4')
    ttl2 = redis_db.pttl(key)
    assert ttl2 > ttl
    time.sleep(0.3)
    assert redis_db.pttl(key) == -2
