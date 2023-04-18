from flask import session
from flask_socketio import SocketIO, emit, Namespace, join_room, leave_room
from datetime import datetime

history = dict()


class MyCustomAction(Namespace):
    def on_connect(self, data):
        ad = data.get('ad')
        join_room(ad)
        history_ = list(history[ad][i] for i in range(len(history[ad])))
        emit('history', history_)
        print('connected')

    def on_disconnect(self):
        print('Client disconnected')

    def on_my_event(self, data):
        ad = data.get('ad')
        msg = data.get('msg')
        if not history[ad]:
            history[ad].append(msg)
        emit('recv', {'msg':data.get('msg'), 'user':session['uemail']}, broadcast=True, to=ad)


class MyWebSocket(SocketIO):
    def __init__(self, app):
        super().__init__(app)
        self.on_namespace(MyCustomAction())