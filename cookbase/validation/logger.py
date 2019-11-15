import logging.config
import os
import yaml

config_file_path = os.path.join(
    os.path.dirname(__file__),
    "logger-config.yaml")

with open(config_file_path, "r") as f:
    config = yaml.safe_load(f.read())
    logging.config.dictConfig(config)

logger = logging.getLogger("Validator")
