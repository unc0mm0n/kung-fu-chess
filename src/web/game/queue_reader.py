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
    """ Poll a given response queue in redis object for new responses,
    emitting them to players as necessary."""
    while True:
        _, cnf = db.blpop(game_cnfs_queue)
        game_id, player_id, cmd, data = json.loads(cnf)
        if cmd == "sync-cnf":
            print('emitting sync-cnf to {}'.format(player_id))
            color = "o"
            if player_id == data["white"]:
                color = "w"
            elif player_id == data["black"]:
                color = "b"
            socketio.emit('sync-cnf',
                        {'color': color,
                        'board': data['board']},
                    room=player_id,
                    namespace="/game")
        elif cmd == "move-cnf":
            if data is None:
                print("emitting move-cnf (fail) to {}".format(player_id))
                socketio.emit('move-cnf',
                {'result': FAIL, 'reason': 'illegal move'},
                room=player_id,
                namespace="/game")
            else:
                print("emitting move-cnf (success) to {}".format(game_id))
                socketio.emit('move-cnf',
                {'result': SUCCESS, 'move': data},
                 room=game_id,
                 namespace="/game")
        elif cmd == "error-ind":
            #TODO: Add proper logging instead of total collapse
            raise Exception("Error ind received!!")


