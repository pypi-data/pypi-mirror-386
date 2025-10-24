from flask import Flask
from flask_exts import Manager
from .file_view import file_view
from flask_exts.datastore.sqla import db


def create_app():
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev"
    init_app(app)

    with app.app_context():
        db.drop_all()
        db.create_all()

    return app


def init_app(app: Flask):
    manager = Manager()
    manager.init_app(app)
    manager.admin.add_view(file_view)
