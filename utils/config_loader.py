import os

import yaml

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")


def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)


config = load_config()
