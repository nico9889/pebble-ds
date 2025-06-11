from threading import Lock

from flask import Flask
from flask_cors import CORS

from speex import SpeexDecoder
from speex_noise_cpp import AudioProcessor
from vosk import Model, KaldiRecognizer

from ds.config import ORIGINS, ENABLE_NOISE_REDUCTION

# Initializing Speex Audio Processor
auto_gain = 6000
noise_suppression = -30
audio_processor = AudioProcessor(auto_gain, noise_suppression)


# Flask initialization
app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": ORIGINS}})

# Speex initialization
decoder = SpeexDecoder(1)

# Vosk initialization
model = Model(lang="it")
recognizer = KaldiRecognizer(model, 16000)
recognizer.SetWords(True)
recognizer.SetPartialWords(True)

# Initializing recognizer lock as we don't want it to be shared between users
rec_lock = Lock()

# Everything is initialized, registering routes
from ds.api import routes

app.register_blueprint(routes)
