"""
game.py

Holds the basic KungFuChess game, which is the deterministic authority about the state of the game.
Basic implementation idea is the same as 0x88 implementation
"""

from datetime import datetime
from collections import defaultdict

STARTING_NFEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR KQkq 1"

# pieces
EMPTY = '.'
KING = 'k'
QUEEN = 'q'
ROOK = 'r'
KNIGHT = 'n'
BISHOP = 'b'
PAWN = 'p'

PIECES = [KING, QUEEN, ROOK, KNIGHT, BISHOP, PAWN]

# colors
BLACK = 'b'
WHITE = 'w'


class Piece():
    """ basic  representation of piece"""
    def __init__(self, type, color, last_move):
        self.type = type
        self.color = color
        self.last_move = last_move

    def __str__(self):
        return self.san

    @property
    def san(self):
        """ Return the piece letter in san notation """
        if self.color == BLACK:
            return self.type.upper()
        return self.type.lower()


class Square():
    """ basic representation of square, supporting different notation formats. """

    UP = 8
    DOWN = -8
    LEFT = -1
    RIGHT = 1

    @classmethod
    def FromFileRank(cls, file, rank):
        """ Create square from given file and rank. """
        if (file < 1 or file > 8 or rank < 1 or rank > 8):
            raise ValueError("Square file and rank must be between 1 and 8")
        return cls(((file - 1) << 4) + (rank - 1))

    @classmethod
    def FromSan(cls, san):
        if (len(san) != 2):
            raise ValueError("san string must contain two characters!")
        san = san.lower()  # allow uppercase notation
        return cls.FromFileRank(ord(san[0])-ord('a') + 1, int(san[1]))

    def __init__(self, index):
        self._index = index

    def __eq__(self, other):
        return self._index == other._index

    def offset(self, off):
        """ Return square at offset from this square or none if invalid square.

         For convenience, it is recommended to use the constants Square.UP/DOWN/LEFT/RIGHT
         when calculating the offsets. """
        new_index = self._index + off
        if new_index & 0x88:
            return None
        else:
            return Square(new_index)

    @property
    def idx(self):
        """ Set index as property to make pseudo-immutable """
        return self._index

    @property
    def rank(self):
        """ Return rank number where rank 1 is the bottom rank (white first) """
        return (self._index & 0x7) + 1 # first 3 bits are rank

    @property
    def file(self):
        """ Return file as number where file 1 is the leftmost rank (a) """
        return ((self._index >> 4) & 0x7) + 1  # bits 4-7 are file

    @property
    def san(self):
        """ Return square in SAN notation """
        return "{}{}".format(chr(ord('a') + self.file), self.rank)


class Move():
    CAPTURE = "capture"
    PROMOTE = "promote"
    KCASTLE = "kcastle"
    QCASTLE = "qcastle"

    def __init__(self, from_sq, to_sq, promote=QUEEN, metadata=None):
        self._from = from_sq
        self._to = to_sq
        self._promote = promote
        # contain additional information that might be relevant but is
        # not a part of the move itself. See examples in properties
        self._metadata = defaultdict(lambda: None)
        self._metadata.update(metadata)

    @property
    def captured(self):
        return self._metadata[Move.CAPTURE]

    @property
    def promote(self):
        return self._metadata[Move.PROMOTE]

    @property
    def is_kingside_castle(self):
        return self._metadata[Move.KCASTLE]

    @property
    def is_queenside_castle(self):
        return self._metadata[Move.QCASTLE]


class KungFuBoard():
    """ A Kung Fu Board is the same board as a chess board, but move
    numbers are tracked for half-moves instead of full moves, and
    timestamps of the game start and last move of each piece are also
    recorded """

    def __init__(self):
        """ Initialize an empty board. """

        self._pieces         = []
        self._empty          = Piece(EMPTY, EMPTY, None) # single reference to save memory
        self._last_move_time = None

        for i in range(0xff):
            self._pieces.append(self._empty)

    def put_piece(self, type, color, to_sq):
        """ Create a new piece of given type and color and put in to to_sq, deleting the piece in to_sq

        The last_move of the piece will be set to None. Can be used with type=EMPTY to remove pieces.
        Return the new Piece."""

        if type == EMPTY:
            self._pieces[to_sq.idx] = self._empty
            return

        piece = Piece(type, color, None)
        self._pieces[to_sq.idx]   = piece
        return piece

    def get_piece(self, from_sq):
        """ Return the piece at given square."""

        return self._pieces[from_sq.idx]


    def move_piece(self, from_sq, to_sq, new_time, color):
        """ Attempt to move piece of given color to the given squares, updating piece_move_time to new_time.

        This will delete any piece at to_sq.

        Return the recorded move timestamp or none if the move wasn't made. """

        piece = self._pieces[from_sq.idx]
        if piece.type == EMPTY or piece.color != color:
            return None

        piece.last_move           = now()
        self._pieces[to_sq.idx]   = piece
        self._pieces[from_sq.idx] = self._empty
        self._last_move_time      = piece.last_move

        return piece.last_move

    @property
    def last_time(self):
        """ last recorded move time. """
        return self._last_move_time

    @property
    def ascii(self):
        res = ""
        for i in range(0x7f):
            if (i & 0x88):
                if not ((i & 0xf) ^ 0x8):
                    res+='\n'
                continue
            else:
                res += self._pieces[i].san
        return res


class KungFuChess():
    # Offsets specific to KungFuChess for each piece (same as standard chess)
    OFFSETS = {
        KING    : [up(left(0)), up(0), up(right(0)), left(0), right(0), down(left(0)), down(0), down(right(0))],
        QUEEN   : [up(left(0)), up(0), up(right(0)), left(0), right(0), down(left(0)), down(0), down(right(0))],
        ROOK    : [up(0), left(0), right(0), down(0)],
        KNIGHT  : [up(up(left(0))), up(up(right(0))), right(right(up(0))), left(left(up(0))), right(right(down(0))),
                   left(left(down(0))), down(down(left(0))), down(down(right(0)))],
        BISHOP  : [up(left(0)), up(right(0)), down(left(0)), down(right(0))],
        PAWN    : {WHITE: up(0), BLACK: down(0)} # pawns handled separately
    }

    # Sliding ability specific to KungFuChess for each piece (same as standard chess)
    SLIDE = {
        KING   : False,
        QUEEN  : True,
        ROOK   : True,
        KNIGHT : False,
        BISHOP : True,
        PAWN   : False  # pawns handled separately
    }

    PAWN_START_RANK = {
        WHITE: 2,
        BLACK: 7
    }

    PAWN_PROMOTE_RANK = {
        WHITE: 8,
        BLACK: 1
    }

    @classmethod
    def FromNfen(cls, move_cd, nfen=None):
        """ Initialize a new board from given nFEN.

        nFEN, or not FEN, is based on the official FEN but without the 2nd, 4th and 5th parts,
        and where the move number is in half moves.
        For FEN notation see https://en.wikipedia.org/wiki/Forsyth%E2%80%93Edwards_Notation.
        nFEN is not complete, not containing the last move timestamp of each piece and current time
        """
        if not nfen:
            nfen = STARTING_NFEN

        board = KungFuBoard()

        rows, castles, move_num = nfen.split(" ")

        for (rank, row) in enumerate(rows.split("/")):
            file = 0
            for l in row:
                sq = Square.FromFileRank(rank + 1, file + 1)
                try:
                    spaces = int(l)
                    for _ in range(spaces):
                        sq = Square.FromFileRank(rank + 1, file + 1)
                        board.put_piece(EMPTY, EMPTY, sq)
                        file += 1
                except ValueError:  # not an integer, then
                    if l.isupper():
                        color = BLACK
                    else:
                        color = WHITE
                    board.put_piece(l, color, sq)
                    file += 1

        return KungFuChess(board, move_cd)


    def __init__(self, board, move_cd, time_since=0):
        """ Initialize a new game on given board requiring move_cd between moves of the same piece.
        by default, the last_move time of the board is used as reference time (meaning the last piece
         to move is always locked on start), but if time_since is supplied it will be used instead. """

        self._board = board
        self._start_time = now() - time_since
        self._castles = {  # TODO figure out castling
            WHITE: [],
            BLACK: []
        }

    def moves(self, san_sq):
        """ Return a list of all possible moves from san_sq """
        try:
            sq = Square.FromSan(san_sq)
        except ValueError:
            return []  # illegal square, no moves

        piece = self._board.get_piece(sq)
        moves = []

        # The ugly part...

        if piece.type == PAWN:
            o_sq = sq.offset(self.OFFSETS[PAWN][piece.color])  # one move forward
            if o_sq and self._board.get_piece(o_sq).type == EMPTY:
                moves.extend(self.create_pawn_moves(sq, o_sq, piece.color))
                if (sq.rank == self.PAWN_START_RANK[piece.color]):  # if on starting rank
                    oo_sq = o_sq.offset(self.OFFSETS[PAWN][piece.color])  # two moves forward
                    if oo_sq and self._board.get_piece(oo_sq).type == EMPTY:
                        moves.extend(self.create_pawn_moves(sq, oo_sq, piece.color))
            lo_sq = o_sq.offset(o_sq.LEFT)  # capture forward left
            if lo_sq and self._board.get_piece(lo_sq).color == other(piece.color):
                self.create_pawn_moves(sq, lo_sq, piece.color,
                                       extra_flags={Move.CAPTURE: self._board.get_piece(lo_sq).type})

            ro_sq = o_sq.offset(o_sq.RIGHT)  # capture forward right
            if ro_sq and self._board.get_piece(ro_sq).color == other(piece.color):
                self.create_pawn_moves(sq, ro_sq, piece.color)
        else:   # normal piece, excluding castle
            for offset in self.OFFSETS[piece.type]:
                o_sq = sq.offset(offset)

                while o_sq:
                    o_piece = self._board.get_piece(o_sq)
                    if o_piece.type == EMPTY:
                        moves.append(Move(sq, o_sq))
                    elif o_piece.color == other(piece.color):
                        moves.append(Move(sq, o_sq,
                                          metadata={Move.CAPTURE: o_piece.type}))
                    if not self.OFFSETS[piece.type]:
                        break
                    o_sq = o_sq.offset(offset)

        # castle
        if piece.type == KING:
            if KING in self._castles[piece.color]:
                moves.append(Move(sq, sq.offset(sq.RIGHT).offset(sq.RIGHT),
                                  metadata={Move.KCASTLE : True}))
            if QUEEN in self._castles[piece.color]:
                moves.append(Move(sq, sq.offset(sq.LEFT).offset(sq.LEFT),
                                  metadata={Move.QCASTLE: True}))

        return moves

    def move(self, san_from_sq, san_to_sq, promote=QUEEN):
        """ Make a move from san_from_sq to san_to_sq, Return the move if it was made, or None otherwise. """
        from_sq = Square.FromSan(san_from_sq)
        to_sq = Square.FromSan(san_to_sq)

        if not from_sq or not to_sq:
            return None

        for move in self.moves(san_from_sq):
            if move.to == to_sq and move.promote and move.promote == promote:
                #TODO: Make move actually happen


    def create_pawn_moves(self, from_sq, to_sq, color, extra_flags=None):
        """ create pawn moves between squares, assuming the move is legal, and returns a list.
        """
        moves = []

        if not extra_flags:
            extra_flags = {}

        if to_sq == self.PAWN_PROMOTE_RANK[color]:
            extra_flags.update(Move.PROMOTE)
            for piece in [QUEEN, ROOK, BISHOP, KNIGHT]:
                moves.append(Move(from_sq, to_sq, promote=piece, metadata=extra_flags))
        else:
            moves.append(Move(from_sq, to_sq, metadata=extra_flags))

        return moves


########################################################################################################
# Utility functions                                                                                    #
########################################################################################################

def now():
    """ Return current time in miliseconds since epoch """
    return int(datetime.now().timestamp() * 1000)

if __name__ == "__main__":
    print("Creating game")
    game = KungFuChess.FromNfen(4000)
    print(game._board.ascii)

def up(n):
    return n + Square.UP

def down(n):
    return n + Square.DOWN

def left(n):
    return n + Square.LEFT

def right(n):
    return n + Square.RIGHT

def other(color):
    if (color == WHITE):
        return BLACK
    return WHITE