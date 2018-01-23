/* Should include both kfchessjs and chessboardjs before this script */

window.onload = function() {

//------------------------------------------------------------------------------
// timer functions
//------------------------------------------------------------------------------

  var interval = 17; // approx 60 fps
  var cd = 1000;    // testing

  var board, game = new Chess(), disabledSquares = {};

  function colorSquare(sq, duration) {
    disabledSquares[sq] = true;
    var squareEl = $('#board .square-' + sq);
    console.log(squareEl.children());
    squareEl.wrapInner("<div class='sq" + sq + "-inner'></div>");
    innerEl = $('#board .square-' + sq + " > .sq" + sq + "-inner");
    colorSquareRec(Date.now(), Date.now(), duration, innerEl, sq);
  }

  function colorSquareRec(start, expected, total, elem, sq) {
    var dnow = Date.now();
    var dt = dnow - expected;

    var background = '#900';
    var percent = (100 - 100 * (dnow - start) / total);
    elem.css('background', background);
    elem.css('height', percent + "%");
    elem.css('width', "100%");
    expected += interval;

    if (dnow - start < total) {
      setTimeout(colorSquareRec, Math.max(0, interval - dt), start, expected, total, elem, sq); // take into account drift
    }
    else {
      disabledSquares[sq] = false;
      elem.contents().unwrap();
    }
  }

  var onDragStart = function (source, piece) {
    // do not pick up pieces if the game is over
    // or if it's not that side's turn
    if (game.game_over() === true ||
        (source in disabledSquares && disabledSquares[source] == true)) {
      console.log(source, disabledSquares);
      return false;
    }
  };
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

  /* Self play example */
  /* Should include both kfchessjs and chessboardjs before this script */
  var onDrop = function (source, target) {
    // see if the move is legal
    var move = game.move({
          from: source,
          to: target,
          promotion: 'q' // NOTE: always promote to a queen for example simplicity
        },
        {
          legal: false,
          ignore_color: true,
          cooldown_time: 0
        });

    // illegal move
    if (move === null) return 'snapback';
  };

  // update the board position after the piece snap
  // for castling, en passant, pawn promotion
  var onSnapEnd = function (source, target) {
    board.position(game.fen());
    colorSquare(target, cd);
  };


  var cfg = {
    draggable: true,
    position: 'start',
    onDragStart: onDragStart,
    onDrop: onDrop,
    onSnapEnd: onSnapEnd,
    position: 'start',
    pieceTheme: "static/libs/chessboardjs-0.3.0/img/chesspieces/wikipedia/{piece}.png"
  };
  board = ChessBoard('board', cfg);
};
/* */