import os

DEBUG = True
SECRET_KEY = os.environ.get('SALTSTATS_DEV_SECRET_KEY')
SQLALCHEMY_DATABASE_URI = os.environ.get('SALTSTATS_DEV_DATABASE_URI')
LDAP_SERVER = 'your.server.address'
