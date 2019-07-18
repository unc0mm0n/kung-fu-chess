"""
queue_reader.py

Module which handles reading a redis queue for game moves
and emitting them to room based game_id
"""
import json

import redis

FAIL = 'fail'
SUCCESS = 'success'

def test():
    print("Hello world")

def poll_game_cnfs(db, game_cnfs_queue, socketio):
    """ Poll a given response queue in redis object for new responses,
    emitting them to players as necessary."""
    while True:
        _, cnf = db.blpop(game_cnfs_queue)
        print(cnf)
        game_id, player_id, cmd, data = json.loads(cnf)
        if cmd == "sync-cnf":
            print('emitting sync-cnf to {}'.format(player_id))
            color = "o"
            if player_id == data["white"]:
                color = "w"
            elif player_id == data["black"]:
                color = "b"
            print(player_id, data["white"], color, data)
            socketio.emit('sync-cnf',
                        {'color': color,
                        'board': data['board']},
                    room=player_id,
                    namespace="/game")
        elif cmd == "move-cnf":
            print("emitting move-cnf to {}".format(game_id))
            if data is None:
                socketio.emit('move-cnf',
                {'result': FAIL, 'reason': 'illegal move'},
                room=player_id,
                namespace="/game",
                broadcast=True,
                include_self=True)
            else:
                print("Emitting move-cnf to {}".format(player_id))
                socketio.emit('move-cnf',
                {'result': SUCCESS, 'move': data},
                 room=player_id,
                 namespace="/game")
        elif cmd == "error-ind":
            #TODO: Add proper logging instead of total collapse
            raise Exception("Error ind received!!")


