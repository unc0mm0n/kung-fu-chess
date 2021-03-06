/* Should include both kfchessjs and chessboardjs before this script */

"use strict";

$(window).ready(function() {
  //------------------------------------------------------------------------------
  // create socket context - we only work if we have an active socket connection
  //------------------------------------------------------------------------------
  var socket = io('/game');
  socket.on('connect', function() {

    var color;

    //------------------------------------------------------------------------------
    // timed functions
    //------------------------------------------------------------------------------

    var interval = 17; // approx 60 fps
    var cd = 4000;    // testing TODO: Get from server on game start
    var start_time;
    var time_offset;

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
      disableSquareRec(start_time + start, Date.now(), duration, innerEl, sq);
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

    socket.on('ind', function(d)
    {
      console.log("got ind" + d);
    });
    socket.on('sync-cnf', function(sync_desc) {

      console.log(sync_desc)
      var now = Date.now();
      if (sync_desc['result'] == 'fail') { // invalid id or not id
        //TODO: should handle in informative way, shouldn't really happen though
        console.log("failed to sync", sync_desc);
        alert("invalid game ID")
        location.replace("/")
        return
      }
      console.log("received sync");
      console.log(sync_desc);
      time_offset = now - sync_desc.board.current_time;
      start_time  = sync_desc.board.start_time + time_offset;
      cd = sync_desc.board.cd;
      color = sync_desc.color;
      if (color == 'w') {
        $("#content-title").text("You are playing white.");
      }
      else if (color == 'b') {
        $("#content-title").text("You are playing Black.");
        board.flip();
      }
      else
      {
        $("#content-title").text("You are an observer.");
      }
      var nfen = sync_desc.board.nfen;
      game = Chess(nfen, start_time);
      board.position(game.nfen());

      for (var [key, value] of Object.entries(sync_desc.board.times)) {
        disableSquare(key, cd, value)
      }

    });


    socket.on('move-cnf', function(move_desc) {

      if (move_desc['result'] == 'fail') { // move was illegal, update board and ask for resync
        console.log('illegal move response received');
        socket.emit("sync-req", game_id);
        board.position(game.nfen());
        return;
      }

      console.log("received move");
      console.log(move_desc);
      var move = move_desc.move;
      var res  = game.move(move, {
        ignore_color: true,
        cd: cd,
        time: move_desc.time
      });

      if (res === null)
      {
        console.log("Invalid move received, requesting sync");
        socket.emit("sync-req", game_id);
        return;
      }

      if (game.game_over()) {
        alert("Game over! "+ game.winner() +" wins!");
        window.location = "/";
      }

     console.log(res)
      var changes = board.position(game.nfen());
      for (var i = 0; i < changes.length; i++) {
        disableSquare(changes[i].destination, cd, move.time);
      }
      disableSquare(move.to, cd, move.time);
    });

    //------------------------------------------------------------------------------
    // Board event handlers
    //------------------------------------------------------------------------------
    var removeAvailableSquares = function() {
      $('#board .square-55d63').css('background', '');
    };

    var setSquareAvailable = function(square) {
      var squareEl = $('#board .square-' + square);

      var background = '#a9a9a9';
      if (squareEl.hasClass('black-3c85d') === true) {
        background = '#696969';
      }

      squareEl.css('background', background);
    };
    var onDragStart = function (source, piece) {
      // do not pick up pieces if the game is over
      // or if it's still disabled
      if (game.game_over() === true ||
          (source in disabledSquares && disabledSquares[source] == true) ||
          game.get(source).color != color) {
        return false;
      }
    };

    var onDrop = function (source, target) {
      removeAvailableSquares(); // first unmark squares

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
        socket.emit('move-req', game_id, move);
      }
      else {
        return 'snapback'
      }
      // we let the move happen, will be fixed after server checks the move anyway
    };

    var onMouseoverSquare = function(square, piece) {
      if ((square in disabledSquares && disabledSquares[square] == true) ||
          game == undefined ||
          game.game_over() === true) {
        return;
      }

      if (piece === false || piece[0] !== color) {
        return;
      }

      // get list of possible moves for this square
      var moves = game.moves({
        square: square,
        ignore_color: true,
        cooldown_time: cd,
        verbose: true
      });

      // highlight the square they moused over
      setSquareAvailable(square);

      // highlight the possible squares for this piece
      for (var i = 0; i < moves.length; i++) {
        setSquareAvailable(moves[i].to);
      }
    };

    var onMouseoutSquare = function(square, piece) {
      removeAvailableSquares();
    };

    //------------------------------------------------------------------------------
    // Finally do something
    //------------------------------------------------------------------------------
    socket.emit("join-req", game_id);

    var game;
    var disabledSquares = {};

    var cfg = {
      draggable: true,
      position: 'start',
      onDragStart: onDragStart,
      onDrop: onDrop,
      onMouseoverSquare: onMouseoverSquare,
      onMouseoutSquare: onMouseoutSquare,
      pieceTheme: "static/libs/chessboardjs-0.3.0/img/chesspieces/wikipedia/{piece}.png"

    };

    var board = ChessBoard('board', cfg);

    // test function that makes random moves
    var makeRandomMoves = function() {
      var possibleMoves = game.moves({
        ignore_color: true,
        cooldown_time: cd
      });
      if (game.game_over() === true) {
        return;
      }
      var randomIndex = Math.floor(Math.random() * possibleMoves.length);

      socket.emit('move-req', game_id, possibleMoves[randomIndex]); // request the move
      window.setTimeout(makeRandomMoves, 500);
    };

    //window.setTimeout(makeRandomMoves, 500);

    // be nice citizens and close the socket
    $(window).on('beforeunload', function () {
      console.log("Closing socket")
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
