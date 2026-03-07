"""Flask application factory."""
import os
from flask import Flask
from backend.routes import api


def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'),
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    )
    app.register_blueprint(api)
    return app
