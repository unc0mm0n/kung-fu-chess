"""
game_manager.py

A manager whose job is to manage multiple game objects.
This barebone object is created with the idea of scalability,
allowing for example to completely replace the game module or
putting in a messaging/multi-processing layer.
"""

from kfchess.game import KungFuChess, EMPTY


class Manager():
    def __init__(self, default_cd=None):
        self._games = {}
        self._cd    = default_cd

    def __contains__(self, item):
        return item in self._games

    def create_game(self, id, cd, nfen=None):
        if id in self._games:
            raise ManagerIdError("id {} is in use".format(id))
        self._games[id] = KungFuChess.FromNfen(cd, nfen)

    def move_game(self, id, move):
        """ move is a dict with 'from' and 'to' keys representing the move, and 'promotion' if relevant. """
        if id not in self._games:
            raise ManagerIdError("id {} not found".format(id))
        if move is None:
            return None
        game = self._games[id]
        if game.winner != EMPTY:
            return None

        if 'promotion' in move:
            res = game.move(move['from'], move['to'], promote=move['promotion'])
        else:
            res = game.move(move['from'], move['to'])

        return res

    def build_game_dict(self, id):
        if id not in self._games:
            raise ManagerIdError("id {} not found".format(id))
        game = self._games[id]
        res = game.to_dict()
        return res


class ManagerIdError(Exception):
    pass