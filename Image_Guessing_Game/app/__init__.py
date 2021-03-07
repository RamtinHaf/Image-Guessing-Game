from flask import Flask, g
from config import Config
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
import sqlite3
import os
from flask_socketio import SocketIO, send, emit
from flask_argon2 import Argon2


# create and configure app
app = Flask(__name__, static_url_path='')
Bootstrap(app)
app.config.from_object(Config)
argon2 = Argon2(app)

# Initialise socket io
socketio = SocketIO(app)

# get an instance of the db
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
    db.row_factory = sqlite3.Row
    return db


# initialize db for the first time
def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


# perform generic query, not very secure yet
def query_db(query, one=False):
    db = get_db()
    cursor = db.execute(query)
    rv = cursor.fetchall()
    cursor.close()
    db.commit()
    return (rv[0] if rv else None) if one else rv


def get_userbyid(userid):
    userrow = query_db('SELECT * FROM Users WHERE id="{}";'.format(userid), one=True)
    return userrow


def get_best_players():
    userrow = query_db('SELECT username, points  FROM Users ORDER BY points DESC LIMIT 10 ;')
    return userrow

# automatically called when application is closed, and closes db connection
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# initialize db if it does not exist
if not os.path.exists(app.config['DATABASE']):
    init_db()

from app import routes

# Login manager initializing
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = '/'

from app.models import User

# Loading the user for the login_manager
@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


if __name__ == '__main__':
    socketio.run(app)