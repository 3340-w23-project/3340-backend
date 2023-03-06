from backend import app

@app.route('/ping')
@app.route('/')
def ping():
    return '<h1>pong</h1>'
