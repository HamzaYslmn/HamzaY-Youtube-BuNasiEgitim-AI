
from gtts import gTTS
from playsound import playsound
import tempfile
import os

def speak(text, lang='en'):
    tts = gTTS(text=text, lang=lang)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
        temp_path = fp.name
    tts.save(temp_path)
    playsound(temp_path)
    os.remove(temp_path)

if __name__ == "__main__":
    text = "güneş neden sarı renkli"
    speak(text)