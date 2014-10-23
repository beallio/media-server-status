"""
APACHE MOD_WSGI Load script
Some of the variables in this file may need to be adjusted depending on
server setup and/or location of virtual environment and application
"""
import sys
import os

PROJECT_DIR = '/var/www/status'  # change to the root of your app
# 'venv/bin' is the location of the project's virtual environment
VIRTUAL_ENV_DIR = 'venv/bin'
PACKAGES = 'lib/python2.7/site-packages'

activate_this = os.path.join(PROJECT_DIR, VIRTUAL_ENV_DIR, 'activate_this.py')
execfile(activate_this, dict(__file__=activate_this))
sys.path.append(PROJECT_DIR)
sys.path.append(os.path.join(PROJECT_DIR, VIRTUAL_ENV_DIR, PACKAGES))

