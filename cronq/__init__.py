# -*- coding: utf-8 -*-
__version__ = '0.26.1'

# import here
import cronq.logsetup


def make_application():
    from flask import Flask
    from cronq.config import Config
    import cronq.web
    import os

    flask_app = Flask(__name__,
                      static_url_path='/static')

    if Config.BUGSNAG_API_KEY:
        import bugsnag
        from bugsnag.flask import handle_exceptions
        bugsnag.configure(api_key=Config.BUGSNAG_API_KEY)
        handle_exceptions(flask_app)
    elif Config.SENTRY_DSN:
        from raven.contrib.flask import Sentry
        sentry = Sentry()
        sentry.init_app(flask_app, dsn=Config.SENTRY_DSN)

    flask_app.config.from_object('cronq.config.Config')
    flask_app.register_blueprint(cronq.web.blueprint_http)
    cronq.web.blueprint_http.config = flask_app.config

    return flask_app
