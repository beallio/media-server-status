import flask


app = flask.Flask(__name__)
import views
import assets

# handler = logging.StreamHandler()
#handler.setLevel(logging.DEBUG)
#handler.setFormatter(
#    logging.Formatter('[%(levelname)s] %(asctime)s\n\tModule: %(module)s\n\tFunction: %(funcName)s \n\t%(message)s'))
#app.logger.addHandler(handler)
#app.logger.propagate = False


