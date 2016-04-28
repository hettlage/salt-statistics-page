import logging
import os
from logging.handlers import RotatingFileHandler
from flask import Flask

logger = None


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

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
