import os
from datetime import timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_session import Session
from flask_socketio import SocketIO
from comments import MyWebSocket

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'database.db')
bcrypt = Bcrypt()
#
app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = '2e343t54ytgfe3r54oigth'
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(seconds=3600*24*30)

db = SQLAlchemy(app)
Session(app)
MyWebSocket(app)

# database creation
with app.app_context():
    db.create_all()