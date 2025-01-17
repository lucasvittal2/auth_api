import logging
from typing import Dict

import yaml


def read_yaml(path: str) -> dict:
    with open(path) as file:
        try:
            data = yaml.safe_load(file)
            return data
        except Exception as err:
            logging.error(f"Error reading YAML file: {err}")
            raise err


def delta_parse(delta_str: str) -> Dict[str, int]:
    days, hours, minutes, seconds = map(int, delta_str.split(":"))
    return {"days": days, "hours": hours, "minutes": minutes, "seconds": seconds}
