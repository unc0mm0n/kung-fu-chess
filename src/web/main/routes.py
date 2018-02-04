import flask

from web.main import main

@main.route('/')
def index():
    return flask.render_template("main/main_page.html", games = [1,2,3])
