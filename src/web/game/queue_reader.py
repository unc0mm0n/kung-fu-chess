"""
queue_reader.py

Module which handles reading a redis queue for game moves
and emitting them to room based game_id
"""
import json

import redis

FAIL = 'fail'
SUCCESS = 'success'

def poll_game_cnfs(db, game_cnfs_queue, socketio):
    """ Poll a given moves queue in redis object for new moves, emitting them to players and updating relevant parts in game store."""
    while True:
        _, cnf = db.blpop(game_cnfs_queue)
        print(cnf)
        game_id, cmd, data = json.loads(cnf)
        if cmd == "sync-cnf":
            socketio.emit('sync-cnf',
                    data(store_key),
                    room=game_id,
                    namespace="/game")
        elif cmd == "move-cnf":
            player_id, move = data
            if move is None:
                socketio.emit('move-cnf',
                {'result': FAIL, 'reason': 'illegal move'},
                room=player_id,
                namespace="/game")
            else:
                socketio.emit('move-cnf',
                {'result': SUCCESS, 'move': move},
                 room=game_id,
                 namespace="/game")


