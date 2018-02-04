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
        print("[{}] Reading queue {}".format(multiprocessing.current_process().name, in_q))
        while not done:
            _, out = db.blpop(in_q)
            try:
                cmd, data = json.loads(out)
            except Exception as ex:
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
                                                            "store_key": game_key}]
                except KeyError as ex:
                    self._db.rpush(self._out, ["error-ind", out, repr(ex)])
            if cmd == "exit-req":
                print("exit-req received")
                for _, q in self._games:
                    # Push from the left to prevent farther events processing
                    self._db.lpush(q, "exit-req")
                self._db.rpush(self._out, "exit-cnf")
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
                gid, cmd, data = json.loads(out)
                gid_queue = self._game_key_from_id(gid)
                if not self._db.exists(gid_queue):
                    cmd.rpush(out_q, ["error-ind", {"reason": "invalid game id"}])
                    return
                if cmd == "move-req":
                    res = None
                    try:
                        player_id, move = data
                        if _pids[game[move['from']].color] == player_id:
                            res = kfc.move(db, gid_queue, move['from'], move['to'], move.get('promote'))
                    except (KeyError, TypeError, AttributeError, ValueError):
                        pass
                    db.rpush(out_q, prepare_move_cnf(res, game_id, player_id))
                    db.expire(out_q, 3600)
                if cmd == "exit-req":
                    db.rpush(out_q, prepare_exit_cnf(game_id))
                    db.expire(out_q, 3600)
                    done = True
        """ poll_in_queue done """
        p = multiprocessing.Process(target=poll_in_queue, args=(self._db, in_queue, out_queue),
                                    name="worker:{}".format(1))

        p.daemon = True
        self._games.append((p, in_queue))
        p.start()

    def _game_key_from_id(self, game_id):
        return "{}:games:{}".format(self._key_base, game_id)


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
    return json.dumps([game_id, 'move-cnf', [player_id, move]])

def prepare_exit_cnf(game_id):
    return json.dumps([game_id, 'exit-cnf', None])

if __name__ == "__main__":
    import sys
    _, in_q, out_q, host, port = sys.argv

    db = redis.StrictRedis(host=host, port=port)
    run_game_manager(db, in_q, out_q)
