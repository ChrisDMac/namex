
import os

import flask
import flask_sqlalchemy

import config
import synonyms.endpoints
import synonyms.models


__all__ = ['create_application']


# Create the Flask application
def create_application(run_mode=os.getenv('FLASK_ENV', 'production')):
    # Create application
    application = flask.Flask(__name__)
    application.config.from_object(config.CONFIGURATION[run_mode])
    endpoints.api.init_app(application)

    # Create the connection to the database.
    models.db.init_app(application)

    return application
