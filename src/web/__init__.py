import os

import redis
import eventlet
eventlet.monkey_patch()

from flask import Flask

from flask_socketio import SocketIO
from flask_login import LoginManager
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt

from web import defaultconfig

socketio = SocketIO()
login_manager = LoginManager()
mysql = MySQL()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__)
    #print(os.path.dirname(__file__))
    app.config.from_object("web.defaultconfig")
    if "KFCHESS_CONFIG" in os.environ:
        app.config.from_envvar("KFCHESS_CONFIG")
        print("Using config at {}".format(os.environ["KFCHESS_CONFIG"]))
    else:
        print("KFCHESS_CONFIG envvar is not present, using default config")

    app.redis = redis.StrictRedis(host=app.config["REDIS_HOSTNAME"],
                                  port=app.config["REDIS_PORT"])

    socketio.init_app(app)
    login_manager.init_app(app)
    mysql.init_app(app)
    bcrypt.init_app(app)

    # this weird local import on create seems to be necessitated by flask-socketio's lack of support of blueprints
    from web.main import main, user
    app.register_blueprint(main, url_prefix='/')

    from web.game import game_bp, init_game
    app.register_blueprint(game_bp, url_prefix='/game')
    app.register_blueprint(game_bp, url_prefix='/games')
    init_game(app, socketio)


    return app
