'''Module setting up a :mod:`logging` instance to report on the validation process.'''
import logging.config
import os

from ruamel.yaml import YAML

config_file_path = os.path.join(os.path.dirname(__file__), 'logger-config.yaml')

with open(config_file_path) as f:
    config = YAML().load(f)

logging.config.dictConfig(config)
logger = logging.getLogger('Validator')
