#!/usr/bin/env python


if __name__ == '__main__':
    from serverstatus import app

    app.config.update(DEBUG=True, TESTING=True)
    app.config.update()
    app.run(host='0.0.0.0')