
from gtts import gTTS
import tempfile
import os
import asyncio

async def speak(text, lang='en'):
    tts = gTTS(text=text, lang=lang)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
        temp_path = fp.name
    tts.save(temp_path)

    def play_and_remove():
        from playsound3 import playsound
        try:
            playsound(temp_path)
        finally:
            # Oynatma bittikten sonra sil
            if os.path.exists(temp_path):
                os.remove(temp_path)

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, play_and_remove)

if __name__ == "__main__":
    text = "güneş neden sarı renkli"
    asyncio.run(speak(text, lang='tr'))