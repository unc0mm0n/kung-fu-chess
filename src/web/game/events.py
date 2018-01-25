"""
Event handler for game Blueprint, handles socket.io events connecting the server to the game implementation
"""

from web import socketio
from flask_socketio import emit, join_room, rooms
from web.game import manager

SUCCESS = 'success'
FAIL    = 'fail'

@socketio.on('move-req', namespace='/game')
def handle_game_move(game_id, move_json):
    """ ask to play a move """
    if game_id not in rooms():
        # room id mismatch
        emit('move-cnf', {'result': FAIL, 'reason': 'invalid game_id'})  # send only to requester
        return

    move = manager.move_game(game_id, move_json)  #TODO: Add users layer somewhere..
    if not move:
        emit('move-cnf', {'result': FAIL, 'reason': 'illegal move'})  # send only to requester
        return
    emit('move-cnf',
         {'result': SUCCESS, 'from': move.from_sq.san, 'to': move.to_sq.san, 'promotion': move.promote, 'time': move.time},
         room=game_id,
         namespace="/game")

@socketio.on('sync-req', namespace='/game')
def handle_sync_req(game_id):
    """ ask to be synced about the state of the game """
    # TODO: verify users, join rooms, etc.
    if game_id not in manager:  # TODO: more recoveries here (maybe game should be loaded from db)
        emit('sync-cnf', {'result': FAIL, 'reason': 'Unknown game id {}.'.format(game_id)})
        return

    join_room(game_id)

    emit('sync-cnf', {'result': SUCCESS, 'board': manager.build_game_dict(game_id)})
    return