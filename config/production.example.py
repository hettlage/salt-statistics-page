import os

DEBUG = False
SECRET_KEY = os.environ.get('SALTSTATS_SECRET_KEY')
DATABASE_URI = os.environ.get('SALTSTATS_DATABASE_URI')
