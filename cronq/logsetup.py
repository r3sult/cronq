import os
import logging
import logging.config

LOG_SETTINGS = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'normal': {
            'format': "[%(asctime)s] %(name)s - %(levelname)s - %(message)s",
            'datefmt': "%Y-%m-%d %H:%M:%S"
        },
    },
    'handlers': {
        'verbose': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'normal',
            'stream': 'ext://sys.stdout'
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'normal',
            'stream': 'ext://sys.stdout'
        },
        'error': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'formatter': 'normal',
            'stream': 'ext://sys.stderr'
        },
    },
    'root': {
        'level': 'NOTSET',
        'handlers': ['console', 'error']
    },
}

LOGGING_VERBOSE = bool(os.environ.get("LOGGING_VERBOSE", False))
if LOGGING_VERBOSE:
    LOG_SETTINGS['root']['handlers'].remove('console')
    LOG_SETTINGS['root']['handlers'].append('verbose')

logging.config.dictConfig(LOG_SETTINGS)
