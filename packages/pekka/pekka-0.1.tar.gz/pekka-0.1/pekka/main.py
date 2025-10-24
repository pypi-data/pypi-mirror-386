from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

APP=None

def hello():
    print("Hello, World!")

def app(slack_bot):
    app = App(token=slack_bot)
    APP=app
    return APP

def add_command(app,command,text):
    @app.command(command)
    def handle_command(ack, respond):
        ack()
        respond(text)

def run_app(app,slack_app):
    handler = SocketModeHandler(app, slack_app)
    handler.start()