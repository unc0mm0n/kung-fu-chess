"""
Event handler for game Blueprint, handles socket.io events connecting the server to the game implementation
"""

from flask_socketio import emit, join_room, rooms
from flask import request

from web.game import send_sync_req, send_move_req
from web.game.queue_reader import FAIL
from web import socketio

@socketio.on('move-req', namespace='/game')
def handle_game_move(game_id, move_json):
    """ ask to play a move """
    send_move_req(game_id, move_json)

@socketio.on('sync-req', namespace='/game')
def handle_sync_req(game_id):
    """ ask to be synced about the state of the game """
    join_room(game_id)

    send_sync_req(game_id)
