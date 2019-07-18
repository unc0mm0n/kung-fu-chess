"""
game.py

Holds the basic KungFuChess game, which is the deterministic authority about the state of the game.
Basic implementation idea is the same as 0x88 implementation
"""

from datetime import datetime
from collections import defaultdict
import pprint
import json

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
EMPTY = 'e'

COLORS = [BLACK, WHITE]

WAITING = "waiting"
PLAYING = "playing"
W_WINS = "w_wins"
B_WINS = "b_wins"

STATES = [WAITING, PLAYING, W_WINS, B_WINS]

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

    def dict(self):
        return {
                'type': self.type,
                'color': self.color,
                'last_move': self.last_move
                }

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


# Offsets for each piece (same as standard chess)
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

# Sliding ability for each piece (same as standard chess)
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

class KungFuBoard():
    """ A Kung Fu Board is the same board as a chess board, but move
    numbers are tracked for half-moves instead of full moves, and
    timestamps of the game start and last move of each piece are also
    recorded. DEPRECATED."""




class RedisKungFuBoard(KungFuBoard):
    """ A Kung Fu Board implementation storing using Redis instead of an
    internal list. Should check performence differences"""

    def __init__(self, redis_db, store_key, cd=None, exp=None):
        """ Initialize a new RedisKungFuBoard at given redis_db and store.

        the expire of the game (from last set or get) will be set to exp milliseconds if it is not none.
        cd if not specified will be taken from db, """
        self._db        = redis_db
        self._store_key = str(store_key)
        self._exp       = None
        if exp:
            self._set("exp", exp)
            self._exp       = exp
        else:
            self._exp = self._get("exp")
        self._pexpire()

        if cd is not None:
            self._cd = cd
            self._set("cd", cd)
        else:
            self._cd = self._get("cd")

        super().__init__()

    def clear(self):
        """ Create new, empty, board. called by __init__ """
        for i in range(8):
            for j in range(8):
                sq = Square.FromFileRank(i+1, j+1)
                self[sq] = Piece(EMPTY, EMPTY, None)

        self.set_last_move(None)
        self.set_move_number(0)

    def __getitem__(self, sq : Square) -> Piece:
        """ Get piece from square. """
        if self._exp:
            self._db.pexpire(self._store_key, self._exp)
        try:
            san = sq.san
        except AttributeError:
            print(sq)
            try:
                san = Square(sq).san
            except:
                pass


        res = self._db.hget(self._store_key, san)
        if res is None:
            return Piece(EMPTY, EMPTY, 0)
        return Piece(**json.loads(res))

    def _pexpire(self):
        if self._exp:
            self._db.pexpire(self._store_key, self._exp)

    def _get(self, key):
        """ Get a non-square key """
        self._pexpire()
        try:
            return json.loads(self._db.hget(self._store_key, key))
        except TypeError:  #key not found
            return None

    def _set(self, key, value):
        """ put a value in a non-square key"""
        self._pexpire()
        self._db.hset(self._store_key, key, json.dumps(value))

    def __setitem__(self, sq: Square, piece: Piece):
        """ Overwriting this should suffice in changing store method. """
        try:
            t_piece = self[sq]
        except ValueError:
            t_piece = Piece(EMPTY, EMPTY, None)

        # set expire
        self._pexpire()

        # if we removed a king
        if t_piece.type == KING:
            king_key = "kings:{}".format(t_piece.color)
            self._set(king_key, None)

        # remember new piece
        self._db.hset(self._store_key, sq.san, json.dumps(piece.dict()))

        # if we put a king
        if piece.type == KING:
            old = self.kings
            king_key = "kings:{}".format(piece.color)
            king_sq =  self._get(king_key)
            if king_sq:
                raise ValueError("Too many kings of same color")
            self._set(king_key, json.dumps(sq.san))


    def put_piece(self, type, color, to_sq, time=None):
        """ Create a new piece of given type and color and put in to to_sq, deleting the piece in to_sq

        The last_move of the piece will be set to time. Can be used with type=EMPTY to remove pieces.
        Return the new Piece."""
        piece = Piece(type, color, time)
        self[to_sq]   = piece
        return piece

    def get_piece(self, from_sq):
        """ Return the piece at given square."""

        return self[from_sq]


    def move_piece(self, from_sq, to_sq, new_time):
        """ Attempt to move piece of given color to the given squares, updating piece_move_time to new_time.

        This will delete any piece at to_sq.

        Return moved piece or None of from_sq was empty """

        piece = self[from_sq]
        if piece.type == EMPTY:
            return None

        piece.last_move           = new_time
        self[from_sq]             = Piece(EMPTY, EMPTY, None)
        self[to_sq]               = piece
        self.set_last_move(piece.last_move)
        self.inc_move_number()
        return piece

    def set_black(self, name):
        if self.black is not None:
            raise Exception("Reassignment of black player!")
        self._set(BLACK, name)
        if self.white is not None:
            self.set_state(PLAYING)

    def set_white(self, name):
        if self.white is not None:
            raise Exception("Reassignment of white player!")
        self._set(WHITE, name)
        if self.black is not None:
            self.set_state(PLAYING)

    def set_state(self, new_state):
        if new_state not in STATES:
            raise ValueError("Invalid assignment to state {}".format(new_state))
        self._set("state", new_state)

    def set_start_time(self, time):
        self._set("start_time", time)

    def set_castles(self, castles):
        self._set("castles", castles)

    def set_move_number(self, move):
        self._set("move_number", move)

    def inc_move_number(self):
        self._db.hincrby(self._store_key, "move_number", 1)

    def set_last_move(self, time):
        self._set("last_move", time)

    def can_castle(self, color, side):
        letter = 'k' if side == KING else 'q'
        fen_letter = letter.upper() if color == WHITE else letter
        return fen_letter in str(self.castles)

    def disable_castle(self, color, side):
        letter = 'k' if side == KING else 'q'
        fen_letter = letter.upper() if color == WHITE else letter
        current = self.castles
        self.set_castles(str(current).replace(fen_letter, ""))

    def get_all_pieces(self, type=None, color=None, move_before=None, move_after=None):
        """ Get a tuple (sq, piece) of all pieces.

        limited to type/color/move_before/move_after (where move times are relative to game start).
        setting move_after 0 will get all pieces that ever moved. """
        res = []
        for r in range(8):
            rank = 8-r
            for f in range(8):
                file = f + 1
                sq = Square.FromFileRank(file, rank)
                piece = self[sq]
                if (type is None or piece.type == type)\
                    and (color is None or piece.color == color)\
                    and (move_before is None or piece.last_move is None or piece.last_move < move_before)\
                    and (move_after is None or (piece.last_move is not None and piece.last_move > move_after)):
                    res.append((sq, piece))
        return res

    @property
    def winner(self):
        kings = self.kings
        if kings[WHITE] == None:
            return BLACK
        elif kings[BLACK] == None:
            return WHITE
        else:
            return None

    @property
    def start_time(self):
        res = self._get("start_time")
        return res

    @property
    def cd(self):
        return self._cd

    @property
    def kings(self):
        w_key = "kings:{}".format(WHITE)
        b_key = "kings:{}".format(BLACK)
        try:
            w_king = self._get(w_key)
        except TypeError:
            self._set(w_key, None)
            w_king = None
        try:
            b_king = self._get(b_key)
        except TypeError:
            self._set(b_key, None)
            b_king = None
        return {WHITE: w_king, BLACK: b_king}

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
        return self._get("last_move")

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

    @property
    def castles(self):
        return self._get("castles")

    @property
    def move_number(self):
        return self._get("move_number")

    @property
    def white(self):
        return self._get(WHITE)

    @property
    def black(self):
        return self._get(BLACK)

    @property
    def state(self):
        return self._get("state")

    def get_player(self, color):
        if color == WHITE:
            return self.white
        elif color == BLACK:
            return self.black
        else:
            raise ValueError("invalid value for get_player")

@property
def game_winner(db, store_key):
    """ Return color of winner if game is over, or EMPTY if there is no winner yet. """
    board = RedisKungFuBoard(db, store_key)
    if board.kings[WHITE] == Square.O():
        return BLACK
    if self._kings[BLACK] == Square.O():
        return WHITE
    return EMPTY

def get_board(db, store_key):
    return RedisKungFuBoard(db, store_key)

def moves(db, store_key, san_sq):
    """ Return a list of all possible moves from san_sq """
    try:
        sq = Square.FromSan(san_sq)
    except ValueError:
        return []  # illegal square, no moves

    board = RedisKungFuBoard(db, store_key)
    piece = board.get_piece(sq)
    moves = []

    # The ugly part...
    if piece.type == EMPTY:
        return []
    if piece.type == PAWN:
        o_sq = sq + OFFSETS[PAWN][piece.color]  # one move forward
        if o_sq and board[o_sq].type == EMPTY:
            moves.extend(create_pawn_moves(sq, o_sq, piece.color))
            if (sq.rank == PAWN_START_RANK[piece.color]):  # if on starting rank
                oo_sq = o_sq + OFFSETS[PAWN][piece.color]  # two moves forward
                if oo_sq and board[oo_sq].type == EMPTY:
                    moves.extend(create_pawn_moves(sq, oo_sq, piece.color))
        lo_sq = o_sq.left  # capture forward left
        if lo_sq.valid and board[lo_sq].color == other(piece.color):
            moves.extend(create_pawn_moves(sq, lo_sq, piece.color,
                                           extra_flags={Move.CAPTURE: board[lo_sq].type}))

        ro_sq = o_sq.right  # capture forward right
        if ro_sq.valid and board[ro_sq].color == other(piece.color):
            moves.extend(create_pawn_moves(sq, ro_sq, piece.color,
                                            extra_flags={Move.CAPTURE: board[lo_sq].type}))
    else:   # normal piece, excluding castle
        for offset in OFFSETS[piece.type]:
            o_sq = sq + offset
            while o_sq.valid:
                o_piece = board[o_sq]
                if o_piece.type == EMPTY:
                    moves.append(Move(sq, o_sq))
                else:
                    if o_piece.color == other(piece.color):
                        moves.append(Move(sq, o_sq,
                                          metadata={Move.CAPTURE: o_piece.type}))
                    break
                if not SLIDE[piece.type]:
                    break
                o_sq = o_sq + offset

    # castle
    if piece.type == KING:
        if board.can_castle(piece.color, KING):
            moves.append(Move(sq, sq.right.right,
                              metadata={Move.KCASTLE: True}))
        if board.can_castle(piece.color, QUEEN):
            moves.append(Move(sq, sq.left.left,
                              metadata={Move.QCASTLE: True}))

    return moves

def move(player, db, store_key, san_from_sq, san_to_sq, promote=None):
    """ Make a move from san_from_sq to san_to_sq, Return the move if
    it was made, or None otherwise. """
    try:
        from_sq = Square.FromSan(san_from_sq)
        to_sq = Square.FromSan(san_to_sq)
    except:
        return None

    if not from_sq.valid or not to_sq.valid:
        return None

    board = RedisKungFuBoard(db, store_key)

    if board.state != PLAYING:
        print("bad state")
        return None

    piece = board[from_sq]
    if piece.type == EMPTY or board.get_player(piece.color) != player:
        print(from_sq, piece)
        return None

    o_piece = board[to_sq]

    for move in moves(db, store_key, san_from_sq):
        if move.to_sq == to_sq and move.promote == promote:
            move_time = now()
            relative_move_time = move_time - board.start_time  # internally we hold relative times
            if piece.last_move is not None and board.cd > (relative_move_time - piece.last_move):  # move too early
                return None
            # TODO: Update history here

            # Do move
            board.move_piece(from_sq, to_sq, relative_move_time)
            # Do special moves
            if move.is_kingside_castle:
                castle_from = to_sq.right
                castle_to   = to_sq.left
                board.move_piece(castle_from, castle_to, relative_move_time)

            if move.is_queenside_castle:
                castle_from = to_sq.left.left
                castle_to = to_sq.right
                board.move_piece(castle_from, castle_to, relative_move_time)

            if move.promote:
                board.put_piece(move.promote, piece.color, to_sq, relative_move_time)

            # Update castles
            for color in COLORS:
                king_sqs  = CASTLE_DISABLING_SQUARES[color][KING]
                queen_sqs = CASTLE_DISABLING_SQUARES[color][QUEEN]
                if from_sq in king_sqs or to_sq in king_sqs:
                    board.disable_castle(color, KING)
                if from_sq in queen_sqs or to_sq in queen_sqs:
                    board.disable_castle(color, QUEEN)

            move._metadata[Move.TIME] = relative_move_time

            if board.winner == WHITE:
                board.set_state(W_WINS)
            elif board.winner == BLACK:
                board.set_state(B_WINS)
            return move, board.state

def to_dict(db, store_key):
    """ Return a dictionary representing the game """
    board = RedisKungFuBoard(db, store_key)
    res = {
        "cd": board.cd,
        "history": None, #TODO,
        "white": board.white,
        "black": board.black,
        "state": board.state,
        "current_time": now(),
        "start_time":   board.start_time,
        "nfen": "{} {} {}".format(board.fen, board.castles, board.move_number),
        "times": {}
    }

    for r in range(8):
        rank = r + 1
        for f in range(8):
            file = f + 1
            sq = Square.FromFileRank(file, rank)
            piece = board[sq]
            if (piece.last_move):  # only pass non-None times
                res["times"][sq.san] = piece.last_move

    return res

def create_pawn_moves(from_sq, to_sq, color, extra_flags=None):
    """ create pawn moves between squares, assuming the move is legal, and returns a list.
    """
    moves = []

    if not extra_flags:
        extra_flags = {}

    if to_sq.rank == PAWN_PROMOTE_RANK[color]:
        for piece in [QUEEN, ROOK, BISHOP, KNIGHT]:
            extra_flags.update({Move.PROMOTE: piece})
            move = Move(from_sq, to_sq, metadata=extra_flags)
            moves.append(move)
    else:
        moves.append(Move(from_sq, to_sq, metadata=extra_flags))

    return moves


def create_game_from_nfen(db, cd, store_key, *, exp=None, nfen=None):
    """ Initialize a new game from given nFEN in redis store at given store_key.

    nFEN, or not FEN, is based on the official FEN but without the 2nd, 4th and 5th parts,
    and where the move number is in half moves.
    For FEN notation see https://en.wikipedia.org/wiki/Forsyth%E2%80%93Edwards_Notation.
    nFEN is not complete, not containing the last move timestamp of each piece and current time
    """
    if not nfen:
        nfen = STARTING_NFEN

    board = RedisKungFuBoard(redis_db=db, cd=cd, store_key=store_key, exp=exp)
    board.clear()
    rows, castles, move_num = nfen.split(" ")

    for (rank, row) in enumerate(rows.split("/")):
        file = 0
        for l in row:
            sq = Square.FromFileRank(file + 1, 8 - rank )  # FEN ranks go from top to bottom
            try:
                spaces = int(l)
                file += spaces
            except ValueError:  # not an integer, then
                if l.isupper():
                    color = WHITE
                else:
                    color = BLACK
                board.put_piece(l.lower(), color, sq)
                file += 1

    board.set_move_number(int(move_num))
    board.set_start_time(now())
    board.set_castles(castles)

    board.set_state(WAITING) # for player assigment

    kings = board.get_all_pieces(type=KING)
    if len(kings) >= 3 or len(kings) == 0:
        raise ValueError("Invalid board given, should have 1 or 2 kings")

    return board

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
