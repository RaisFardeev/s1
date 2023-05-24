import os
from datetime import timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_session import Session
from dotenv import load_dotenv
from flask_mail import Mail


load_dotenv()
github_id = os.getenv("GITHUB_ID")
github_secret = os.getenv("GITHUB_SECRET")
vk_id = os.getenv("VK_ID")
vk_secret = os.getenv("VK_SECRET")
gmail_address = os.getenv("GMAIL_ADDRESS")
gmail_password = os.getenv("GMAIL_PASSWORD")

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'database.db')
bcrypt = Bcrypt()
#
app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = '2e343t54ytgfe3r54oigth'
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'app/static/uploads'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(seconds=3600 * 24 * 30)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Адрес вашего SMTP-сервера
app.config['MAIL_PORT'] = 465  # 587 Порт SMTP-сервера
app.config['MAIL_USE_SSL'] = True
#app.config['MAIL_USE_TLS'] = True  # Использовать TLS для защиты соединения
app.config['MAIL_USERNAME'] = gmail_address  # Ваш адрес электронной почты
app.config['MAIL_DEFAULT_SENDER'] = gmail_address
app.config['MAIL_PASSWORD'] = gmail_password  # Ваш пароль от электронной почты
db = SQLAlchemy(app)
Session(app)
mail = Mail(app)
from .ws import MyWebSocket
socket = MyWebSocket(app)
from . import routes, models

# database creation
with app.app_context():
    db.create_all()
from .utils import fill_database

fill_database(app, db)
