#!/usr/bin/env python
"""
Main initilizating file.  If called from command line starts WSGI debug testing server
"""


if __name__ == '__main__':
    from serverstatus import app

    app.config.update(DEBUG=True, TESTING=True)
    app.run(host='0.0.0.0')
    print 'Test server running...'