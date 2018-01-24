"""
Event handler for game Blueprint, handles socket.io events connecting the server to the game implementation
"""

from web import socketio
from kfchess.game_manager import Manager

@socketio.on('move-req', namespace='/game')
def handle_game_move(move):
    # TODO here: Legality check
    print('received move {}'.format(move))
    if not move:
        return
    socketio.emit('move-cnf',
                  {'from': move['from'], 'to': move['to'], 'promotion': move.get('promotion', 'q'), 'time': 0}, # TODO: move building will move to tester
                  namespace="/game")

@socketio.on('connect')
def handle_connect():
    print('Connect')

@socketio.on('disconnect')
def handle_disconnect():
    print('Disconnect')



