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
        self._ctrl_in  = in_queue
        self._games_in  = "{}:games".format(in_queue)

    def run(self):
        """ an event loop, reading for messages on in_queue and responding on out_queue """
        done = False
        db = self._db
        in_q = self._ctrl_in
        game_loop_p = self.run_games_loop(self._games_in)
        print("[{}] Reading queue {}".format(multiprocessing.current_process().name, in_q))
        while not done:
            _, out = db.blpop(in_q)
            try:
                cmd, data = json.loads(out)
            except Exception as ex:
                print(_, out)
                print(ex)
                self._db.rpush(self._out, ["error-ind", out, repr(ex)])
                cmd = None
            if cmd == "game-req":
                try:
                    game_key = self._game_key_from_id(data["game_id"])
                    board = kfc.create_game_from_nfen(db = self._db,
                                                      cd = data["cd"],
                                                      store_key=game_key,
                                                      nfen = data.get("nfen", None),
                                                      exp=data.get("exp", None))

                    self.manage_game(game)
                    self._db.rpush(self._out, ["game-cnf", {"in_queue": self._games_in,
                                                            "store_key": game_key}])
                except KeyError as ex:
                    self._db.rpush(self._out, ["error-ind", out, repr(ex)])
            if cmd == "exit-req":
                print("exit-req received")
                
                # Push from the left to prevent farther events processing
                self._db.lpush(self._games_in, json.dumps([0, "exit-req", None]))
                game_loop_p.join()
                cnf = prepare_exit_cnf()
                print(cnf)
                self._db.rpush(self._out, cnf)
                self._db.expire(self._out, 3600)
                done = True

    def run_games_loop(self, in_queue, out_queue=None):
        """ Start process responsible for reading game related requests and executing them 

        If out_queue is not given, the default out_queue will be used.
        Note that in_queues must be unique per game loop, and different from the manager's own in_queue"""
        def poll_in_queue(db, in_q, out_q):
            """ poll incoming queue for commands """

            done = False
            print("[{}] Reading queue {}".format(multiprocessing.current_process().name, in_q))
            while not done:
                _, out = db.blpop(in_q)
                game_id, cmd, data = json.loads(out)

                if cmd == "exit-req":
                    db.rpush(out_q, prepare_exit_cnf())
                    db.expire(out_q, 3600)
                    done = True
                else:
                    game_store = self._gam_key_from_id(game_id)
                    if not self._db.exists(game_store):
                        cmd.rpush(out_q, ["error-ind", {"reason": "invalid game id"}])
                        return
                    if cmd == "move-req":
                        res = None
                        try:
                            res = kfc.move(db, game_store, move['from'], move['to'], move.get('promote'))
                        except KeyError:
                            print("Invalid move!")
                        db.rpush(out_q, prepare_move_cnf(res, game_id))
                        db.expire(out_q, 3600)
        """ poll_in_queue done """
        if not out_queue:
            out_queue = self._out
        p = multiprocessing.Process(target=poll_in_queue, args=(self._db, in_queue, out_queue),
                                    name="worker:{}".format(1))

        p.daemon = True
        p.start()

        return p

    def _game_key_from_id(self, game_id):
        return "{}:games:{}".format(self._key_base, game_id)

    @property
    def games_queue(self):
        return self._games_in


def run_game_manager(db, in_q, out_q):
    game_manager = RedisGamesManager(db, in_q, out_q)
    game_manager.run()

def prepare_move_cnf(move, game_id, player_id):
    """ Prepare json for a move command response. """
    if move is not None:
        move =  {
                "from":    move.from_sq.san,
                "to":      move.to_sq.san,
                "promote": move.promote,
                "time":    move.time
                }
    return json.dumps([game_id, 'move-cnf', move])

def prepare_exit_cnf():
    return json.dumps(['exit-cnf', multiprocessing.current_process().name])

if __name__ == "__main__":
    import sys
    _, in_q, out_q, host, port = sys.argv

    db = redis.StrictRedis(host=host, port=port)
    run_game_manager(db, in_q, out_q)
