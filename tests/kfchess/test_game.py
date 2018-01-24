from itertools import product
import time

import pytest

from kfchess.game import *

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

def test_FromNfen():
    kfc = KungFuChess.FromNfen(0)
    assert kfc._board.ascii == "rnbqkbnr\npppppppp\n........\n........\n........\n........\nPPPPPPPP\nRNBQKBNR\n"

    kfc = KungFuChess.FromNfen(0, "3b4/NP6/rp2k1B1/2R3P1/3K4/2B2Q2/P1P3P1/4r3 - 1")
    assert kfc._board.ascii == "...b....\nNP......\nrp..k.B.\n..R...P.\n...K....\n..B..Q..\nP.P...P.\n....r...\n"

    with pytest.raises(ValueError):
        kfc = KungFuChess.FromNfen(1000, "r6r/pbppqppp/1pn2n2/4p3/1bB5/2NPPN2/PPPBQPPP/R6R KQkq 8")

    with pytest.raises(ValueError):
        kfc = KungFuChess.FromNfen(1000, "r3K2r/pbppqppp/1pn2n2/4p3/1bB5/2NPPN2/PPPBQPPP/R3K2R KQkq 8")

    with pytest.raises(ValueError):
        kfc = KungFuChess.FromNfen(1000, "r3k2r/pbppqppp/1pn1Kn2/4p3/1bB5/2NPPN2/PPPBQPPP/R3K2R KQkq 8")

def test_board_get_piece():
    board = KungFuChess.FromNfen(0)._board
    sq = Square.FromSan('e2')
    assert board.get_piece(sq).type == PAWN

def test_create_pawn_moves_regular():
    kfc = KungFuChess.FromNfen(0)
    from_sq = Square.FromSan('e2')
    to_sq = Square.FromSan('e3')
    res = [m.to_sq.san for m in kfc.create_pawn_moves(from_sq, to_sq, WHITE)]
    ex  = ['e3']
    for move in res:
        assert move in ex
    for move in ex:
        assert move in res

    from_sq = Square.FromSan('e2')
    to_sq = Square.FromSan('e4')
    res = [m.to_sq.san for m in kfc.create_pawn_moves(from_sq, to_sq, WHITE)]
    ex = ['e4']
    for move in res:
        assert move in ex
    for move in ex:
        assert move in res

    from_sq = Square.FromSan('e7')
    to_sq = Square.FromSan('e6')
    res = [m.to_sq.san for m in kfc.create_pawn_moves(from_sq, to_sq, BLACK)]
    ex = ['e6']
    for move in res:
        assert move in ex
    for move in ex:
        assert move in res

    from_sq = Square.FromSan('e7')
    to_sq = Square.FromSan('e5')
    res = [m.to_sq.san for m in kfc.create_pawn_moves(from_sq, to_sq, BLACK)]
    ex = ['e5']
    for move in res:
        assert move in ex
    for move in ex:
        assert move in res

def test_create_pawn_moves_promote():
    kfc = KungFuChess.FromNfen(0)

    from_sq = Square.FromSan('e7')
    to_sq = Square.FromSan('e8')
    res = [m.promote for m in kfc.create_pawn_moves(from_sq, to_sq, WHITE)]
    print(res)
    ex = [QUEEN, BISHOP, KNIGHT, ROOK]
    for move in res:
        assert move in ex
    for move in ex:
        assert move in res

    from_sq = Square.FromSan('e2')
    to_sq = Square.FromSan('f1')
    res = [m.promote for m in kfc.create_pawn_moves(from_sq, to_sq, BLACK)]
    print(res)
    ex = [QUEEN, BISHOP, KNIGHT, ROOK]
    for move in res:
        assert move in ex
    for move in ex:
        assert move in res

def test_moves_basic():
    kfc = KungFuChess.FromNfen(0)

    res = [m.to_sq.san for m in kfc.moves('e2')]
    ex  = ['e3', 'e4']
    for move in res:
        assert move in ex
    for move in ex:
        assert move in res

    res = [m.to_sq.san for m in kfc.moves('g1')]
    ex = ['f3', 'h3']
    for move in res:
        assert move in ex
    for move in ex:
        assert move in res

    res = [m.to_sq.san for m in kfc.moves('b8')]
    ex = ['a6', 'c6']
    for move in res:
        assert move in ex
    for move in ex:
        assert move in res

    res = [m.to_sq.san for m in kfc.moves('h8')]
    ex = []
    for move in res:
        assert move in ex
    for move in ex:
        assert move in res

def test_moves_advanced():
    kfc = KungFuChess.FromNfen(0, "3b4/NP6/rp2k1B1/2R3P1/3K4/2B2Q2/P1P3P1/4r3 - 1")
    print(kfc._board.ascii)

    res = [m.to_sq.san for m in kfc.moves('e6')]  # no castles
    ex = ['d7', 'd6', 'd5', 'e7', 'e5', 'f7', 'f6', 'f5']
    assert(len(res) == len(ex))
    for move in res:
        assert move in ex
    for move in ex:
        assert move in res

    res = [m.to_sq.san for m in kfc.moves('b7')]
    ex = ['b8']
    assert(len(res) == 4)  # promotions
    for move in res:
        assert move in ex
    for move in ex:
        assert move in res

    moves = kfc.moves('a6')
    res = [m.to_sq.san for m in moves]
    ex = ['a7', 'a5', 'a4', 'a3', 'a2']
    assert(len(res) == len(ex))  # captures only enemy pieces
    for move in res:
        assert move in ex
    for move in ex:
        assert move in res

    assert len(list(filter(lambda x: x.captured, [m for m in moves]))) == 2  # only two capture moves

    kfc = KungFuChess.FromNfen(0, "r3k2r/pbppqppp/1pn2n2/4p3/1bB5/2NPPN2/PPPBQPPP/R3K2R KQkq 8")
    print(kfc._board.ascii)
    res = [m.to_sq.san for m in kfc.moves('e1')]  # yes castles
    ex = ['d1', 'f1', 'c1', 'g1']
    assert (len(res) == len(ex))
    for move in res:
        assert move in ex
    for move in ex:
        assert move in res

    res = [m.to_sq.san for m in kfc.moves('e8')]  # yes castles
    ex = ['d8', 'f8', 'c8', 'g8']
    assert (len(res) == len(ex))
    for move in res:
        assert move in ex
    for move in ex:
        assert move in res

def test_move_simple():
    kfc = KungFuChess.FromNfen(0)
    kfc.move('e2', 'e4')
    assert kfc._board.ascii == "rnbqkbnr\n" \
                               "pppppppp\n" \
                               "........\n" \
                               "........\n" \
                               "....P...\n" \
                               "........\n" \
                               "PPPP.PPP\n" \
                               "RNBQKBNR\n"

    kfc.move('f1', 'c4')
    assert kfc._board.ascii == "rnbqkbnr\n" \
                               "pppppppp\n" \
                               "........\n" \
                               "........\n" \
                               "..B.P...\n" \
                               "........\n" \
                               "PPPP.PPP\n" \
                               "RNBQK.NR\n"

    kfc.move('g1', 'f3')
    assert kfc._board.ascii == "rnbqkbnr\n" \
                               "pppppppp\n" \
                               "........\n" \
                               "........\n" \
                               "..B.P...\n" \
                               ".....N..\n" \
                               "PPPP.PPP\n" \
                               "RNBQK..R\n"

    kfc.move('e1', 'g1')       # castle
    assert kfc._board.ascii == "rnbqkbnr\n" \
                               "pppppppp\n" \
                               "........\n" \
                               "........\n" \
                               "..B.P...\n" \
                               ".....N..\n" \
                               "PPPP.PPP\n" \
                               "RNBQ.RK.\n"

    kfc.move('g8', 'h6')
    kfc.move('e7', 'e6')
    kfc.move('f8', 'e7')
    assert kfc._board.ascii == "rnbqk..r\n" \
                               "ppppbppp\n" \
                               "....p..n\n" \
                               "........\n" \
                               "..B.P...\n" \
                               ".....N..\n" \
                               "PPPP.PPP\n" \
                               "RNBQ.RK.\n"

    assert kfc.move('h8', 'f8') is not None
    assert kfc.move('f8', 'h8') is not None
    assert kfc._board.ascii == "rnbqk..r\n" \
                               "ppppbppp\n" \
                               "....p..n\n" \
                               "........\n" \
                               "..B.P...\n" \
                               ".....N..\n" \
                               "PPPP.PPP\n" \
                               "RNBQ.RK.\n"

    assert kfc.move('e8', 'g8') is None  # no castle after rook move

def test_move_time_delay():
    kfc = KungFuChess.FromNfen(1000)  # delay between moves in ms
    kfc.move('e2', 'e4')
    assert kfc._board.ascii == "rnbqkbnr\n" \
                               "pppppppp\n" \
                               "........\n" \
                               "........\n" \
                               "....P...\n" \
                               "........\n" \
                               "PPPP.PPP\n" \
                               "RNBQKBNR\n"

    assert kfc.move('e4', 'e5') is None
    assert kfc._board.ascii == "rnbqkbnr\n" \
                               "pppppppp\n" \
                               "........\n" \
                               "........\n" \
                               "....P...\n" \
                               "........\n" \
                               "PPPP.PPP\n" \
                               "RNBQKBNR\n"

    time.sleep(1)  # should be fine now (sleep is in secs)

    assert kfc.move('e4', 'e5') is not None
    assert kfc._board.ascii == "rnbqkbnr\n" \
                               "pppppppp\n" \
                               "........\n" \
                               "....P...\n" \
                               "........\n" \
                               "........\n" \
                               "PPPP.PPP\n" \
                               "RNBQKBNR\n"

def test_move_castle_rook_delayed():
    kfc = KungFuChess.FromNfen(1000, "r3k2r/pbppqppp/1pn2n2/4p3/1bB5/2NPPN2/PPPBQPPP/R3K2R KQkq 8")
    assert kfc._board.ascii == "r...k..r\n" \
                               "pbppqppp\n" \
                               ".pn..n..\n" \
                               "....p...\n" \
                               ".bB.....\n" \
                               "..NPPN..\n" \
                               "PPPBQPPP\n" \
                               "R...K..R\n"

    kfc.move('e1', 'g1')
    assert kfc._board.ascii == "r...k..r\n" \
                               "pbppqppp\n" \
                               ".pn..n..\n" \
                               "....p...\n" \
                               ".bB.....\n" \
                               "..NPPN..\n" \
                               "PPPBQPPP\n" \
                               "R....RK.\n"

    assert kfc.move('f1', 'e1') is None

    time.sleep(1)  # should be fine now (sleep is in secs)

    assert kfc.move('f1', 'e1') is not None
    assert kfc._board.ascii == "r...k..r\n" \
                               "pbppqppp\n" \
                               ".pn..n..\n" \
                               "....p...\n" \
                               ".bB.....\n" \
                               "..NPPN..\n" \
                               "PPPBQPPP\n" \
                               "R...R.K.\n"

def test_move_winner():
    kfc = KungFuChess.FromNfen(1000, "r3k2r/pbppqppp/1pn2n2/4p3/1bB5/2NPPN2/PPPBQPPP/R3K2R KQkq 8")
    assert kfc._board.ascii == "r...k..r\n" \
                               "pbppqppp\n" \
                               ".pn..n..\n" \
                               "....p...\n" \
                               ".bB.....\n" \
                               "..NPPN..\n" \
                               "PPPBQPPP\n" \
                               "R...K..R\n"

    assert kfc.winner == EMPTY

    kfc = KungFuChess.FromNfen(1000, "r3k2r/pbppqppp/1pn2n2/4p3/1bB5/2NPPN2/PPPBQPPP/R6R KQkq 8")
    assert kfc._board.ascii == "r...k..r\n" \
                               "pbppqppp\n" \
                               ".pn..n..\n" \
                               "....p...\n" \
                               ".bB.....\n" \
                               "..NPPN..\n" \
                               "PPPBQPPP\n" \
                               "R......R\n"

    assert kfc.winner == BLACK

    kfc = KungFuChess.FromNfen(1000, "r6r/pbppqppp/1pn2n2/4p3/1bB5/2NPPN2/PPPBQPPP/R3K2R KQkq 8")
    assert kfc._board.ascii == "r......r\n" \
                               "pbppqppp\n" \
                               ".pn..n..\n" \
                               "....p...\n" \
                               ".bB.....\n" \
                               "..NPPN..\n" \
                               "PPPBQPPP\n" \
                               "R...K..R\n"

    assert kfc.winner == WHITE