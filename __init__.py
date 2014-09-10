#!/bin/python
from app import app

if __name__ == '__main__':
    # app.config.update(DEBUG=True)
    #app.run()
    app.config.update()
    app.run(host='0.0.0.0')