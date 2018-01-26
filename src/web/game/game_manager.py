"""
game_manager.py

A manager whose job is to manage multiple game objects.
This barebone object is created with the idea of scalability,
allowing for example to completely replace the game module or
putting in a messaging/multi-processing layer.
"""

from kfchess.game import KungFuChess, EMPTY, WHITE, BLACK


class Manager():
    def __init__(self, default_cd=None):
        self._games = {}
        self._cd    = default_cd

    def __contains__(self, item):
        return item in self._games

    def create_game(self, id, cd, nfen=None):
        if id in self._games:
            raise ManagerIdError("id {} is in use".format(id))
        self._games[id] = (KungFuChess.FromNfen(cd, nfen), { WHITE: None, BLACK: None})

    def move_game(self, id, move, player_id):
        """ move is a dict with 'from' and 'to' keys representing the move, and 'promotion' if relevant. """
        if id not in self._games:
            raise ManagerIdError("id {} not found".format(id))
        if move is None:
            return None
        game, meta = self._games[id]
        if game.winner != EMPTY or  player_id != meta[move['color']]:
            return None

        if 'promotion' in move:
            res = game.move(move['from'], move['to'], promote=move['promotion'])
        else:
            res = game.move(move['from'], move['to'])

        return res

    def set_player(self, id, color, player_id):
        """ move is a dict with 'from' and 'to' keys representing the move, and 'promotion' if relevant. """
        if id not in self._games:
            raise ManagerIdError("id {} not found".format(id))

        _, meta = self._games[id]
        if meta[color] != None:
            raise ManagerMetaError("set player called on color already in use")

        meta[color] = player_id

    def get_meta(self, id):
        if id not in self._games:
            return None
        _, meta = self._games[id]
        return meta

    def game_over(self, game_id):
        game, _ = self._games[game_id]
        return game.is_over

    def delete(self, game_id):
        del self._games[game_id]

    def build_game_dict(self, id):
        if id not in self._games:
            raise ManagerIdError("id {} not found".format(id))
        game, meta = self._games[id]
        res = game.to_dict()
        return res

    @property
    def games(self):
        """ Keys of all existing game ids """
        return self._games.keys()


class ManagerIdError(Exception):
    pass

class ManagerMetaError(Exception):
    pass