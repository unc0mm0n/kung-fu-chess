import os
from flask import Flask
from flask_socketio import SocketIO

socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    app.config.from_object("web.defaultconfig")
    if "KFCHESS_CONFIG" in os.environ:
        app.config.from_envvar("KFCHESS_CONFIG")
        print("Using redis at: {}:{}".format(app.config["REDIS_HOSTNAME"], app.config["REDIS_PORT"]))
    else:
        print("KFCHESS_CONFIG envvar is not present, using default config")

    if not app.config["TESTING"]:
        socketio.init_app(app)
    # this weird local import on create seems to be necessitated by flask-socketio's lack of support of blueprints
    from web.main import main
    app.register_blueprint(main, url_prefix='/')

    from web.game import game_bp, init_game
    app.register_blueprint(game_bp, url_prefix='/game')
    app.register_blueprint(game_bp, url_prefix='/games')
    init_game(app, socketio)


    return app
