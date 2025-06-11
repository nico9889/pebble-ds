from os import getenv

ORIGINS = (getenv("DS_ORIGINS") or "*").split(",")
