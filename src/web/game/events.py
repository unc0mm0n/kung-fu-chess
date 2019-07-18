"""
Event handler for game Blueprint, handles socket.io events connecting the server to the game implementation
"""

from flask_socketio import emit, join_room, rooms
from flask_login import current_user
from flask import request

from web.game import push_req
from web.game.queue_reader import FAIL
from web import socketio

def send_sync_req(game_id, player_id):
    push_req("sync-req", None, game_id, player_id)

def send_join_req(game_id, player_id):
    push_req("join-req", None, game_id, player_id)

def send_move_req(game_id, player_id, move):
    push_req("move-req", move, game_id, player_id)


@socketio.on('move-req', namespace='/game')
def handle_game_move(game_id, move_json):
    """ ask to play a move """
    if current_user.is_authenticated:
        sid = current_user.get_id()
        send_move_req(game_id, sid, move_json)

@socketio.on('join-req', namespace='/game')
def handle_join_req(game_id):
    """ Ask to get updates for given game id"""
    join_room(game_id)
    sid = current_user.get_id() if current_user.is_authenticated else request.sid
    if current_user.is_authenticated:
        send_join_req(game_id, sid)
    send_sync_req(game_id, sid)

@socketio.on('sync-req', namespace='/game')
def handle_sync_req(game_id):
    """ ask to be synced about the state of the game """
    sid = current_user.get_id() if current_user.is_authenticated else request.sid
    send_sync_req(game_id, sid)

@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        join_room(current_user.get_id(), namespace="/game")
