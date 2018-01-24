from flask import Flask
from flask_socketio import SocketIO

socketio = SocketIO()

def create_app():
    app = Flask(__name__)

    # this weird local import on create seems to be necessitated by flask-socketio's lack of support of blueprints
    from web.main import main
    app.register_blueprint(main, url_prefix='/')

    from web.game import game
    app.register_blueprint(game, url_prefix='/game')

    socketio.init_app(app)

    return app
