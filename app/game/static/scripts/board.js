/* Should include both kfchessjs and chessboardjs before this script */

"use strict";

$(window).ready(function() {
  //------------------------------------------------------------------------------
  // create socket context - we only work if we have an active socket connection
  //------------------------------------------------------------------------------
  var socket = io('/game');
  socket.on('connect', function() {

    //------------------------------------------------------------------------------
    // timed functions
    //------------------------------------------------------------------------------

    var interval = 17; // approx 60 fps
    var cd = 4000;    // testing TODO: Get from server on game start

    /*
     * Disable the square for given duration.
     * start is optional timestamp to start counting from. Will use Date.now() if none given.
     */
    function disableSquare(sq, duration, start) {
      if (start == undefined || typeof start !== 'number') {
        start = Date.now();
      }
      disabledSquares[sq] = true;
      var squareEl = $('#board .square-' + sq);
      squareEl.wrapInner("<div class='sq" + sq + "-inner'></div>");
      var innerEl = $('#board .square-' + sq + " > .sq" + sq + "-inner");
      disableSquareRec(start, Date.now(), duration, innerEl, sq);
    }

    function disableSquareRec(start, expected, total, elem, sq) {
      var dnow = Date.now();
      var dt = dnow - expected;

      var background = '#900';
      var percent = (100 - 100 * (dnow - start) / total);
      elem.css('background', background);
      elem.css('height', percent + "%");
      elem.css('width', "100%");
      expected += interval;

      if (dnow - start < total) {
        setTimeout(disableSquareRec, Math.max(0, interval - dt), start, expected, total, elem, sq); // take into account drift
      }
      else {
        disabledSquares[sq] = false;
        elem.contents().unwrap();

      }
    }

    //------------------------------------------------------------------------------
    // socket handlers
    //------------------------------------------------------------------------------

    socket.on('move-cnf', function(move_desc) {
      console.log("received move ");
      console.log(move_desc);
      var move = game.move(move_desc, {
        ignore_color: true,
        cd: cd
      });
      if (move === null)
      {
        //TODO: Error getting move, ask for resync
        return;
      }

      board.position(game.fen());
      disableSquare(move.to, cd, move_desc.time);
    });

    //------------------------------------------------------------------------------
    // Board event handlers
    //------------------------------------------------------------------------------

    var onDragStart = function (source, piece) {
      // do not pick up pieces if the game is over
      // or if it's still disabled
      if (game.game_over() === true ||
          (source in disabledSquares && disabledSquares[source] == true)) {
        return false;
      }
    };

    var onDrop = function (source, target) {
      // get all legal moves from source
      // see if move to target is there
      var piece_moves = game.moves({
        square: source,
        ignore_color: true,
        cooldown_time: cd
      });

      var move = null;

      for (var i = 0; i < piece_moves.length; i++) {
        if (piece_moves[i].to === target) {
          move = piece_moves[i];
          break;
        }
      }

      if (move !== null) { // client decided move is legal
        // now verify on server
        console.log('emitting move');
        console.log(move);
        socket.emit('move-req', move);
      }
      else {
        return 'snapback'
      }
      // we let the move happen, will be fixed after server checks the move anyway

    };

    //------------------------------------------------------------------------------
    // Finally do something
    //------------------------------------------------------------------------------
    console.log("connected");

    var game = new Chess();
    var disabledSquares = {};

    var cfg = {
      draggable: true,
      position: 'start',
      onDragStart: onDragStart,
      onDrop: onDrop,
      pieceTheme: "static/libs/chessboardjs-0.3.0/img/chesspieces/wikipedia/{piece}.png"

    };

    var board = ChessBoard('board', cfg);

    // test function that makes random moves
    var makeRandomMoves = function() {
      var possibleMoves = game.moves({
        ignore_color: true,
        cooldown_time: 5000
      });
      if (game.game_over() === true) {
        return;
      }
      var randomIndex = Math.floor(Math.random() * possibleMoves.length);

      console.log("requesting move ");
      console.log(possibleMoves[randomIndex]);
      socket.emit('move-req', possibleMoves[randomIndex]); // request the move
      window.setTimeout(makeRandomMoves, 500);
    };

    window.setTimeout(makeRandomMoves, 500);

    // be nice citizens and close the socket
    $(window).on('beforeunload', function () {
      socket.close();
    });

//============================================= Start test stuff =================================================//

    /*
     var makeRandomMove = function() {
     var possibleMoves = game.moves({
     ignore_color: true,
     cooldown_time:  5000
     });

     // exit if the game is over
     if (game.game_over() === true ||
     game.in_draw() === true ||
     possibleMoves.length === 0)
     {
     console.log("gg");
     return;
     }

     var randomIndex = Math.floor(Math.random() * possibleMoves.length);

     console.log(game.move(possibleMoves[randomIndex],
     {
     ignore_color: true,
     cooldown_time:  5000
     }));

     board.position(game.fen());

     window.setTimeout(makeRandomMove, 500);
     };

     board = ChessBoard('board', {
     position: 'start',
     pieceTheme: "static/libs/chessboardjs-0.3.0/img/chesspieces/wikipedia/{piece}.png"
     });

     window.game = game; // for debug
     window.setTimeout(makeRandomMove, 500);

     }; /* */

  });

});
/* */