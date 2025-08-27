import asyncio
from ollama import AsyncClient

async def main():
  messages = [
    {
      'role': 'system',
      'content': 'Always talk in english.',
    },
    {
      'role': 'user',
      'content': 'Çilek ne renktir?',
    },
    {
      'role': 'assistant',
      'content': "Strawberries are red.",
    },
  ]
  client = AsyncClient()
  while True:
    user_input = input('\n\nChat with history: ')
    messages.append({'role': 'user', 'content': user_input})
    response = await client.chat('gemma3:4b-it-q4_K_M', messages=messages, stream=True)

    async for chunk in response:
        assistant_content = chunk['message']['content']
        messages.append({'role': 'assistant', 'content': assistant_content})
        print(assistant_content, end='', flush=True)

if __name__ == '__main__':
  asyncio.run(main())