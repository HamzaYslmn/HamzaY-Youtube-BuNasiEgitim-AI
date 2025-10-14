from g4f.client import Client
from g4f.Provider import Mintlify

def web_agent(user_input):
    client = Client(provider=Mintlify)
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": f"Plain text ve Türkçe olarak yanıt ver.: {user_input}"}],
        web_search=True
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    user_input = input("Bir soru girin: ")
    print(web_agent(user_input))