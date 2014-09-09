#!flask/bin/python

from app import app

app.config.update(DEBUG=True, TESTING=True)
app.run()