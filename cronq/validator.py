#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import logging
import json
import jsonschema
import sys


def cronq_schema():
    return {
        "title": "cronq",
        "type": "object",
        "properties": {
            "category": {
                "type": "string"
            },
            "jobs": {
                "type": "array",
                "items": {
                    "title": "job",
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                        },
                        "schedule": {
                            "type": "string",
                            "pattern": "^R/[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}(:[0-9]{2})?/(P([0-9]+Y)?([0-9]+M)?([0-9]+D)?T?([0-9]+H)?([0-9]+M)?([0-9]+S)?|P[0-9]+W)$",  # noqa
                        },
                        "command": {
                            "type": "string",
                        },
                        "routing_key": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "name",
                        "schedule",
                        "command",
                        "routing_key",
                    ],
                },
            },
        },
        "required": [
            "category",
            "jobs",
        ],
    }


def validate(config_file):
    logger = logging.getLogger('amqp-dispatcher')
    logger.setLevel(logging.ERROR)

    config = None
    with open(config_file) as f:
        config = json.loads(f.read())

    if config is None:
        logger.error('Failed to open config file')
        return False

    jsonschema.validate(config, cronq_schema())
    return True


def main():
    parser = argparse.ArgumentParser(description='Validate cronq.config')
    parser.add_argument('--config',
                        metavar='config',
                        type=str,
                        default='cronq.config',
                        help='path to the config file')
    args = parser.parse_args()
    if not validate(args.config):
        sys.exit(1)


if __name__ == '__main__':
    main()
