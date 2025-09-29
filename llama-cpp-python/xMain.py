# !pip install llama-cpp-python

from llama_cpp import Llama

llm = Llama.from_pretrained(
	repo_id="ggml-org/SmolVLM-500M-Instruct-GGUF",
	filename="SmolVLM-500M-Instruct-Q8_0.gguf",
)

llm.create_chat_completion(
	messages = "No input example has been defined for this model task."
)