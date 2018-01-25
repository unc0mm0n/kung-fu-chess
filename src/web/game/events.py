"""
Event handler for game Blueprint, handles socket.io events connecting the server to the game implementation
"""

from web import socketio
from flask_socketio import emit, send
from web.game import manager

SUCCESS = 'success'
FAIL    = 'fail'

@socketio.on('move-req', namespace='/game')
def handle_game_move(move_json):
    """ ask to play a move """
    move = manager.move_game(1, move_json)  #TODO: Add users layer somewhere..
    if not move:
        print("illegal move {}".format(move_json))
        emit('move-cnf', {'result': FAIL})  # send only to requester
        return
    socketio.emit('move-cnf',
                  {'result': SUCCESS, 'from': move.from_sq.san, 'to': move.to_sq.san, 'promotion': move.promote, 'time': move.time},
                  namespace="/game")

@socketio.on('sync-req', namespace='/game')
def handle_sync_req(req_json):
    """ ask to be synced about the state of the game """
    # TODO: verify users, join rooms, etc.
    if 'id' not in req_json:
        emit('sync-cnf', {'result': FAIL, 'reason': 'missing id.'})
        return
    try:
        id = int(req_json['id'])
    except ValueError:
        emit('sync-cnf', {'result': FAIL, 'reason': 'badly formatted id.'})
        return

    if id not in manager:  # TODO: more recoveries here (maybe game should be loaded from db)
        emit('sync-cnf', {'result': FAIL, 'reason': 'Unknown game id.'})
        return

    emit('sync-cnf', {'result': SUCCESS, 'board': manager.build_game_dict(id)})
    return


@socketio.on('connect')
def handle_connect():
    print('Connect')

@socketio.on('disconnect')
def handle_disconnect():
    print('Disconnect')



