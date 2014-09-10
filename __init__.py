#!flask/bin/python
from app import app

if __name__ == '__main__':
    app.config.update(DEBUG=True, TESTING=True)
    app.run()