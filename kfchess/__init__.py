from flask import Flask
from kfchess.game import game

app = Flask(__name__)
app.register_blueprint(game, url_prefix='/game')

import kfchess.views
