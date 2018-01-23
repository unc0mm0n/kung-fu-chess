from flask import Blueprint

game = Blueprint('game', __name__, static_folder='static')

from . import routes, events