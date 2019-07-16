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
    def __init__(self, redis_db, in_queue, out_queue):
        """ initialize a games manager.

        This object runs new kfchess games in processes, relaying messages to them through redis.
        By default all responses from the manager go out to a single queue, but a different queue
        per process (game) can also be submitted. """
        self._db  = redis_db
        self._key_base = "manager:{}".format(uuid4())
        self._out = out_queue
        self._in  = in_queue

    def run(self):
        """ an event loop, reading for messages on in_queue and responding on out_queue """
        done = False
        db = self._db
        in_q = self._in
        out_q = self._out
        print("[{}] Reading queue {}".format(multiprocessing.current_process().name, in_q))
        while not done:
            _, out = db.blpop(in_q)
            try:
                game_id, cmd, data = json.loads(out)
                game_key = self._game_key_from_id(game_id)
                if cmd == "game-req":
                    if not db.exists(game_key):
                        board = kfc.create_game_from_nfen(db = self._db,
                                                      cd = data["cd"],
                                                      store_key=game_key,
                                                      nfen = data.get("nfen", None),
                                                      exp=data.get("exp", None))

                    self._db.rpush(self._out, json.dumps([game_id, "game-cnf", {"in_queue": in_q,
                                                                       "store_key": game_key}]))
                elif cmd == "join-req":
                    if not db.exists(game_key):
                        self._db.rpush(self._out, json.dumps([game_id, "join-cnf", None])
                    else:
                        #todo: see if color is open, if yes return color otherwise return observer.
                        self._db.rpush(self._out, json.dumps([game_id, "join-cnf", {"color": "observer"}),
                elif cmd == "exit-req":
                    print("exit-req received")

                    cnf = prepare_exit_cnf()
                    self._db.rpush(self._out, cnf)
                    self._db.expire(self._out, 3600)
                    done = True
                elif cmd == "move-req":
                    res = None
                    try:
                        res = kfc.move(db, game_key, data['from'], data['to'], data.get('promote'))
                    except KeyError:
                        print("Invalid move!")
                    db.rpush(out_q, prepare_move_cnf(res, game_id))
                    db.expire(out_q, 3600)
                elif cmd == "sync-req":
                    db.rpush(out_q, prepare_sync_cnf(game_id, db, self._game_key_from_id(game_id)))
                    db.expire(out_q, 3600)
                else:
                    print("Unknown command {}".format(cmd))
                    self._db.rpush(self._out, prepare_error_ind(command=cmd, reason="Unknown command"))
            except Exception as ex:
                print(_, out)
                traceback.print_exc()
                self._db.rpush(self._out, prepare_error_ind(reason="exception", exc=ex))
                cmd = None

    def _game_key_from_id(self, game_id):
        return "{}:games:{}".format(self._key_base, game_id)


def run_game_manager(db, in_q, out_q):
    game_manager = RedisGamesManager(db, in_q, out_q)
    game_manager.run()

def prepare_move_cnf(move, game_id):
    """ Prepare json for a move command response. """
    if move is not None:
        move =  {
                "from":    move.from_sq.san,
                "to":      move.to_sq.san,
                "promote": move.promote,
                "time":    move.time
                }
    return json.dumps([game_id, 'move-cnf', move])

def prepare_sync_cnf(game_id, db, store_key):
    """ Prepare json for a sync command response. """
    try:
        return json.dumps([game_id, 'sync-cnf', kfc.to_dict(db, store_key)])
    except ValueError:
        return prepare_error_ind(game_id, reason="Invalid game id")

def prepare_exit_cnf():
    return json.dumps(['exit-cnf', multiprocessing.current_process().name])


def prepare_error_ind(game_id=-1, **kwargs):
    """ prepare an error indication. game_id is -1 if error is not relevant to specific game """
    return json.dumps([game_id, "error-ind", {k: str(v) for k,v in kwargs.items()}])

if __name__ == "__main__":
    import sys
    _, in_q, out_q, host, port = sys.argv

    db = redis.StrictRedis(host=host, port=port)
    run_game_manager(db, in_q, out_q)
