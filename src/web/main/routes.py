import flask

from web.main import main
from web.game import manager

@main.route('/')
def index():
    return flask.render_template("main/main_page.html", games = manager.games)