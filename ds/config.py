from os import getenv

# Set the allowed domain origin, if unset all the domains are allowed
ORIGINS = (getenv("DS_ORIGINS") or "*").split(",")

# Boosts the volume before transcribing, it may enhance or worsen the transcription
BOOST_VOLUME = (getenv("DS_BOOST_VOLUME") or "false") == "true"

# Enables Speex noise cancellation
ENABLE_NOISE_REDUCTION = (getenv("DS_ENABLE_NOISE_REDUCTION") or "false") == "true"

# Enable saving the last received audio for debugging purposes
ENABLE_AUDIO_DEBUG = (getenv("DS_ENABLE_AUDIO_DEBUG") or "false") == "true"