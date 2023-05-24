from flask import session
from flask_socketio import SocketIO, emit, Namespace
from .models import User
from . import db

class MyCustomAction(Namespace):
    def on_connect(self):
        print('connected')

    def on_disconnect(self):
        print('Client disconnected')

    def on_submit(self, data):
        email = session['uemail']
        number = int(data.get('number'))
        user = User.query.filter(User.email == email).first()
        new_b = user.balance + number
        db.session.query(User).filter(User.id == user.id). \
            update(dict(balance=new_b))
        db.session.commit()
        emit('recv', {'balance': new_b})


class MyWebSocket(SocketIO):
    def __init__(self, app):
        super().__init__(app)
        self.on_namespace(MyCustomAction())