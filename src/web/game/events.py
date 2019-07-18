"""
Event handler for game Blueprint, handles socket.io events connecting the server to the game implementation
"""

from flask_socketio import emit, join_room, rooms
from flask import request

from web.game import push_req
from web.game.queue_reader import FAIL
from web import socketio

#TODO: Numbers..
def send_sync_req(game_id, player_id):
    push_req("sync-req", None, game_id, player_id)

def send_move_req(game_id, player_id, move):
    push_req("move-req", move, game_id, player_id)

def send_new_game_req(game_id, player_id, cd=10000):
    push_req("game-req", {"cd": cd}, game_id, player_id)

@socketio.on('move-req', namespace='/game')
def handle_game_move(game_id, move_json):
    """ ask to play a move """
    send_move_req(game_id, request.sid, move_json)
    emit("ind", "km")

@socketio.on('join-req', namespace='/game')
def handle_join_req(game_id):
    """ ask to play a move """
    join_room(game_id)
    print(rooms())
    print("joined {}, {}".format(game_id, request.sid))
    send_new_game_req(game_id, request.sid)
    send_sync_req(game_id, request.sid)
    emit("ind", "kj")

@socketio.on('sync-req', namespace='/game')
def handle_sync_req(game_id):
    """ ask to be synced about the state of the game """
    send_sync_req(game_id, request.sid)
    emit("ind", "ks")
