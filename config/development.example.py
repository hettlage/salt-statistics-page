import os

DEBUG = True
SECRET_KEY = os.environ.get('SALTSTATS_DEV_SECRET_KEY')
DATABASE_URI = os.environ.get('SALTSTATS_DEV_DATABASE_URI')
LDAP_SERVER = 'your.server.address'
