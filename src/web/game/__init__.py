from flask import Blueprint
from . import game_manager

game = Blueprint('game', __name__, static_folder='static')
manager = game_manager.Manager()

from . import routes, events