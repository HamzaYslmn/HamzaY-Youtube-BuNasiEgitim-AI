from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import List, Dict
from webtool import web_agent

MODEL_NAME = "vngrs-ai/Kumru-2B-Base"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, dtype="auto", device_map="auto")

conversation_history = []

def generate_answer(prompt: str, max_length: int = 512) -> str:
    global conversation_history
    
    full_prompt = "\n".join(conversation_history) + "\n" + prompt if conversation_history else prompt
    
    tokenized_text = tokenizer.encode_plus(
        full_prompt,
        return_tensors='pt',
        return_token_type_ids=False,
        max_length=model.config.max_position_embeddings - 64,
        truncation=True
    ).to(model.device)

    generated_tokens = model.generate(
        **tokenized_text,
        max_new_tokens=max_length,
        repetition_penalty=1.15,
        no_repeat_ngram_size=5
    )
    generated_text = tokenizer.decode(generated_tokens[0], skip_special_tokens=True)
    
    conversation_history.extend([prompt, f"Cevap: {generated_text}"])
    if len(conversation_history) > 10:
        conversation_history = conversation_history[-10:]
    
    return generated_text

PROMPT_TEMPLATE = """Aşağıdaki web arama sonuçlarına dayanarak soruyu yanıtlayın. Yanıtınız bilgilendirici, doğru ve Türkçe olmalıdır.
Web Arama Sonuçları:
{search_results}

Soru: {question} ?
Cevap:
"""

def ai_websearch_answer(query: str, num_results: int = 2, fetch_content: bool = True) -> str:
    print(f"\n{'='*50}\nSoru: {query}\n{'='*50}\n")
    print("🔍 Web araması yapılıyor...")

    search_results = web_agent(query)

    prompt = PROMPT_TEMPLATE.format(question=query, search_results=search_results)
    print("🤖 AI yanıt üretiliyor...\n")
    
    return generate_answer(prompt)

if __name__ == "__main__":
    print("Kumru AI\n" + "="*50)
    print("Komutlar: 'q' (çık), 'reset' (hafızayı temizle)")
    
    while True:
        user_query = input("\nSoru girin: ").strip()
        
        if user_query.lower() in ['q', 'quit', 'exit', 'çık']:
            print("Görüşmek üzere!")
            break
        
        if user_query.lower() == 'reset':
            conversation_history.clear()
            print("✅ Konuşma hafızası temizlendi.")
            continue
        
        if not user_query:
            continue
        
        try:
            answer = ai_websearch_answer(user_query, num_results=2)
            print(f"\n{'='*50}\n\033[92m💬 YANIT:\033[0m\n{'='*50}\n\033[92m{answer}\033[0m\n{'='*50}\n")
        except Exception as e:
            print(f"❌ Hata oluştu: {e}")
