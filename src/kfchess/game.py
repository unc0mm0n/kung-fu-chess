"""
game.py

Holds the basic KungFuChess game, which is the deterministic authority about the state of the game.
Basic implementation idea is the same as 0x88 implementation
"""

from datetime import datetime
from collections import defaultdict
import pprint

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

COLORS = [BLACK, WHITE]


class Piece():
    """ basic  representation of piece"""
    def __init__(self, type, color, last_move):
        if (type not in PIECES or color not in COLORS) and type != EMPTY:
            raise ValueError("Invalid piece type ({}) or color ({})".format(type, color))
        self.type = type
        self.color = color
        self.last_move = last_move

    def __str__(self):
        return self.san

    @property
    def san(self):
        """ Return the piece letter in san notation """
        if self.color == WHITE:
            return self.type.upper()
        return self.type.lower()


class Square():
    """ basic representation of square, supporting different notation formats. """

    UP = 16
    DOWN = -16
    LEFT = -1
    RIGHT = 1

    @classmethod
    def FromFileRank(cls, file, rank):
        """ Create square from given file and rank. """
        if (file < 1 or file > 8 or rank < 1 or rank > 8):
            raise ValueError("Square file and rank must be between 1 and 8")
        return cls(((rank - 1) << 4) + (file - 1))

    @classmethod
    def O(cls):
        """ Create a zero square """
        return cls(0)

    @classmethod
    def FromSan(cls, san):
        if (len(san) != 2):
            raise ValueError("san string must contain two characters!")
        san = san.lower()  # allow uppercase notation
        return cls.FromFileRank(ord(san[0])-ord('a') + 1, int(san[1]))

    def __init__(self, index):
        self._index = index

    def __eq__(self, other):
        try:
            return self._index == other._index
        except AttributeError:  #not comparing to square. Maybe to int?
            return self._index == other

    def __repr__(self):
        return "Square({})".format(self._index)

    def __add__(self, o):
        try:
            return Square(self._index + o._index)
        except AttributeError:  # maybe adding int to square
            return Square(self._index + o)

    def offset(self, o):
        """ Return a square at given offset from current square.

        As offset do not directly correspond to coordinates (file and rank) it is recommended to use the
        up/down/left/right properties or the Square.UP/DOWN/LEFT/RIGHT constants to calculate the correct
        offset. """
        return self + o

    @property
    def up(self):
        return self.offset(Square.UP)

    @property
    def down(self):
        return self.offset(Square.DOWN)

    @property
    def left(self):
        return self.offset(Square.LEFT)

    @property
    def right(self):
        return self.offset(Square.RIGHT)

    @property
    def idx(self):
        """ Set index as property to make pseudo-immutable """
        return self._index

    @property
    def rank(self):
        """ Return rank number where rank 1 is the bottom rank (white first) """
        return ((self._index >> 4)  & 0x7) + 1 # bits 4-7 are rank

    @property
    def file(self):
        """ Return file as number where file 1 is the leftmost rank (a) """
        return (self._index & 0x7) + 1  # first 3 bits are file

    @property
    def san(self):
        """ Return square in SAN notation """
        if not self.valid:
            return ""
        return "{}{}".format(chr(ord('a') + self.file - 1), self.rank)

    @property
    def valid(self):
        """ Return True if square is valid square on board """
        return self._index >= 0 and self._index <= 0xff and not self._index & 0x88


class Move():
    CAPTURE = "capture"
    PROMOTE = "promote"
    KCASTLE = "kcastle"
    QCASTLE = "qcastle"
    TIME    = "time"

    def __init__(self, from_sq, to_sq, metadata=None):
        self.from_sq = from_sq
        self.to_sq = to_sq
        # contain additional information that might be relevant but is
        # not a part of the move itself. See examples in properties
        self._metadata = defaultdict(lambda: None)
        if metadata:
            self._metadata.update(metadata)

    def __str__(self):
        return "Move(from {}, to {}, metadata:{}".format(self.from_sq.san, self.to_sq.san, pprint.pformat(dict(self._metadata)))

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

    @property
    def time(self):
        return self._metadata[Move.TIME]


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
        self.move_number     = 0

        for i in range(0xff):
            self._pieces.append(self._empty)

    def __getitem__(self, sq):
        try:
            return self._pieces[sq.idx]
        except AttributeError:  # try int
            return self._pieces[sq]

    def put_piece(self, type, color, to_sq, time=None):
        """ Create a new piece of given type and color and put in to to_sq, deleting the piece in to_sq

        The last_move of the piece will be set to time. Can be used with type=EMPTY to remove pieces.
        Return the new Piece."""
        if type == EMPTY:
            self._pieces[to_sq.idx] = self._empty
            return

        piece = Piece(type, color, time)
        self._pieces[to_sq.idx]   = piece
        return piece

    def get_piece(self, from_sq):
        """ Return the piece at given square."""

        return self._pieces[from_sq.idx]


    def move_piece(self, from_sq, to_sq, new_time):
        """ Attempt to move piece of given color to the given squares, updating piece_move_time to new_time.

        This will delete any piece at to_sq.

        Return the recorded move timestamp or none if the move wasn't made. """

        piece = self._pieces[from_sq.idx]
        if piece.type == EMPTY:
            return None

        piece.last_move           = new_time
        self._pieces[to_sq.idx]   = piece
        self._pieces[from_sq.idx] = self._empty
        self._last_move_time      = piece.last_move
        self.move_number          += 1

        return piece

    @property
    def fen(self):
        """ Return the board part of fen (or nfen) notation"""
        res = ""
        for r in range(8):
            rank = 8 - r
            e_cnt = 0
            for f in range(8):
                file = f + 1
                piece = self.get_piece(Square.FromFileRank(file, rank))
                if (piece.type == EMPTY):
                    e_cnt += 1
                else:
                    if (e_cnt != 0):
                        res += str(e_cnt)
                        e_cnt = 0
                    res += str(piece)

            if (e_cnt != 0):
                res += str(e_cnt)
            if (rank > 1):
                res += "/"
        return res

    @property
    def last_time(self):
        """ last recorded move time. """
        return self._last_move_time

    @property
    def ascii(self):
        res = ""
        for r in range(8):
            rank = 8-r
            for f in range(8):
                file = f + 1
                res += str(self.get_piece(Square.FromFileRank(file, rank)))
            res += "\n"
        return res


class KungFuChess():
    # Offsets specific to KungFuChess for each piece (same as standard chess)
    OFFSETS = {
        KING    : [Square.O().up.left, Square.O().up, Square.O().up.right, Square.O().left,
                   Square.O().right, Square.O().down.left, Square.O().down, Square.O().down.right],
        QUEEN   : [Square.O().up.left, Square.O().up, Square.O().up.right, Square.O().left,
                   Square.O().right, Square.O().down.left, Square.O().down, Square.O().down.right],
        ROOK    : [Square.O().up, Square.O().down, Square.O().left, Square.O().right],
        KNIGHT  : [Square.O().up.up.left, Square.O().up.up.right, Square.O().up.right.right, Square.O().up.left.left,
                   Square.O().down.right.right, Square.O().down.left.left, Square.O().down.down.right, Square.O().down.down.left],
        BISHOP  : [Square.O().up.left, Square.O().down.left, Square.O().up.right, Square.O().down.right],
        PAWN    : {WHITE: Square.O().up, BLACK: Square.O().down} # pawns handled separately
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

    CASTLE_DISABLING_SQUARES = { # Moves from or to these squares will disable the respective castle
        WHITE: {
            KING: [Square.FromSan('e1'), Square.FromSan('h1')],
            QUEEN: [Square.FromSan('e1'), Square.FromSan('a1')]
        },
        BLACK: {
            KING: [Square.FromSan('e8'), Square.FromSan('h8')],
            QUEEN: [Square.FromSan('e8'), Square.FromSan('a8')]
        }
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
                sq = Square.FromFileRank(file + 1, 8 - rank )  # FEN ranks go from top to bottom
                try:
                    spaces = int(l)
                    for _ in range(spaces):
                        sq = Square.FromFileRank(file + 1, 8 - rank)
                        board.put_piece(EMPTY, EMPTY, sq)
                        file += 1
                except ValueError:  # not an integer, then
                    if l.isupper():
                        color = WHITE
                    else:
                        color = BLACK
                    board.put_piece(l.lower(), color, sq)
                    file += 1

        board.move_number = int(move_num)

        kfc = KungFuChess(board, move_cd)
        if "K" not in castles:
            kfc._castles[WHITE][KING] = False
        if "Q" not in castles:
            kfc._castles[WHITE][QUEEN] = False
        if "k" not in castles:
            kfc._castles[BLACK][KING] = False
        if "q" not in castles:
            kfc._castles[BLACK][QUEEN] = False

        return kfc


    def __init__(self, board, move_cd, time_since=0):
        """ Initialize a new game on given board requiring move_cd between moves of the same piece.
        by default, the last_move time of the board is used as reference time (meaning the last piece
         to move is always locked on start), but if time_since is supplied it will be added to that time. """

        self._board = board

        kings = list([(sq, piece) for sq, piece in enumerate(self._board) if piece.type == KING])
        if len(kings) != 2 and len(kings) != 1:
            raise ValueError("Invalid board given, should have 1 or 2 kings")

        self._kings = {
            BLACK: Square.O(),
            WHITE: Square.O()
        }
        for sq, king in kings:
            if (self._kings[king.color] != Square.O()):
                raise ValueError("Invalid board given, two kings of same color")
            self._kings[king.color] = Square(sq)


        timed_moves = list([piece.last_move for piece in self._board if piece.last_move is not None])
        if not timed_moves:
            board_latest = 0
        else:
            board_latest = max(timed_moves)
        self._start_time = now() - board_latest + time_since

        self._cd = move_cd
        self._castles = {  # TODO figure out castling
            WHITE: {KING: True, QUEEN: True},
            BLACK: {KING: True, QUEEN: True}
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
        if piece.type == EMPTY:
            return []
        if piece.type == PAWN:
            o_sq = sq + self.OFFSETS[PAWN][piece.color]  # one move forward
            if o_sq and self._board.get_piece(o_sq).type == EMPTY:
                moves.extend(self.create_pawn_moves(sq, o_sq, piece.color))
                if (sq.rank == self.PAWN_START_RANK[piece.color]):  # if on starting rank
                    oo_sq = o_sq + self.OFFSETS[PAWN][piece.color]  # two moves forward
                    if oo_sq and self._board.get_piece(oo_sq).type == EMPTY:
                        moves.extend(self.create_pawn_moves(sq, oo_sq, piece.color))
            lo_sq = o_sq.left  # capture forward left
            if lo_sq.valid and self._board.get_piece(lo_sq).color == other(piece.color):
                moves.extend(self.create_pawn_moves(sq, lo_sq, piece.color,
                                                    extra_flags={Move.CAPTURE: self._board.get_piece(lo_sq).type}))

            ro_sq = o_sq.right  # capture forward right
            if ro_sq.valid and self._board.get_piece(ro_sq).color == other(piece.color):
                moves.extend(self.create_pawn_moves(sq, ro_sq, piece.color,
                                                    extra_flags={Move.CAPTURE: self._board.get_piece(lo_sq).type}))
        else:   # normal piece, excluding castle
            for offset in self.OFFSETS[piece.type]:
                o_sq = sq + offset
                while o_sq.valid:
                    o_piece = self._board.get_piece(o_sq)
                    if o_piece.type == EMPTY:
                        moves.append(Move(sq, o_sq))
                    else:
                        if o_piece.color == other(piece.color):
                            moves.append(Move(sq, o_sq,
                                              metadata={Move.CAPTURE: o_piece.type}))
                        break
                    if not self.SLIDE[piece.type]:
                        break
                    o_sq = o_sq + offset

        # castle
        if piece.type == KING:
            if self._castles[piece.color][KING]:
                moves.append(Move(sq, sq.right.right,
                                  metadata={Move.KCASTLE: True}))
            if self._castles[piece.color][QUEEN]:
                moves.append(Move(sq, sq.left.left,
                                  metadata={Move.QCASTLE: True}))

        return moves

    def move(self, san_from_sq, san_to_sq, promote=None):
        """ Make a move from san_from_sq to san_to_sq, Return the move if it was made, or None otherwise. """
        from_sq = Square.FromSan(san_from_sq)
        to_sq = Square.FromSan(san_to_sq)

        if not from_sq.valid or not to_sq.valid:
            return None

        piece = self._board[from_sq]
        o_piece = self._board[to_sq]

        for move in self.moves(san_from_sq):
            if move.to_sq == to_sq and move.promote == promote:
                move_time = now()
                relative_move_time = move_time - self._start_time  # internally we hold relative times
                if piece.last_move is not None and self._cd > (relative_move_time - piece.last_move):  # move too early
                    return None
                # TODO: Update history here

                # Do move
                self._board.move_piece(from_sq, to_sq, relative_move_time)
                # Do special moves
                if move.is_kingside_castle:
                    castle_from = to_sq.right
                    castle_to   = to_sq.left
                    self._board.move_piece(castle_from, castle_to, relative_move_time)

                if move.is_queenside_castle:
                    castle_from = to_sq.left.left
                    castle_to = to_sq.right
                    self._board.move_piece(castle_from, castle_to, relative_move_time)

                if move.promote:
                    self._board.put_piece(move.promote, piece.color, to_sq, relative_move_time)

                # Update castles
                for color in COLORS:
                    king_sqs  = self.CASTLE_DISABLING_SQUARES[color][KING]
                    queen_sqs = self.CASTLE_DISABLING_SQUARES[color][QUEEN]
                    if from_sq in king_sqs or to_sq in king_sqs:
                        self._castles[color][KING] = False
                    if from_sq in queen_sqs or to_sq in queen_sqs:
                        self._castles[color][QUEEN] = False

                # Update king capture
                if o_piece.type == KING:
                    self._kings[o_piece.color] = Square.O()

                move._metadata[Move.TIME] = relative_move_time

                return move

    def to_dict(self):
        """ Return a dictionary representing the game """
        res = {
            "cd": self._cd,
            "history": None, #TODO,
            "current_time": now(),
            "start_time":   self._start_time,
            "nfen": "{} {} {}".format(self._board.fen, self.castles_nfen, self._board.move_number),
            "times": {}
        }

        for r in range(8):
            rank = r + 1
            for f in range(8):
                file = f + 1
                sq = Square.FromFileRank(file, rank)
                piece = self._board.get_piece(sq)
                if (piece.last_move):  # only pass non-None times
                    res["times"][sq.san] = piece.last_move

        return res

    def create_pawn_moves(self, from_sq, to_sq, color, extra_flags=None):
        """ create pawn moves between squares, assuming the move is legal, and returns a list.
        """
        moves = []

        if not extra_flags:
            extra_flags = {}

        if to_sq.rank == self.PAWN_PROMOTE_RANK[color]:
            for piece in [QUEEN, ROOK, BISHOP, KNIGHT]:
                extra_flags.update({Move.PROMOTE: piece})
                move = Move(from_sq, to_sq, metadata=extra_flags)
                moves.append(move)
        else:
            moves.append(Move(from_sq, to_sq, metadata=extra_flags))

        return moves

    @property
    def castles_nfen(self):
        res = "{K}{Q}{k}{q}".format(
            K="K" if self._castles[WHITE][KING] else "",
            Q="Q" if self._castles[WHITE][QUEEN] else "",
            k="k" if self._castles[BLACK][KING] else "",
            q="q" if self._castles[BLACK][QUEEN] else ""
        )
        if not res:
            res = '-'
        return res

    @property
    def winner(self):
        """ Return color of winner if game is over, or EMPTY if there is no winner yet. """
        if self._kings[WHITE] == Square.O():
            return BLACK
        if self._kings[BLACK] == Square.O():
            return WHITE
        return EMPTY

    @property
    def is_over(self):
        return self.winner != EMPTY


########################################################################################################
# Utility functions                                                                                    #
########################################################################################################

def now():
    """ Return current time in miliseconds since epoch """
    return int(datetime.now().timestamp() * 1000)

def other(color):
    if (color == WHITE):
        return BLACK
    return WHITE

########################################################################################################
# Random Main                                                                                          #
########################################################################################################

if __name__ == "__main__":
    print("Creating game")
    game = KungFuChess.FromNfen(4000)
    print(game._board.ascii)
