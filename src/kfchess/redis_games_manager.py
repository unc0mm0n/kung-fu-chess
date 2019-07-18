""" redis_game_manager.py

Manage a stream of commands for games sitting in redis. Reading
requests from input queue and sending responses to output queue.

Future:
    - Manage workers handling games, possibly with separate queues
    - Move to real loggig library (project-wide)
"""
import threading
import multiprocessing
import json
import traceback
from uuid import uuid4

import redis

import kfchess.game as kfc

class RedisGamesManager():
    """ Manage games using redis queue for incoming and outgoing messages """
    def __init__(self, redis_db, in_queue, out_queue, key_base_suffix=None):
        """ initialize a games manager.

        This object runs new kfchess games in processes, relaying messages to them through redis.
        By default all respodatao a single queue, but a different queue
        per process (game) can also be submitted. """
        if not key_base_suffix:
            key_base_suffix = str(uuid4())
        self._db  = redis_db
        self._key_base = "manager:{}".format(key_base_suffix)
        self._out = out_queue
        self._in  = in_queue

    def run(self):
        """ an event loop, reading for messages on in_queue and responding on out_queue """
        done = False
        db = self._db
        in_q = self._in
        out_q = self._out
        while not done:
            _, out = db.blpop(in_q)
            try:
                game_id, player_id, cmd, data = json.loads(out)
                game_key = self.game_key_from_id(game_id)
                print("[{}, {}] responding to {}, data={}".format(game_id, player_id, cmd, data))
                if cmd == "game-req":
                    if not db.exists(game_key):
                        board = kfc.create_game_from_nfen(db = self._db,
                                                      cd = data["cd"],
                                                      store_key=game_key,
                                                      nfen = data.get("nfen", None),
                                                      exp=data.get("exp", 3600))
                        board.set_white(player_id)
                        self._db.rpush(self._out, json.dumps([game_id, player_id, "game-cnf", {"state": board.state,
                                                                                               "store_key": game_key}]))
                    else:
                        self._db.rpush(self._out, json.dumps([game_id, player_id, "game-cnf", None]))
                elif cmd == "join-req":
                    if not db.exists(game_key):
                        self._db.rpush(self._out, json.dumps([game_id, player_id, "join-cnf", None]))
                    else:
                        board = kfc.get_board(db, game_key)
                        if board.black is None:
                            board.set_black(player_id)
                        self._db.rpush(self._out, json.dumps([game_id, player_id, "join-cnf", {"state": board.state,
                                                                       "store_key": game_key}]))
                elif cmd == "exit-req":
                    print("exit-req received")

                    cnf = prepare_exit_cnf()
                    self._db.rpush(self._out, cnf)
                    done = True
                elif cmd == "move-req":
                    res = None
                    try:
                        res = kfc.move(player_id, db, game_key, data['from'], data['to'], data.get('promote'))
                    except KeyError:
                        print("Invalid move!")
                    db.rpush(out_q, prepare_move_cnf(res, game_id, player_id))
                elif cmd == "sync-req":
                    if not db.exists(game_key):
                        db.rpush(out_q, json.dumps([game_id, player_id, "sync-cnf", None]))
                    else:
                        db.rpush(out_q, prepare_sync_cnf(game_id, player_id, db, game_key))
                else:
                    print("Unknown command {}".format(cmd))
                    self._db.rpush(self._out, prepare_error_ind(command=cmd, reason="Unknown command"))
                db.expire(out_q, 3600)
            except Exception as ex:
                print(_, out)
                traceback.print_exc()
                self._db.rpush(self._out, prepare_error_ind(reason="exception", exc=ex))
                cmd = None

    def game_key_from_id(self, game_id):
        return "{}:games:{}".format(self._key_base, game_id)


def run_game_manager(db, in_q, out_q):
    game_manager = RedisGamesManager(db, in_q, out_q)
    game_manager.run()

def prepare_move_cnf(move_state, game_id, player_id):
    """ Prepare json for a move command response. """
    data = None
    if move_state != None:
        move, state = move_state
        move =  {
                "from":    move.from_sq.san,
                "to":      move.to_sq.san,
                "promote": move.promote,
                "time":    move.time
                }
        data = {"state": state, "move": move}
    return json.dumps([game_id, player_id, 'move-cnf', data])

def prepare_sync_cnf(game_id, player_id, db, store_key):
    """ Prepare json for a sync command response. """
    try:
        board = kfc.get_board(db, store_key)
        res = json.dumps([game_id, player_id, 'sync-cnf', 
            {'board': kfc.to_dict(db, store_key),
            'white': board.white,
            'black': board.black}])
        return res
    except ValueError as e:
        return prepare_error_ind(game_id, player_id, reason=repr(e))

def prepare_exit_cnf():
    return json.dumps(['exit-cnf', multiprocessing.current_process().name])


def prepare_error_ind(game_id=-1, player_id=-1, **kwargs):
    """ prepare an error indication. game_id is -1 if error is not relevant to specific game """
    return json.dumps([game_id, player_id, "error-ind", {k: str(v) for k,v in kwargs.items()}])

if __name__ == "__main__":
    import sys
    _, in_q, out_q, host, port = sys.argv

    db = redis.StrictRedis(host=host, port=port)
    run_game_manager(db, in_q, out_q)
