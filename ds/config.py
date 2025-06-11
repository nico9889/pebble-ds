from os import getenv

# Set the allowed domain origin, if unset all the domains are allowed
ORIGINS = (getenv("DS_ORIGINS") or "*").split(",")

# Boosts the volume before transcribing, it may enhance or worsen the transcription
BOOST_VOLUME = (getenv("DS_BOOST_VOLUME") or "false") == "true"

# FIXME: permanently disabled until a working implementation is done
ENABLE_DEEP_FILTER_NET = False and (getenv("DS_ENABLE_DEEP_FILTER_NET") or "false") == "true"

ENABLE_AUDIO_DEBUG = (getenv("DS_ENABLE_AUDIO_DEBUG") or "false") == "true"