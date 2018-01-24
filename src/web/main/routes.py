from web.main import main
import flask

@main.route('/')
def index():
    return flask.render_template("base.html")