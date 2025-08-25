import asyncio, json
import modules.ollama.xGemma3_4b as xGemma
import modules.ollama.xSTT as xSTT
import modules.ollama.xTTS as xTTS

async def mic_chat():
    conversation_id = None
    instructions = None
    schema = {
      "lang": {
        "type": "string",
        "enum": ["en", "tr"],
        "description": "Detected language"
      }
    }
    print("""Voice Chat started.""")
    while True:
        user_input = xSTT.recognize_speech_from_mic()
        async for content, conversation_id in xGemma.chat(
            message=user_input,
            conversation_id=conversation_id,
            instructions=instructions,
            schema_props=schema,
            stream=False
        ):
            print("Assistant:", content)
            content_dict = json.loads(content)
            await xTTS.speak(text=content_dict["answer"], lang=content_dict["lang"])

if __name__ == "__main__":
    asyncio.run(mic_chat())