from threading import Lock

from df import init_df
from flask import Flask
from flask_cors import CORS

from speex import SpeexDecoder
from vosk import Model, KaldiRecognizer

from ds.config import ORIGINS


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

# Initializing DeepFilterNet
filter_model, df_state, _ = init_df()  # Load default model

# Everything is initialized, registering routes
from ds.api import routes

app.register_blueprint(routes)
