import configparser
from pathlib import Path

def default_format():
    config = configparser.ConfigParser()
    config.read(Path(__file__).with_name("config.ini"))
    return config["export"]["format"]
