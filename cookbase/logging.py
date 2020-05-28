import inspect
import logging.config
import os

from ruamel.yaml import YAML


def config_logger():
    config_file_path = os.path.join(os.path.dirname(__file__), "logger-config.yaml")

    with open(config_file_path) as f:
        config = YAML().load(f)

    logging.config.dictConfig(config)

    #     formatter = logging.Formatter(
    #         fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
    #
    #     handler = logging.StreamHandler()
    #     handler.setFormatter(formatter)
    #
    #     global logger
    #     logger = logging.getLogger(logger_name)
    #     logger.setLevel(logging.DEBUG)
    #     logger.addHandler(handler)

    global logger
    logger = logging.getLogger("validation")


# =======================================================================================
# Hack to ensure correct logging from sphinx-build
# =======================================================================================
stack = inspect.stack()
path_splits = stack[len(stack) - 1].filename.rsplit("/", 1)
main_filename = path_splits[len(path_splits) - 1]
logger = None

if main_filename != "sphinx-build":
    config_logger()
# =======================================================================================
