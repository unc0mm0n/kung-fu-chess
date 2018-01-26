/*
 * Copyright (c) 2016, Jeff Hlywa (jhlywa@gmail.com)
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice,
 *    this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the documentation
 *    and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 *
 *----------------------------------------------------------------------------*/

/* minified license below  */

/* @license
 * Copyright (c) 2016, Jeff Hlywa (jhlywa@gmail.com)
 * Released under the BSD license
 * https://github.com/jhlywa/chess.js/blob/master/LICENSE
 */

/* This modified version of the original chess.js is a derivative of the above.
 * Author: YuvalW (yvw.bor@gmail.com)
 *
 * - Add time since last move for each piece.
 * - Remove turn test from move legality
 * - Remove check/mate tests, and all draws apart of insufficient material
 * - Allow king capture
 */
var Chess = function(nfen, start_time) {

    var BLACK = 'b';
    var WHITE = 'w';

    var EMPTY = -1;

    var PAWN = 'p';
    var KNIGHT = 'n';
    var BISHOP = 'b';
    var ROOK = 'r';
    var QUEEN = 'q';
    var KING = 'k';

    var SYMBOLS = 'pnbrqkPNBRQK';

    var DEFAULT_POSITION = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR KQkq 1';

    var POSSIBLE_RESULTS = ['1-0', '0-1', '1/2-1/2', '*'];

    var PAWN_OFFSETS = {
        b: [16, 32, 17, 15],
        w: [-16, -32, -17, -15]
    };

    var PIECE_OFFSETS = {
        n: [-18, -33, -31, -14,  18, 33, 31,  14],
        b: [-17, -15,  17,  15],
        r: [-16,   1,  16,  -1],
        q: [-17, -16, -15,   1,  17, 16, 15,  -1],
        k: [-17, -16, -15,   1,  17, 16, 15,  -1]
    };

    var FLAGS = {
        NORMAL: 'n',
        CAPTURE: 'c',
        BIG_PAWN: 'b',
        EP_CAPTURE: 'e',
        PROMOTION: 'p',
        KSIDE_CASTLE: 'k',
        QSIDE_CASTLE: 'q'
    };

    var BITS = {
        NORMAL: 1,
        CAPTURE: 2,
        BIG_PAWN: 4,
        EP_CAPTURE: 8,
        PROMOTION: 16,
        KSIDE_CASTLE: 32,
        QSIDE_CASTLE: 64,
    };

    var RANK_1 = 7;
    var RANK_2 = 6;
    var RANK_3 = 5;
    var RANK_4 = 4;
    var RANK_5 = 3;
    var RANK_6 = 2;
    var RANK_7 = 1;
    var RANK_8 = 0;

    var SQUARES = {
        a8:   0, b8:   1, c8:   2, d8:   3, e8:   4, f8:   5, g8:   6, h8:   7,
        a7:  16, b7:  17, c7:  18, d7:  19, e7:  20, f7:  21, g7:  22, h7:  23,
        a6:  32, b6:  33, c6:  34, d6:  35, e6:  36, f6:  37, g6:  38, h6:  39,
        a5:  48, b5:  49, c5:  50, d5:  51, e5:  52, f5:  53, g5:  54, h5:  55,
        a4:  64, b4:  65, c4:  66, d4:  67, e4:  68, f4:  69, g4:  70, h4:  71,
        a3:  80, b3:  81, c3:  82, d3:  83, e3:  84, f3:  85, g3:  86, h3:  87,
        a2:  96, b2:  97, c2:  98, d2:  99, e2: 100, f2: 101, g2: 102, h2: 103,
        a1: 112, b1: 113, c1: 114, d1: 115, e1: 116, f1: 117, g1: 118, h1: 119
    };

    var ROOKS = {
        w: [{square: SQUARES.a1, flag: BITS.QSIDE_CASTLE},
            {square: SQUARES.h1, flag: BITS.KSIDE_CASTLE}],
        b: [{square: SQUARES.a8, flag: BITS.QSIDE_CASTLE},
            {square: SQUARES.h8, flag: BITS.KSIDE_CASTLE}]
    };

    var board = new Array(128);
    var kings = {w: EMPTY, b: EMPTY};
    var turn = WHITE;
    var castling = {w: 0, b: 0};
    var ep_square = EMPTY;
    var half_moves = 0;
    var move_number = 1;
    var history = [];
    var header = {};

    /* if the user passes in a nfen string, load it, else default to
     * starting position
     */
    if (typeof nfen === 'undefined') {
        load(DEFAULT_POSITION);
    } else {
        load(nfen);
    }

    function clear() {
        board = new Array(128);
        kings = {w: EMPTY, b: EMPTY};
        turn = WHITE;
        castling = {w: 0, b: 0};
        ep_square = EMPTY;
        half_moves = 0;
        move_number = 1;
        history = [];
        header = {};
        update_setup(generate_nfen());
    }

    function reset() {
        load(DEFAULT_POSITION);
    }

    function load(nfen) {
        var tokens = nfen.split(/\s+/);
        var position = tokens[0];
        var square = 0;

        if (!validate_nfen(nfen).valid) {
            console.log("Invalid nfen!");
            console.log(validate_nfen(nfen));
            return false;
        }

        clear();

        for (var i = 0; i < position.length; i++) {
            var piece = position.charAt(i);

            if (piece === '/') {
                square += 8;
            } else if (is_digit(piece)) {
                square += parseInt(piece, 10);
            } else {
                var color = (piece < 'a') ? WHITE : BLACK;
                put({type: piece.toLowerCase(), color: color, last_move_time: 0}, algebraic(square));
                square++;
            }
        }

        if (tokens[1].indexOf('K') > -1) {
            castling.w |= BITS.KSIDE_CASTLE;
        }
        if (tokens[1].indexOf('Q') > -1) {
            castling.w |= BITS.QSIDE_CASTLE;
        }
        if (tokens[1].indexOf('k') > -1) {
            castling.b |= BITS.KSIDE_CASTLE;
        }
        if (tokens[1].indexOf('q') > -1) {
            castling.b |= BITS.QSIDE_CASTLE;
        }

        move_number = parseInt(tokens[2], 10);

        update_setup(generate_nfen());

        return true;
    }

    /* TODO: this function is pretty much crap - it validates structure but
     * completely ignores content (e.g. doesn't verify that each side has a king)
     * ... we should rewrite this, and ditch the silly error_number field while
     * we're at it
     */
    function validate_nfen(nfen) {
        var errors = {
            0: 'No errors.',
            1: 'nFEN string must contain three space-delimited fields.',
            2: '3rd field (move number) must be a positive integer.',
            3: '2nd field (castling availability) is invalid.',
            4: '1st field (piece positions) does not contain 8 \'/\'-delimited rows.',
            5: '1st field (piece positions) is invalid [consecutive numbers].',
            6: '1st field (piece positions) is invalid [invalid piece].',
            7: '1st field (piece positions) is invalid [row too large].'
        };

        /* 1st criterion: 3 space-seperated fields? */
        var tokens = nfen.split(/\s+/);
        if (tokens.length !== 3) {
            return {valid: false, error_number: 1, error: errors[1]};
        }

        /* 2nd criterion: move number field is a integer value > 0? */
        if (isNaN(tokens[2]) || (parseInt(tokens[2], 10) <= 0)) {
            return {valid: false, error_number: 2, error: errors[2]};
        }

        /* 5th criterion: 2nd field is a valid castle-string? */
        if( !/^(KQ?k?q?|Qk?q?|kq?|q|-)$/.test(tokens[1])) {
            return {valid: false, error_number: 3, error: errors[3]};
        }

        /* 7th criterion: 1st field contains 8 rows? */
        var rows = tokens[0].split('/');
        if (rows.length !== 8) {
            return {valid: false, error_number: 4, error: errors[4]};
        }

        /* 8th criterion: every row is valid? */
        for (var i = 0; i < rows.length; i++) {
            /* check for right sum of fields AND not two numbers in succession */
            var sum_fields = 0;
            var previous_was_number = false;

            for (var k = 0; k < rows[i].length; k++) {
                if (!isNaN(rows[i][k])) {
                    if (previous_was_number) {
                        return {valid: false, error_number: 5, error: errors[5]};
                    }
                    sum_fields += parseInt(rows[i][k], 10);
                    previous_was_number = true;
                } else {
                    if (!/^[prnbqkPRNBQK]$/.test(rows[i][k])) {
                        return {valid: false, error_number: 6, error: errors[6]};
                    }
                    sum_fields += 1;
                    previous_was_number = false;
                }
            }
            if (sum_fields !== 8) {
                return {valid: false, error_number: 7, error: errors[7]};
            }
        }

        /* everything's okay! */
        return {valid: true, error_number: 0, error: errors[0]};
    }

    function generate_nfen() {
        var empty = 0;
        var nfen = '';

        for (var i = SQUARES.a8; i <= SQUARES.h1; i++) {
            if (board[i] == null) {
                empty++;
            } else {
                if (empty > 0) {
                    nfen += empty;
                    empty = 0;
                }
                var color = board[i].color;
                var piece = board[i].type;

                nfen += (color === WHITE) ?
                    piece.toUpperCase() : piece.toLowerCase();
            }

            if ((i + 1) & 0x88) {
                if (empty > 0) {
                    nfen += empty;
                }

                if (i !== SQUARES.h1) {
                    nfen += '/';
                }

                empty = 0;
                i += 8;
            }
        }

        var cflags = '';
        if (castling[WHITE] & BITS.KSIDE_CASTLE) { cflags += 'K'; }
        if (castling[WHITE] & BITS.QSIDE_CASTLE) { cflags += 'Q'; }
        if (castling[BLACK] & BITS.KSIDE_CASTLE) { cflags += 'k'; }
        if (castling[BLACK] & BITS.QSIDE_CASTLE) { cflags += 'q'; }

        /* do we have an empty castling flag? */
        cflags = cflags || '-';

        return [nfen, cflags, move_number].join(' ');
    }

    function set_header(args) {
        for (var i = 0; i < args.length; i += 2) {
            if (typeof args[i] === 'string' &&
                typeof args[i + 1] === 'string') {
                header[args[i]] = args[i + 1];
            }
        }
        return header;
    }

    /* called when the initial board setup is changed with put() or remove().
     * modifies the SetUp and nFEN properties of the header object.  if the nFEN is
     * equal to the default position, the SetUp and nFEN are deleted
     * the setup is only updated if history.length is zero, ie moves haven't been
     * made.
     */
    function update_setup(nfen) {
        if (history.length > 0) return;

        if (nfen !== DEFAULT_POSITION) {
            header['SetUp'] = '1';
            header['FEN'] = nfen;
        } else {
            delete header['SetUp'];
            delete header['FEN'];
        }
    }

    function get(square) {
        var piece = board[SQUARES[square]];
        return (piece) ? {type: piece.type, color: piece.color, last_move_time: piece.last_move_time} : null;
    }

    function put(piece, square) {
        /* check for valid piece object */
        if (!('type' in piece && 'color' in piece)) {
            return false;
        }

        /* check for piece */
        if (SYMBOLS.indexOf(piece.type.toLowerCase()) === -1) {
            return false;
        }

        /* check for valid square */
        if (!(square in SQUARES)) {
            return false;
        }

        var sq = SQUARES[square];

        /* don't let the user place more than one king */
        if (piece.type == KING &&
            !(kings[piece.color] == EMPTY || kings[piece.color] == sq)) {
            return false;
        }

        board[sq] = {type: piece.type, color: piece.color, last_move_time: 0};
        if (piece.type === KING) {
            kings[piece.color] = sq;
        }

        update_setup(generate_nfen());

        return true;
    }

    function remove(square) {
        var piece = get(square);
        board[SQUARES[square]] = null;
        if (piece && piece.type === KING) {
            kings[piece.color] = EMPTY;
        }

        update_setup(generate_nfen());

        return piece;
    }

    function build_move(board, from, to, flags, promotion) {
        var move = {
            color: board[from].color,
            from: from,
            to: to,
            flags: flags,
            piece: board[from].type
        };

        if (promotion) {
            move.flags |= BITS.PROMOTION;
            move.promotion = promotion;
        }

        if (board[to]) {
            move.captured = board[to].type;
        } else if (flags & BITS.EP_CAPTURE) {
            move.captured = PAWN;
        }
        return move;
    }

    function generate_moves(options) {
        function add_move(board, moves, from, to, flags) {
            /* if pawn promotion */
            if (board[from].type === PAWN &&
                (rank(to) === RANK_8 || rank(to) === RANK_1)) {
                var pieces = [QUEEN, ROOK, BISHOP, KNIGHT];
                for (var i = 0, len = pieces.length; i < len; i++) {
                    moves.push(build_move(board, from, to, flags, pieces[i]));
                }
            } else {
                moves.push(build_move(board, from, to, flags));
            }
        }

        var moves = [];
        var second_rank = {b: RANK_7, w: RANK_2};

        var first_sq = SQUARES.a8;
        var last_sq = SQUARES.h1;
        var single_square = false;

        /* do we want legal moves? */
        var cooldown_time = (typeof options !== 'undefined' && 'cooldown_time' in options) ?
            options.cooldown_time : 0;

        /* are we generating moves for a single square? */
        if (typeof options !== 'undefined' && 'square' in options) {
            if (options.square in SQUARES) {
                first_sq = last_sq = SQUARES[options.square];
                single_square = true;
            } else {
                /* invalid square */
                return [];
            }
        }

        for (var i = first_sq; i <= last_sq; i++) {
            /* did we run off the end of the board */
            if (i & 0x88) { i += 7; continue; }

            var piece = board[i];
            if (piece !== null && piece !== undefined) {
                console.log(Date.now(), piece.last_move_time, cooldown_time, Date.now() - piece.last_move_time);
            }
            if (piece == null) {
                continue;
            }
            else if (cooldown_time && ((Date.now() - piece.last_move_time) < cooldown_time)) {
                if (algebraic(i) === 'b8') {
                    /*console.log(algebraic(i),
                     Date.now(), piece.last_move_time,
                     Date.now() - piece.last_move_time,
                     cooldown_time,
                     Date.now() - piece.last_move_time < cooldown_time); /**/
                }
                continue;
            }

            if (piece.type === PAWN) {
                /* single square, non-capturing */
                square = i + PAWN_OFFSETS[piece.color][0];
                if (board[square] == null) {
                    add_move(board, moves, i, square, BITS.NORMAL);

                    /* double square */
                    square = i + PAWN_OFFSETS[piece.color][1];
                    if (second_rank[piece.color] === rank(i) && board[square] == null) {
                        add_move(board, moves, i, square, BITS.BIG_PAWN);
                    }
                }

                /* pawn captures */
                for (j = 2; j < 4; j++) {
                    square = i + PAWN_OFFSETS[piece.color][j];
                    if (square & 0x88) continue;

                    if (board[square] != null &&
                        board[square].color === swap_color(piece.color)) {
                        add_move(board, moves, i, square, BITS.CAPTURE);
                    } else if (square === ep_square) {
                        add_move(board, moves, i, ep_square, BITS.EP_CAPTURE);
                    }
                }
            } else {
                for (var j = 0, len = PIECE_OFFSETS[piece.type].length; j < len; j++) {
                    var offset = PIECE_OFFSETS[piece.type][j];
                    var square = i;

                    while (true) {
                        square += offset;
                        if (square & 0x88) break;

                        if (board[square] == null) {
                            add_move(board, moves, i, square, BITS.NORMAL);
                        } else {
                            if (board[square].color === piece.color) break;
                            add_move(board, moves, i, square, BITS.CAPTURE);
                            break;
                        }

                        /* check for castling if: a) we're generating all moves, or b) we're doing
                         * single square move generation on the king's square
                         */
                        if (piece.type == 'k') {
                            if (castling[piece.color] & BITS.KSIDE_CASTLE) {
                                var castling_from = kings[piece.color];
                                var castling_to = castling_from + 2;

                                if (board[castling_from + 1] == null &&
                                    board[castling_to] == null)
                                {
                                    add_move(board, moves, kings[piece.color], castling_to,
                                        BITS.KSIDE_CASTLE);
                                }
                            }

                            /* queen-side castling */
                            if (castling[piece.color] & BITS.QSIDE_CASTLE) {
                                var castling_from = kings[piece.color];
                                var castling_to = castling_from - 2;

                                if (board[castling_from - 1] == null &&
                                    board[castling_from - 2] == null &&
                                    board[castling_from - 3] == null)
                                {
                                    add_move(board, moves, kings[piece.color], castling_to,
                                        BITS.QSIDE_CASTLE);
                                }
                            }
                        }

                        /* break, if knight or king */
                        if (piece.type === 'n' || piece.type === 'k') break;
                    }
                }
            }
        }

        /* return all pseudo-legal moves (this includes moves that allow the king
         * to be captured)
         */
        return moves;
    }

    /* convert a move from 0x88 coordinates to Almost Standard Algebraic Notation
     * (ASAN)
     */
    function move_to_san(move, sloppy) {

        var output = '';

        if (move.flags & BITS.KSIDE_CASTLE) {
            output = 'O-O';
        } else if (move.flags & BITS.QSIDE_CASTLE) {
            output = 'O-O-O';
        } else {

            if (move.flags & (BITS.CAPTURE | BITS.EP_CAPTURE)) {
                if (move.piece === PAWN) {
                    output += algebraic(move.from)[0];
                }
                output += 'x';
            }

            output += algebraic(move.to);

            if (move.flags & BITS.PROMOTION) {
                output += '=' + move.promotion.toUpperCase();
            }
        }

        /*
         if (move.flags & BITS.CHECK) {
         if (move.flags & BITS.MATE) {
         output += '#';
         } else {
         output += '+';
         }
         }*/

        return output;
    }

    // parses all of the decorators out of a SAN string
    function stripped_san(move) {
        return move.replace(/=/,'').replace(/[+#]?[?!]*$/,'');
    }

    function is_won()
    {
        return (kings[WHITE] == EMPTY || kings[BLACK] == EMPTY);
    }

    function in_draw()
    {
        return insufficient_material();
    }
    function insufficient_material() {
        var pieces = {};
        var bishops = [];
        var num_pieces = 0;
        var sq_color = 0;

        for (var i = SQUARES.a8; i<= SQUARES.h1; i++) {
            sq_color = (sq_color + 1) % 2;
            if (i & 0x88) { i += 7; continue; }

            var piece = board[i];
            if (piece) {
                pieces[piece.type] = (piece.type in pieces) ?
                pieces[piece.type] + 1 : 1;
                if (piece.type === BISHOP) {
                    bishops.push(sq_color);
                }
                num_pieces++;
            }
        }

        /* k vs. k */
        if (num_pieces === 2) { return true; }

        /* k vs. kn .... or .... k vs. kb */
        else if (num_pieces === 3 && (pieces[BISHOP] === 1 ||
            pieces[KNIGHT] === 1)) { return true; }

        /* kb vs. kb where any number of bishops are all on the same color */
        else if (num_pieces === pieces[BISHOP] + 2) {
            var sum = 0;
            var len = bishops.length;
            for (var i = 0; i < len; i++) {
                sum += bishops[i];
            }
            if (sum === 0 || sum === len) { return true; }
        }

        return false;
    }

    function push(move, time) {
        history.push({
            move: move,
            move_time : time,
            kings: {b: kings.b, w: kings.w},
            castling: {b: castling.b, w: castling.w},
            ep_square: ep_square,
            half_moves: half_moves,
            move_number: move_number
        });
    }

    function make_move(move, time) {
        var us = move.color;
        var them = swap_color(us);
        var original_time = board[move.from].last_move_time;
        push(move, original_time);

        if (board[move.to] && board[move.to].type == KING)
        {
            kings[board[move.to].color] = EMPTY;
        }
        board[move.to] = board[move.from];
        console.log('move', start_time, time);
        board[move.to].last_move_time = start_time + time;
        board[move.from] = null;

        /* if ep capture, remove the captured pawn */
        if (move.flags & BITS.EP_CAPTURE) {
            if (us === BLACK) {
                board[move.to - 16] = null;
            } else {
                board[move.to + 16] = null;
            }
        }

        /* if pawn promotion, replace with new piece */
        if (move.flags & BITS.PROMOTION) {
            board[move.to] = {type: move.promotion, color: us, last_move_time : time};
        }

        /* if we moved the king */
        if (board[move.to].type === KING) {
            kings[board[move.to].color] = move.to;

            /* if we castled, move the rook next to the king */
            if (move.flags & BITS.KSIDE_CASTLE) {
                var castling_to = move.to - 1;
                var castling_from = move.to + 1;
                board[castling_to] = board[castling_from];
                board[castling_to].last_move_time = start_time + time;
                board[castling_from] = null;
            } else if (move.flags & BITS.QSIDE_CASTLE) {
                var castling_to = move.to + 1;
                var castling_from = move.to - 2;
                board[castling_to] = board[castling_from];
                board[castling_to].last_move_time = start_time + time;
                board[castling_from] = null;
            }

            /* turn off castling */
            castling[us] = '';
        }

        /* turn off castling if we move a rook */
        if (castling[us]) {
            for (var i = 0, len = ROOKS[us].length; i < len; i++) {
                if (move.from === ROOKS[us][i].square &&
                    castling[us] & ROOKS[us][i].flag) {
                    castling[us] ^= ROOKS[us][i].flag;
                    break;
                }
            }
        }

        /* turn off castling if we capture a rook */
        if (castling[them]) {
            for (var i = 0, len = ROOKS[them].length; i < len; i++) {
                if (move.to === ROOKS[them][i].square &&
                    castling[them] & ROOKS[them][i].flag) {
                    castling[them] ^= ROOKS[them][i].flag;
                    break;
                }
            }
        }

        /* if big pawn move, update the en passant square */
        if (move.flags & BITS.BIG_PAWN) {
            if (turn === 'b') {
                ep_square = move.to - 16;
            } else {
                ep_square = move.to + 16;
            }
        } else {
            ep_square = EMPTY;
        }

        move_number++;
    }

    function undo_move() {
        var old = history.pop();
        if (old == null) { return null; }

        var move = old.move;
        kings = old.kings;
        color = old.move.color;
        castling = old.castling;
        ep_square = old.ep_square;
        half_moves = old.half_moves;
        move_number = old.move_number;
        move_time = old.move_time;

        var us = color;
        var them = swap_color(us);

        board[move.from] = board[move.to];
        board[move.from].type = move.piece;  // to undo any promotions
        board[move.from].last_move_time = move_time;  // reset timer
        board[move.to] = null;

        if (move.flags & BITS.CAPTURE) {
            board[move.to] = {type: move.captured, color: them};
        } else if (move.flags & BITS.EP_CAPTURE) {
            var index;
            if (us === BLACK) {
                index = move.to - 16;
            } else {
                index = move.to + 16;
            }
            board[index] = {type: PAWN, color: them};
        }


        if (move.flags & (BITS.KSIDE_CASTLE | BITS.QSIDE_CASTLE)) {
            var castling_to, castling_from;
            if (move.flags & BITS.KSIDE_CASTLE) {
                castling_to = move.to + 1;
                castling_from = move.to - 1;
            } else if (move.flags & BITS.QSIDE_CASTLE) {
                castling_to = move.to - 2;
                castling_from = move.to + 1;
            }

            board[castling_to] = board[castling_from];
            board[castling_from] = null;
        }

        move_number--;

        return move;
    }

    function ascii() {
        var s = '   +------------------------+\n';
        for (var i = SQUARES.a8; i <= SQUARES.h1; i++) {
            /* display the rank */
            if (file(i) === 0) {
                s += ' ' + '87654321'[rank(i)] + ' |';
            }

            /* empty piece */
            if (board[i] == null) {
                s += ' . ';
            } else {
                var piece = board[i].type;
                var color = board[i].color;
                var symbol = (color === WHITE) ?
                    piece.toUpperCase() : piece.toLowerCase();
                s += ' ' + symbol + ' ';
            }

            if ((i + 1) & 0x88) {
                s += '|\n';
                i += 8;
            }
        }
        s += '   +------------------------+\n';
        s += '     a  b  c  d  e  f  g  h\n';

        return s;
    }

    // convert a move from Standard Algebraic Notation (SAN) to 0x88 coordinates
    function move_from_san(move, sloppy, move_options) {
        // strip off any move decorations: e.g Nf3+?!
        var clean_move = stripped_san(move);

        // if we're using the sloppy parser run a regex to grab piece, to, and from
        // this should parse invalid SAN like: Pe2-e4, Rc1c4, Qf3xf7
        if (sloppy) {
            var matches = clean_move.match(/([pnbrqkPNBRQK])?([a-h][1-8])x?-?([a-h][1-8])([qrbnQRBN])?/);
            if (matches) {
                var piece = matches[1];
                var from = matches[2];
                var to = matches[3];
                var promotion = matches[4];
            }
        }

        var moves = generate_moves(move_options);

        for (var i = 0, len = moves.length; i < len; i++) {
            // try the strict parser first, then the sloppy parser if requested
            // by the user
            if ((clean_move === stripped_san(move_to_san(moves[i]))) ||
                (sloppy && clean_move === stripped_san(move_to_san(moves[i], true)))) {
                return moves[i];
            } else {
                if (matches &&
                    (!piece || piece.toLowerCase() == moves[i].piece) &&
                    SQUARES[from] == moves[i].from &&
                    SQUARES[to] == moves[i].to &&
                    (!promotion || promotion.toLowerCase() == moves[i].promotion)) {
                    return moves[i];
                }
            }
        }

        return null;
    }


    /*****************************************************************************
     * UTILITY FUNCTIONS
     ****************************************************************************/
    function rank(i) {
        return i >> 4;
    }

    function file(i) {
        return i & 15;
    }

    function algebraic(i){
        var f = file(i), r = rank(i);
        return 'abcdefgh'.substring(f,f+1) + '87654321'.substring(r,r+1);
    }

    function swap_color(c) {
        return c === WHITE ? BLACK : WHITE;
    }

    function is_digit(c) {
        return '0123456789'.indexOf(c) !== -1;
    }

    /* pretty = external move object */
    function make_pretty(ugly_move) {
        var move = clone(ugly_move);
        move.san = move_to_san(move, false);
        move.to = algebraic(move.to);
        move.from = algebraic(move.from);

        var flags = '';

        for (var flag in BITS) {
            if (BITS[flag] & move.flags) {
                flags += FLAGS[flag];
            }
        }
        move.flags = flags;

        return move;
    }

    function clone(obj) {
        var dupe = (obj instanceof Array) ? [] : {};

        for (var property in obj) {
            if (typeof property === 'object') {
                dupe[property] = clone(obj[property]);
            } else {
                dupe[property] = obj[property];
            }
        }

        return dupe;
    }

    function trim(str) {
        return str.replace(/^\s+|\s+$/g, '');
    }

    /*****************************************************************************
     * DEBUGGING UTILITIES
     ****************************************************************************/
    function perft(depth) {
        var moves = generate_moves({legal: false});
        var nodes = 0;
        var color = turn;

        for (var i = 0, len = moves.length; i < len; i++) {
            make_move(moves[i]);
            if (!king_attacked(color)) {
                if (depth - 1 > 0) {
                    var child_nodes = perft(depth - 1);
                    nodes += child_nodes;
                } else {
                    nodes++;
                }
            }
            undo_move();
        }

        return nodes;
    }

    return {
        /***************************************************************************
         * PUBLIC CONSTANTS (is there a better way to do this?)
         **************************************************************************/
        WHITE: WHITE,
        BLACK: BLACK,
        PAWN: PAWN,
        KNIGHT: KNIGHT,
        BISHOP: BISHOP,
        ROOK: ROOK,
        QUEEN: QUEEN,
        KING: KING,
        SQUARES: (function() {
            /* from the ECMA-262 spec (section 12.6.4):
             * "The mechanics of enumerating the properties ... is
             * implementation dependent"
             * so: for (var sq in SQUARES) { keys.push(sq); } might not be
             * ordered correctly
             */
            var keys = [];
            for (var i = SQUARES.a8; i <= SQUARES.h1; i++) {
                if (i & 0x88) { i += 7; continue; }
                keys.push(algebraic(i));
            }
            return keys;
        })(),
        FLAGS: FLAGS,

        /***************************************************************************
         * PUBLIC API
         **************************************************************************/
        load: function(fen) {
            return load(fen);
        },

        reset: function() {
            return reset();
        },

        moves: function(options) {
            /* The internal representation of a chess move is in 0x88 format, and
             * not meant to be human-readable.  The code below converts the 0x88
             * square coordinates to algebraic coordinates.  It also prunes an
             * unnecessary move keys resulting from a verbose call.
             */

            var ugly_moves = generate_moves(options);
            var moves = [];

            for (var i = 0, len = ugly_moves.length; i < len; i++) {
                moves.push(make_pretty(ugly_moves[i]));
            }

            return moves;
        },

        in_draw: function() {
            return in_draw();
        },

        game_over: function() {
            return in_draw()
                || is_won();
        },

        validate_nfen: function(fen) {
            return validate_nfen(fen);
        },

        nfen: function() {
            return generate_nfen();
        },

        kfpgn: function(options) {
            /* PGN for kung-fu chess, which is pretty similar to normal pgn but more explicit and less informative
             * example for html usage: .pgn({ max_width: 72, newline_char: "<br />" })
             */
            var newline = (typeof options === 'object' &&
            typeof options.newline_char === 'string') ?
                options.newline_char : '\n';
            var max_width = (typeof options === 'object' &&
            typeof options.max_width === 'number') ?
                options.max_width : 0;
            var result = [];
            var header_exists = false;

            /* add the PGN header headerrmation */
            for (var i in header) {
                /* TODO: order of enumerated properties in header object is not
                 * guaranteed, see ECMA-262 spec (section 12.6.4)
                 */
                result.push('[' + i + ' \"' + header[i] + '\"]' + newline);
                header_exists = true;
            }

            if (header_exists && history.length) {
                result.push(newline);
            }

            /* pop all of history onto reversed_history */
            var reversed_history = [];
            while (history.length > 0) {
                reversed_history.push(undo_move());
            }

            var moves = [];
            var move_string = '';

            /* build the list of moves.  a move_string looks like: "3. e3 e6" */
            while (reversed_history.length > 0) {
                var move = reversed_history.pop();

                /* if the position started with black to move, start PGN with 1. ... */
                if (move.color === 'b') {
                    move_string = move_number + '.B';
                } else if (move.color === 'w') {
                    move_string = move_number + '.W';
                }

                move_string = move_string + '' + move_to_san(move, false);
                moves.push(move_string);
                make_move(move);
            }

            /* is there a result? */
            if (typeof header.Result !== 'undefined') {
                moves.push(header.Result);
            }

            /* history should be back to what is was before we started generating PGN,
             * so join together moves
             */
            if (max_width === 0) {
                return result.join('') + moves.join(' ');
            }

            /* wrap the PGN output at max_width */
            var current_width = 0;
            for (var i = 0; i < moves.length; i++) {
                /* if the current move will push past max_width */
                if (current_width + moves[i].length > max_width && i !== 0) {

                    /* don't end the line with whitespace */
                    if (result[result.length - 1] === ' ') {
                        result.pop();
                    }

                    result.push(newline);
                    current_width = 0;
                } else if (i !== 0) {
                    result.push(' ');
                    current_width++;
                }
                result.push(moves[i]);
                current_width += moves[i].length;
            }

            return result.join('');
        },

        load_pgn: function(pgn, options) {
            // allow the user to specify the sloppy move parser to work around over
            // disambiguation bugs in Fritz and Chessbase
            var sloppy = (typeof options !== 'undefined' && 'sloppy' in options) ?
                options.sloppy : false;

            function mask(str) {
                return str.replace(/\\/g, '\\');
            }

            function has_keys(object) {
                for (var key in object) {
                    return true;
                }
                return false;
            }

            function parse_pgn_header(header, options) {
                var newline_char = (typeof options === 'object' &&
                typeof options.newline_char === 'string') ?
                    options.newline_char : '\r?\n';
                var header_obj = {};
                var headers = header.split(new RegExp(mask(newline_char)));
                var key = '';
                var value = '';

                for (var i = 0; i < headers.length; i++) {
                    key = headers[i].replace(/^\[([A-Z][A-Za-z]*)\s.*\]$/, '$1');
                    value = headers[i].replace(/^\[[A-Za-z]+\s"(.*)"\]$/, '$1');
                    if (trim(key).length > 0) {
                        header_obj[key] = value;
                    }
                }

                return header_obj;
            }

            var newline_char = (typeof options === 'object' &&
            typeof options.newline_char === 'string') ?
                options.newline_char : '\r?\n';
            var regex = new RegExp('^(\\[(.|' + mask(newline_char) + ')*\\])' +
                '(' + mask(newline_char) + ')*' +
                '1.(' + mask(newline_char) + '|.)*$', 'g');

            /* get header part of the PGN file */
            var header_string = pgn.replace(regex, '$1');

            /* no info part given, begins with moves */
            if (header_string[0] !== '[') {
                header_string = '';
            }

            reset();

            /* parse PGN header */
            var headers = parse_pgn_header(header_string, options);
            for (var key in headers) {
                set_header([key, headers[key]]);
            }

            /* load the starting position indicated by [Setup '1'] and
             * [FEN position] */
            if (headers['SetUp'] === '1') {
                if (!(('FEN' in headers) && load(headers['FEN']))) {
                    return false;
                }
            }

            /* delete header to get the moves */
            var ms = pgn.replace(header_string, '').replace(new RegExp(mask(newline_char), 'g'), ' ');

            /* delete comments */
            ms = ms.replace(/(\{[^}]+\})+?/g, '');

            /* delete recursive annotation variations */
            var rav_regex = /(\([^\(\)]+\))+?/g
            while (rav_regex.test(ms)) {
                ms = ms.replace(rav_regex, '');
            }

            /* delete move numbers */
            ms = ms.replace(/\d+\.(\.\.)?/g, '');

            /* delete ... indicating black to move */
            ms = ms.replace(/\.\.\./g, '');

            /* delete numeric annotation glyphs */
            ms = ms.replace(/\$\d+/g, '');

            /* trim and get array of moves */
            var moves = trim(ms).split(new RegExp(/\s+/));

            /* delete empty entries */
            moves = moves.join(',').replace(/,,+/g, ',').split(',');
            var move = '';

            for (var half_move = 0; half_move < moves.length - 1; half_move++) {
                move = move_from_san(moves[half_move], sloppy);

                /* move not possible! (don't clear the board to examine to show the
                 * latest valid position)
                 */
                if (move == null) {
                    return false;
                } else {
                    make_move(move);
                }
            }

            /* examine last move */
            move = moves[moves.length - 1];
            if (POSSIBLE_RESULTS.indexOf(move) > -1) {
                if (has_keys(header) && typeof header.Result === 'undefined') {
                    set_header(['Result', move]);
                }
            }
            else {
                move = move_from_san(move, sloppy);
                if (move == null) {
                    return false;
                } else {
                    make_move(move);
                }
            }
            return true;
        },

        header: function() {
            return set_header(arguments);
        },

        ascii: function() {
            return ascii();
        },

        turn: function() {
            return turn;
        },

        move: function(move, options) {
            /* The move function can be called with in the following parameters:
             *
             * .move('Nxb7')      <- where 'move' is a case-sensitive SAN string
             *
             * .move({ from: 'h7', <- where the 'move' is a move object (additional
             *         to :'h8',      fields are ignored)
             *         promotion: 'q',
             *      })
             */

            // allow the user to specify the sloppy move parser to work around over
            // disambiguation bugs in Fritz and Chessbase
            var sloppy = (typeof options !== 'undefined' && 'sloppy' in options) ?
                options.sloppy : false;

            var move_obj = null;

            if (typeof move === 'string') {
                move_obj = move_from_san(move, sloppy, options);
            } else if (typeof move === 'object') {
                var moves = generate_moves(options);

                /* convert the pretty move object to an ugly move object */
                for (var i = 0, len = moves.length; i < len; i++) {
                    if (move.from === algebraic(moves[i].from) &&
                        move.to === algebraic(moves[i].to) &&
                        (!('promotion' in moves[i]) ||
                        move.promotion === moves[i].promotion)) {
                        move_obj = moves[i];
                        break;
                    }
                }
            }

            /* failed to find move */
            if (!move_obj) {
                return null;
            }

            /* need to make a copy of move because we can't generate SAN after the
             * move is made
             */
            var time = Date.now()
            if ("time" in options)
            {
                time = options.time;
            }
            make_move(move_obj, time);

            var pretty_move = make_pretty(move_obj);
            return pretty_move;
        },

        undo: function() {
            var move = undo_move();
            return (move) ? make_pretty(move) : null;
        },

        clear: function() {
            return clear();
        },

        put: function(piece, square) {
            return put(piece, square);
        },

        get: function(square) {
            return get(square);
        },

        remove: function(square) {
            return remove(square);
        },

        perft: function(depth) {
            return perft(depth);
        },

        square_color: function(square) {
            if (square in SQUARES) {
                var sq_0x88 = SQUARES[square];
                return ((rank(sq_0x88) + file(sq_0x88)) % 2 === 0) ? 'light' : 'dark';
            }

            return null;
        },

        history: function(options) {
            var reversed_history = [];
            var move_history = [];
            var verbose = (typeof options !== 'undefined' && 'verbose' in options &&
            options.verbose);

            while (history.length > 0) {
                reversed_history.push(undo_move());
            }

            while (reversed_history.length > 0) {
                var move = reversed_history.pop();
                move_history.push(make_pretty(move));
                make_move(move);
            }

            return move_history;
        }

    };
};

/* export Chess object if using node or any other CommonJS compatible
 * environment */
if (typeof exports !== 'undefined') exports.Chess = Chess;
/* export Chess object for any RequireJS compatible environment */
if (typeof define !== 'undefined') define( function () { return Chess;  });
