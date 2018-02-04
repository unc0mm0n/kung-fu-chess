from itertools import product
import time
import uuid

import redis
import pytest

from kfchess.game import *

@pytest.fixture
def db():
    _db = redis.StrictRedis()
    return _db

@pytest.fixture
def key():
    return uuid.uuid4()

def test_square_to_rank():
    for r, c in product(range(8), range(8)):
        assert Square(16*r + c).rank == r + 1

def test_square_from_san():
    assert Square.FromSan('a1') == 0
    assert Square.FromSan('e2') == 16 * 1 + 4
    assert Square.FromSan('a7') == 16 * 6
    assert Square.FromSan('c7') == 16 * 6 + 2

def test_square_from_file_rank():
    assert Square.FromFileRank(1, 1) == 0         # a1
    assert Square.FromFileRank(3, 7) == 16*6 + 2  # c7
    assert Square.FromFileRank(1, 7) == 16*6      # a7

def test_square_san():
    for r, c in product(range(8), range(8)):
        e = '{}{}'.format(chr(r + ord('a')), c + 1)
        assert Square.FromSan(e).san == e

def test_square_valid():
    for r, c in product(range(8), range(8)):
        e = '{}{}'.format(chr(r + ord('a')), c + 1)
        assert Square.FromSan(e).valid


def test_FromNfen(db, key):
    board = create_game_from_nfen(db, 0, key, exp=5000)
    assert board.ascii == "rnbqkbnr\npppppppp\n........\n........\n........\n........\nPPPPPPPP\nRNBQKBNR\n"

    board = create_game_from_nfen(db, 0, key, exp=5000, nfen="3b4/NP6/rp2k1B1/2R3P1/3K4/2B2Q2/P1P3P1/4r3 - 1")
    assert board.ascii == "...b....\nNP......\nrp..k.B.\n..R...P.\n...K....\n..B..Q..\nP.P...P.\n....r...\n"

    with pytest.raises(ValueError):
        create_game_from_nfen(db, 1000, key, exp=5000, nfen="r6r/pbppqppp/1pn2n2/4p3/1bB5/2NPPN2/PPPBQPPP/R6R KQkq 8")

    with pytest.raises(ValueError):
        create_game_from_nfen(db, 1000, key, exp=5000, nfen="r3K2r/pbppqppp/1pn2n2/4p3/1bB5/2NPPN2/PPPBQPPP/R3K2R KQkq 8")

    with pytest.raises(ValueError):
        create_game_from_nfen(db, 1000, key, exp=5000, nfen="r3k2r/pbppqppp/1pn1Kn2/4p3/1bB5/2NPPN2/PPPBQPPP/R3K2R KQkq 8")

def test_board_fen(db, key):
    board = create_game_from_nfen(db, 0, key, exp=5000)
    assert board.fen == "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"

    board = create_game_from_nfen(db, 1000, key, exp=5000, nfen="r3k2r/pbppqppp/1pn2n2/4p3/1bB5/2NPPN2/PPPBQPPP/R3K2R KQkq 8")
    assert board.fen == "r3k2r/pbppqppp/1pn2n2/4p3/1bB5/2NPPN2/PPPBQPPP/R3K2R"

    board = create_game_from_nfen(db, 1000, key, exp=5000, nfen="r3k2r/pbppqppp/1pn2n2/4p3/1bB5/2NPPN2/PPPBQPPP/R6R KQkq 8")
    assert board.fen == "r3k2r/pbppqppp/1pn2n2/4p3/1bB5/2NPPN2/PPPBQPPP/R6R"

    board = create_game_from_nfen(db, 1000, key, exp=5000, nfen="r6r/pbppqppp/1pn2n2/4p3/1bB5/2NPPN2/PPPBQPPP/R3K2R KQkq 8")
    assert board.fen == "r6r/pbppqppp/1pn2n2/4p3/1bB5/2NPPN2/PPPBQPPP/R3K2R"

    board = create_game_from_nfen(db, 0, key, exp=5000, nfen="3b4/NP6/rp2k1B1/2R3P1/3K4/2B2Q2/P1P3P1/4r3 - 1")
    assert board.fen == "3b4/NP6/rp2k1B1/2R3P1/3K4/2B2Q2/P1P3P1/4r3"

def test_board_get_piece(db, key):
    board = create_game_from_nfen(db, 0, key, exp=5000)
    sq = Square.FromSan('e2')
    assert board[sq].type == PAWN
    assert board[sq].color == WHITE

def test_create_pawn_moves_regular(db, key):
    board = create_game_from_nfen(db, 0, key, exp=5000)
    from_sq = Square.FromSan('e2')
    to_sq = Square.FromSan('e3')
    res = [m.to_sq.san for m in create_pawn_moves(from_sq, to_sq, WHITE)]
    ex  = ['e3']
    for m in res:
        assert m in ex
    for m in ex:
        assert m in res

    from_sq = Square.FromSan('e2')
    to_sq = Square.FromSan('e4')
    res = [m.to_sq.san for m in create_pawn_moves(from_sq, to_sq, WHITE)]
    ex = ['e4']
    for m in res:
        assert m in ex
    for m in ex:
        assert m in res

    from_sq = Square.FromSan('e7')
    to_sq = Square.FromSan('e6')
    res = [m.to_sq.san for m in create_pawn_moves(from_sq, to_sq, BLACK)]
    ex = ['e6']
    for m in res:
        assert m in ex
    for m in ex:
        assert m in res

    from_sq = Square.FromSan('e7')
    to_sq = Square.FromSan('e5')
    res = [m.to_sq.san for m in create_pawn_moves(from_sq, to_sq, BLACK)]
    ex = ['e5']
    for m in res:
        assert m in ex
    for m in ex:
        assert m in res

def test_create_pawn_moves_promote(db, key):
    board = create_game_from_nfen(db, 0, key, exp=5000)

    from_sq = Square.FromSan('e7')
    to_sq = Square.FromSan('e8')
    res = [m.promote for m in create_pawn_moves(from_sq, to_sq, WHITE)]
    print(res)
    ex = [QUEEN, BISHOP, KNIGHT, ROOK]
    for m in res:
        assert m in ex
    for m in ex:
        assert m in res

    from_sq = Square.FromSan('e2')
    to_sq = Square.FromSan('f1')
    res = [m.promote for m in create_pawn_moves(from_sq, to_sq, BLACK)]
    print(res)
    ex = [QUEEN, BISHOP, KNIGHT, ROOK]
    for m in res:
        assert m in ex
    for m in ex:
        assert m in res

def test_moves_basic(db, key):
    board = create_game_from_nfen(db, 0, key, exp=5000)

    res = [m.to_sq.san for m in moves(db, key, 'e2')]
    ex  = ['e3', 'e4']
    for m in res:
        assert m in ex
    for m in ex:
        assert m in res

    res = [m.to_sq.san for m in moves(db, key, 'g1')]
    ex = ['f3', 'h3']
    for m in res:
        assert m in ex
    for m in ex:
        assert m in res

    res = [m.to_sq.san for m in moves(db, key, 'b8')]
    ex = ['a6', 'c6']
    for m in res:
        assert m in ex
    for m in ex:
        assert m in res

    res = [m.to_sq.san for m in moves(db, key, 'h8')]
    ex = []
    for m in res:
        assert m in ex
    for m in ex:
        assert m in res

def test_moves_advanced(db, key):
    board = create_game_from_nfen(db, 0, key, exp=5000, nfen="3b4/NP6/rp2k1B1/2R3P1/3K4/2B2Q2/P1P3P1/4r3 - 1")
    print(board.ascii)

    res = [m.to_sq.san for m in moves(db, key, 'e6')]  # no castles
    ex = ['d7', 'd6', 'd5', 'e7', 'e5', 'f7', 'f6', 'f5']
    assert(len(res) == len(ex))
    for m in res:
        assert m in ex
    for m in ex:
        assert m in res

    res = [m.to_sq.san for m in moves(db, key, 'b7')]
    ex = ['b8']
    assert(len(res) == 4)  # promotions
    for m in res:
        assert m in ex
    for m in ex:
        assert m in res

    moves_res = moves(db, key, 'a6')
    print(moves_res)
    sq_res = [m.to_sq.san for m in moves_res]
    print(sq_res)
    ex = ['a7', 'a5', 'a4', 'a3', 'a2']
    assert(len(sq_res) == len(ex))  # captures only enemy pieces
    for m in sq_res:
        assert m in ex
    for m in ex:
        assert m in sq_res

    print(moves_res)
    assert len(list(filter(lambda x: x.captured, [m for m in moves_res]))) == 2  # only two capture moves

    board = create_game_from_nfen(db, 0, key, exp=5000, nfen="r3k2r/pbppqppp/1pn2n2/4p3/1bB5/2NPPN2/PPPBQPPP/R3K2R KQkq 8")
    print(board.ascii)
    res = [m.to_sq.san for m in moves(db, key, 'e1')]  # yes castles
    ex = ['d1', 'f1', 'c1', 'g1']
    assert (len(res) == len(ex))
    for m in res:
        assert m in ex
    for m in ex:
        assert m in res

    res = [m.to_sq.san for m in moves(db, key, 'e8')]  # yes castles
    ex = ['d8', 'f8', 'c8', 'g8']
    assert (len(res) == len(ex))
    for m in res:
        assert m in ex
    for m in ex:
        assert m in res

def test_move_simple(db, key):
    board = create_game_from_nfen(db, 0, key, exp=5000)
    move(db, key, 'e2', 'e4')
    assert board.ascii == "rnbqkbnr\n" \
                               "pppppppp\n" \
                               "........\n" \
                               "........\n" \
                               "....P...\n" \
                               "........\n" \
                               "PPPP.PPP\n" \
                               "RNBQKBNR\n"

    move(db, key, 'f1', 'c4')
    assert board.ascii == "rnbqkbnr\n" \
                               "pppppppp\n" \
                               "........\n" \
                               "........\n" \
                               "..B.P...\n" \
                               "........\n" \
                               "PPPP.PPP\n" \
                               "RNBQK.NR\n"

    move(db, key, 'g1', 'f3')
    assert board.ascii == "rnbqkbnr\n" \
                               "pppppppp\n" \
                               "........\n" \
                               "........\n" \
                               "..B.P...\n" \
                               ".....N..\n" \
                               "PPPP.PPP\n" \
                               "RNBQK..R\n"

    move(db, key, 'e1', 'g1')       # castle
    assert board.ascii == "rnbqkbnr\n" \
                               "pppppppp\n" \
                               "........\n" \
                               "........\n" \
                               "..B.P...\n" \
                               ".....N..\n" \
                               "PPPP.PPP\n" \
                               "RNBQ.RK.\n"

    move(db, key, 'g8', 'h6')
    move(db, key, 'e7', 'e6')
    move(db, key, 'f8', 'e7')
    assert board.ascii == "rnbqk..r\n" \
                               "ppppbppp\n" \
                               "....p..n\n" \
                               "........\n" \
                               "..B.P...\n" \
                               ".....N..\n" \
                               "PPPP.PPP\n" \
                               "RNBQ.RK.\n"

    assert move(db, key, 'h8', 'f8') is not None
    assert move(db, key, 'f8', 'h8') is not None
    assert board.ascii == "rnbqk..r\n" \
                               "ppppbppp\n" \
                               "....p..n\n" \
                               "........\n" \
                               "..B.P...\n" \
                               ".....N..\n" \
                               "PPPP.PPP\n" \
                               "RNBQ.RK.\n"

    assert move(db, key, 'e8', 'g8') is None  # no castle after rook move

def test_moves_pawn_capture(db, key):
    board = create_game_from_nfen(db, 0, key, exp=5000)
    move(db, key, 'e2', 'e4')
    move(db, key, 'f7', 'f5')
    move(db, key, 'd7', 'd5')
    assert board.ascii == "rnbqkbnr\n" \
                               "ppp.p.pp\n" \
                               "........\n" \
                               "...p.p..\n" \
                               "....P...\n" \
                               "........\n" \
                               "PPPP.PPP\n" \
                               "RNBQKBNR\n"

    print(board.ascii)
    res = [m.to_sq.san for m in moves(db, key, 'e4')]  # pawn captures
    ex = ['d5', 'e5', 'f5']
    assert (len(res) == len(ex))
    for m in res:
        assert m in ex
    for m in ex:
        assert m in res

    assert move(db, key, 'e4', 'd5') is not None
    assert board.ascii == "rnbqkbnr\n" \
                               "ppp.p.pp\n" \
                               "........\n" \
                               "...P.p..\n" \
                               "........\n" \
                               "........\n" \
                               "PPPP.PPP\n" \
                               "RNBQKBNR\n"

def test_move_time_delay(db, key):
    board = create_game_from_nfen(db, 100, key, exp=5000)  # delay between moves in ms
    move(db, key, 'e2', 'e4')
    assert board.ascii == "rnbqkbnr\n" \
                               "pppppppp\n" \
                               "........\n" \
                               "........\n" \
                               "....P...\n" \
                               "........\n" \
                               "PPPP.PPP\n" \
                               "RNBQKBNR\n"

    assert move(db, key, 'e4', 'e5') is None
    assert board.ascii == "rnbqkbnr\n" \
                               "pppppppp\n" \
                               "........\n" \
                               "........\n" \
                               "....P...\n" \
                               "........\n" \
                               "PPPP.PPP\n" \
                               "RNBQKBNR\n"

    time.sleep(0.1)  # should be fine now (sleep is in secs)

    assert move(db, key, 'e4', 'e5') is not None
    assert board.ascii == "rnbqkbnr\n" \
                               "pppppppp\n" \
                               "........\n" \
                               "....P...\n" \
                               "........\n" \
                               "........\n" \
                               "PPPP.PPP\n" \
                               "RNBQKBNR\n"

def test_move_castle_rook_delayed(db, key):
    board = create_game_from_nfen(db, 100, key, exp=5000, nfen="r3k2r/pbppqppp/1pn2n2/4p3/1bB5/2NPPN2/PPPBQPPP/R3K2R KQkq 8")
    assert board.ascii == "r...k..r\n" \
                               "pbppqppp\n" \
                               ".pn..n..\n" \
                               "....p...\n" \
                               ".bB.....\n" \
                               "..NPPN..\n" \
                               "PPPBQPPP\n" \
                               "R...K..R\n"

    move(db, key, 'e1', 'g1')
    assert board.ascii == "r...k..r\n" \
                               "pbppqppp\n" \
                               ".pn..n..\n" \
                               "....p...\n" \
                               ".bB.....\n" \
                               "..NPPN..\n" \
                               "PPPBQPPP\n" \
                               "R....RK.\n"

    assert move(db, key, 'f1', 'e1') is None

    time.sleep(0.1)  # should be fine now (sleep is in secs)

    assert move(db, key, 'f1', 'e1') is not None
    assert board.ascii == "r...k..r\n" \
                               "pbppqppp\n" \
                               ".pn..n..\n" \
                               "....p...\n" \
                               ".bB.....\n" \
                               "..NPPN..\n" \
                               "PPPBQPPP\n" \
                               "R...R.K.\n"

def test_game_winner_setup(db, key):
    board = create_game_from_nfen(db, 1000, key, exp=5000, nfen="r3k2r/pbppqppp/1pn2n2/4p3/1bB5/2NPPN2/PPPBQPPP/R3K2R KQkq 8")
    assert board.ascii == "r...k..r\n" \
                               "pbppqppp\n" \
                               ".pn..n..\n" \
                               "....p...\n" \
                               ".bB.....\n" \
                               "..NPPN..\n" \
                               "PPPBQPPP\n" \
                               "R...K..R\n"

    assert board.winner == None

    board = create_game_from_nfen(db, 1000, key, exp=5000, nfen="r3k2r/pbppqppp/1pn2n2/4p3/1bB5/2NPPN2/PPPBQPPP/R6R KQkq 8")

    assert board.ascii == "r...k..r\n" \
                               "pbppqppp\n" \
                               ".pn..n..\n" \
                               "....p...\n" \
                               ".bB.....\n" \
                               "..NPPN..\n" \
                               "PPPBQPPP\n" \
                               "R......R\n"

    assert board.winner == BLACK

    board = create_game_from_nfen(db, 1000, key, exp=5000, nfen="r6r/pbppqppp/1pn2n2/4p3/1bB5/2NPPN2/PPPBQPPP/R3K2R KQkq 8")
    assert board.ascii == "r......r\n" \
                               "pbppqppp\n" \
                               ".pn..n..\n" \
                               "....p...\n" \
                               ".bB.....\n" \
                               "..NPPN..\n" \
                               "PPPBQPPP\n" \
                               "R...K..R\n"

    assert board.winner == WHITE

def test_game_winner_capture(db, key):
    print("===========================")
    board = create_game_from_nfen(db, 0, key, exp=5000)
    assert move(db, key, 'e2', 'e4') is not None
    assert move(db, key, 'f7', 'f6') is not None
    assert move(db, key, 'e8', 'f7') is not None
    assert move(db, key, 'f1', 'c4') is not None
    assert move(db, key, 'c4', 'f7') is not None

    assert board.ascii == "rnbq.bnr\n" \
                               "pppppBpp\n" \
                               ".....p..\n" \
                               "........\n" \
                               "....P...\n" \
                               "........\n" \
                               "PPPP.PPP\n" \
                               "RNBQK.NR\n"
    assert board.kings[WHITE] is not None
    assert board.kings[BLACK] == None
    print(board.kings)
    assert board.winner == WHITE
