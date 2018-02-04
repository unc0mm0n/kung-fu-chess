"""
Event handler for game Blueprint, handles socket.io events connecting the server to the game implementation
"""

from flask_socketio import emit, join_room, rooms
from flask import request

from web.game import get_store_key, get_game_redis, push_req
from web.game.queue_reader import FAIL
from web import socketio

@socketio.on('move-req', namespace='/game')
def handle_game_move(game_id, move_json):
    """ ask to play a move """
    game_store = get_game_store(game_id)
    if game_id not in rooms() or not get_game_redis().exists(game_store):
        # room id mismatch
        emit('move-cnf', {'result': FAIL, 'reason': 'invalid game_id'})  # send only to requester
        return

    push_req('move-req', move_json, game_id)


@socketio.on('sync-req', namespace='/game')
def handle_sync_req(game_id):
    """ ask to be synced about the state of the game """
    game_store = get_store_key(game_id)
    if not get_game_redis().exists(game_store):  # TODO: more recoveries here (maybe game should be loaded from sql db)
        emit('sync-cnf', {'result': FAIL, 'reason': 'Unknown game id {}.'.format(game_id)})
        return

    join_room(game_id)

    push_req("sync-req", None, game_id);
