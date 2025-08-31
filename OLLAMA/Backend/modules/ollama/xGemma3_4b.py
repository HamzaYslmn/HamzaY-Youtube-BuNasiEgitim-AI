
import asyncio
import uuid
import base64
from typing import AsyncGenerator, Dict, List, Optional, Tuple, Union
from ollama import AsyncClient
import httpx
import json
import os

_client = AsyncClient()

CONV_DIR = os.path.join(os.path.dirname(__file__), "conversations")
os.makedirs(CONV_DIR, exist_ok=True)

class ConversationManager:
    def __init__(self, max_size_bytes: int = 128000):
        self.max_size_bytes = max_size_bytes * 5

    def _get_conv_path(self, conv_id: str) -> str:
        return os.path.join(CONV_DIR, f"{conv_id}.json")

    def _load_conversation(self, conv_id: str) -> Dict:
        path = self._get_conv_path(conv_id)
        if not os.path.exists(path):
            return {
                "system": {'role': 'system', 'content': "You are a helpful and concise assistant. Detect the user's language from their request and always respond in the same language."},
                "history": []
            }
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_conversation(self, conv_id: str, conversation: Dict):
        path = self._get_conv_path(conv_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(conversation, f, ensure_ascii=False)

    def calculate_size(self, conversation: Dict) -> int:
        return len(json.dumps(conversation, ensure_ascii=False).encode("utf-8"))

    def edit_system_message(self, conv_id: str, system_message: str):
        conversation = self._load_conversation(conv_id)
        conversation["system"] = {"role": "system", "content": system_message}
        self._save_conversation(conv_id, conversation)

    def get_conversation(self, conv_id: str, ollama: bool = False) -> Dict:
        conversation = self._load_conversation(conv_id)
        if not ollama:
            return conversation
        else:
            system_msg = conversation.get("system")
            if isinstance(system_msg, dict):
                sys_entry = system_msg
            else:
                sys_entry = {"role": "system", "content": str(system_msg)}
            return {"history": [sys_entry] + list(conversation.get("history", []))}

    def add_conversation(self,
        conv_id: str,
        user_content: str,
        assistant_content: str,
        images: Optional[List[bytes]] = None,
    ):
        conversation = self._load_conversation(conv_id)
        while (
            self.calculate_size(conversation) > self.max_size_bytes
            and len(conversation["history"]) > 2
        ):
            conversation["history"].pop(0)

        user_entry = {"role": "user", "content": user_content}
        if images:
            user_entry["images"] = images
        conversation["history"].append(user_entry)
        conversation["history"].append({"role": "assistant", "content": assistant_content})
        self._save_conversation(conv_id, conversation)


_conv_manager = ConversationManager()

def create_schema(additional_props: Optional[Dict] = None) -> Dict:
    props = additional_props or {}
    props["answer"] = {
        "type": "string",
        "description": "Responses given in accordance with the instructions"
    }
    return {
        "type": "object",
        "properties": props,
        "required": list(props.keys()),
        "additionalProperties": False
    }

async def get_image_bytes(image_input: str) -> bytes:
    if image_input.startswith(("http://", "https://", "/")):
        async with httpx.AsyncClient() as client:
            response = await client.get(image_input)
            response.raise_for_status()
            return response.content
    if os.path.isfile(image_input):
        with open(image_input, "rb") as img_file:
            return img_file.read()
    if image_input.startswith("data:image"):
        image_input = image_input.split(",", 1)[-1]
    try:
        return base64.b64decode(image_input, validate=True)
    except Exception:
        return image_input.encode()

async def chat(
    message: str,
    image: Union[bytes, str] = None,
    conversation_id: str = None,
    instructions: str = None,
    model: str = "gemma3:4b-it-q4_K_M",
    stream: bool = True,
    schema_props: Optional[Dict] = None,
) -> AsyncGenerator[Tuple[str, str], None]:
    conv_id = conversation_id or f"conv_{uuid.uuid4()}"
    if instructions:
        _conv_manager.edit_system_message(conv_id, instructions)
    messages = _conv_manager.get_conversation(conv_id, ollama=True)["history"]
    user_message = {"role": "user", "content": message}
    image_bytes = None
    if image:
        image_bytes = await get_image_bytes(image)
        user_message["images"] = [image_bytes]
    messages.append(user_message)
    response = await _client.chat(
        model=model,
        messages=messages,
        stream=stream,
        format=create_schema(schema_props)
    )
    full_response = ""
    if stream:
        async for chunk in response:
            content = chunk.get("message", {}).get("content", "")
            if content:
                full_response += content
                yield content, conv_id
    else:
        full_response = response.get("message", {}).get("content", "")
        yield full_response, conv_id
    images_list = [image_bytes] if image_bytes else None
    _conv_manager.add_conversation(conv_id, message, full_response, images_list)

if __name__ == "__main__":
    try:
        async def interactive_chat():
            conversation_id = None
            instructions = None
            schema = {
              "lang": {
                "type": "string",
                "enum": ["en", "tr"],
                "description": "Detected language"
              }
            }
            print("""Chat started. 
                    Type 'exit' to quit,
                    'p,' to add a photo,
                    'i,' to add instructions.""")

            while True:
                user_input = input("\nYou: ").strip()
                if user_input.lower() == "exit":
                    break
                image = None
                if user_input.startswith("p,"):
                    user_input = user_input[2:].strip()
                    image = input("Photo URL or base64: ")
                if user_input.startswith("i,"):
                    user_input = user_input[2:].strip()
                    instructions = input("Instructions: ")
                print("Assistant: ", end="", flush=True)
                async for content, conversation_id in chat(
                    message=user_input,
                    image=image,
                    conversation_id=conversation_id,
                    instructions=instructions,
                    schema_props=schema,
                ):
                    print(content, end="", flush=True)
                print()
                conv = _conv_manager.get_conversation(conversation_id)
                size = _conv_manager.calculate_size(conv)
                print(f"\n[Conversations]: {conv}")
                print(f"\n[Size]: {size} bytes")
        
        asyncio.run(interactive_chat())
    except Exception as e:
        print(f"Error: {e}")
