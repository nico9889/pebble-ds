import wave
import audioop
from ds import decoder, recognizer, rec_lock, audio_processor
from ds.config import BOOST_VOLUME, ENABLE_NOISE_REDUCTION, ENABLE_AUDIO_DEBUG

from flask import request, Blueprint, current_app

from flask import Response
from email.mime.multipart import MIMEMultipart
from email.message import Message
import json

routes = Blueprint('routes', __name__)


@routes.route("/heartbeat")
def heartbeat():
    return "asr"


# From: https://github.com/pebble-dev/rebble-asr/blob/37302ebed464b7354accc9f4b6aa22736e12b266/asr/__init__.py#L27
def parse_chunks(stream):
    boundary = b'--' + request.headers['content-type'].split(';')[1].split('=')[1].encode(
        'utf-8').strip()  # super lazy/brittle parsing.
    this_frame = b''
    while True:
        content = stream.read(4096)
        this_frame += content
        end = this_frame.find(boundary)
        if end > -1:
            frame = this_frame[:end]
            this_frame = this_frame[end + len(boundary):]
            if frame != b'':
                try:
                    header, content = frame.split(b'\r\n\r\n', 1)
                except ValueError:
                    continue
                yield content[:-2]
        if content == b'':
            break


@routes.post("/NmspServlet/")
def asr():
    # TODO: some sort of authentication should be added here. This service is exposed to anyone on the internet and
    #     it's not good

    stream = request.stream

    # Parsing request
    chunks = list(parse_chunks(stream))[3:]  # 0 = Content Type, 1 = Header?

    # Preparing response
    # From: https://github.com/pebble-dev/rebble-asr/blob/37302ebed464b7354accc9f4b6aa22736e12b266/asr/__init__.py#L92
    # Now for some reason we also need to give back a mime/multipart message...
    parts = MIMEMultipart()
    response_part = Message()
    response_part.add_header('Content-Type', 'application/JSON; charset=utf-8')

    # Dirty way to remove initial/final button click
    if len(chunks) > 15:
        chunks = chunks[12:-3]

    # Locking the recognizer to ensure it's not shared between users
    rec_lock.acquire()
    # Resetting Recognizer
    recognizer.Reset()
    pcm = bytearray()
    try:
        for chunk in chunks:
            decoded = decoder.decode(chunk)
            # Filters the audio before boosting
            if ENABLE_NOISE_REDUCTION:
                frame_length = len(decoded)
                if frame_length == 160 * 2:
                    decoded = audio_processor.Process10ms(decoded)
                elif frame_length == 160 * 4:
                    a, b = decoded[0:320], decoded[320:640]
                    a = audio_processor.Process10ms(a)
                    b = audio_processor.Process10ms(b)
                    decoded = bytearray()
                    decoded.extend(a.audio)
                    decoded.extend(b.audio)
                else:
                    current_app.logger.warning(f"Skipping frame denoise: frame length {frame_length} != 320")

            # Boosting the audio volume
            if BOOST_VOLUME:
                decoded = audioop.mul(decoded, 2, 6)

            # Saves the last received audio for debug purposes
            if ENABLE_AUDIO_DEBUG:
                pcm.extend(decoded)

            # Transcribing audio chunk
            recognizer.AcceptWaveform(decoded)

        final = json.loads(recognizer.Result())
    except Exception:
        current_app.logger.error("Exception while transcribing audio", exc_info=True)
        final = {"text": None, "result": []}
        response_part.add_header('Content-Disposition', 'form-data; name="QueryRetry"')
        response_part.set_payload(json.dumps({
            "Cause": 1,
            "Name": "AUDIO_INFO",
            "Prompt": "Error while decoding incoming audio."
        }))

    if ENABLE_AUDIO_DEBUG:
        with wave.open("/tmp/last_recording.wav", "wb") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(16000)
            f.writeframes(pcm)

    try:
        if final["text"]:
            output = [{'word': partial["word"], 'confidence': str(partial["conf"])} for partial in final["result"]]
            output[0]['word'] += '\\*no-space-before'
            output[0]['word'] = output[0]['word'][0].upper() + output[0]['word'][1:]
            response_part.add_header('Content-Disposition', 'form-data; name="QueryResult"')
            response_part.set_payload(json.dumps({
                'words': [output],
            }))
        else:
            current_app.logger.debug("No words detected")
            response_part.add_header('Content-Disposition', 'form-data; name="QueryRetry"')
            response_part.set_payload(json.dumps({
                "Cause": 1,
                "Name": "AUDIO_INFO",
                "Prompt": "Sorry, speech not recognized. Please try again."
            }))
    except Exception:
        current_app.logger.error("Exception occurred while transcribing audio", exc_info=True)
        response_part.add_header('Content-Disposition', 'form-data; name="QueryRetry"')
        response_part.set_payload(json.dumps({
            "Cause": 1,
            "Name": "AUDIO_INFO",
            "Prompt": "Error while processing transcribed text.."
        }))

    # Closing response
    # From: https://github.com/pebble-dev/rebble-asr/blob/37302ebed464b7354accc9f4b6aa22736e12b266/asr/__init__.py#L113
    parts.attach(response_part)
    parts.set_boundary('--Nuance_NMSP_vutc5w1XobDdefsYG3wq')
    response = Response('\r\n' + parts.as_string().split("\n", 3)[3].replace('\n', '\r\n'))
    response.headers['Content-Type'] = f'multipart/form-data; boundary={parts.get_boundary()}'

    # Resetting Recognizer
    recognizer.Reset()

    # Releasing lock
    rec_lock.release()
    return response
