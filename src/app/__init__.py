import logging
import os
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask.ext.bootstrap import Bootstrap
from flask.ext.login import LoginManager
from flask.ext.sqlalchemy import SQLAlchemy

logger = None

bootstrap = Bootstrap()
db = SQLAlchemy()

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'


def create_app(config_name):
    app = Flask(__name__)
    cfg = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'config', config_name + '.py')
    app.config.from_pyfile(cfg)

    # set up logging
    if not app.debug:
        file_handler = RotatingFileHandler(app.config['LOGFILE'], maxBytes=100000, backupCount=10)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.DEBUG)

    global logger
    logger = app.logger

    bootstrap.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    return app
