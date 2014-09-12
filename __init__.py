#!/usr/bin/env python
from serverstatus import app

if __name__ == '__main__':
    app.config.update(DEBUG=False)
    # serverstatus.run()
    app.config.update()
    app.run(host='0.0.0.0')