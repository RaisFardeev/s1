from app import app, socket

if __name__ == '__main__':
    socket.run(app=app, host='127.0.0.1', port=5000, debug=True, allow_unsafe_werkzeug=True)
