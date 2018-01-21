/* Should include both kfchessjs and chessboardjs before this script */

window.onload = function()
{
var board,
  game = new Chess();

var makeRandomMove = function() {
  var possibleMoves = game.moves({
    legal: false,
    ignore_color: true,
    cooldown_time:  10000000000
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
  console.log(possibleMoves[randomIndex]);
  console.log(game.move(possibleMoves[randomIndex],
      {
        legal: false,
        ignore_color: true
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
/* Should include both kfchessjs and chessboardjs before this script * /

window.onload = function()
{
var board,
  game = new Chess();

// do not pick up pieces if the game is over
// only pick up pieces for the side to move
var onDragStart = function(source, piece, position, orientation) {
};

var onDrop = function(source, target) {
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
var onSnapEnd = function() {
  board.position(game.fen());
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