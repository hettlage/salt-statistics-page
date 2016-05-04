import os

DEBUG = True
SECRET_KEY = os.environ.get('SALTSTATS_TEST_SECRET_KEY')
DATABASE_URI = os.environ.get('SALTSTATS_TEST_DATABASE_URI')
LDAP_SERVER = 'your.server.address'
