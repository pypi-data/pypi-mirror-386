import os

from mtcli.conf import config

SYMBOL = os.getenv("SYMBOL", config["DEFAULT"].get("symbol", fallback="WIN$N"))
BARS = int(os.getenv("BARS", config["DEFAULT"].getint("bars", fallback=566)))
BLOCK = int(os.getenv("BLOCK", config["DEFAULT"].getint("block", fallback=100)))
BY = os.getenv("BY", config["DEFAULT"].get("by", fallback="time"))
DIGITOS = int(os.getenv("DIGITOS", config["DEFAULT"].getint("digitos", fallback=0)))
