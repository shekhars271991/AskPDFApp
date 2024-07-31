import requests
from config.config import Config

def ask_llama(context, question):
    template = """
    Answer the question based on the context below. If you can't 
    answer the question, reply "I don't know".

    Context: {context}

    Question: {question}
    """
    prompt = template.format(context=context, question=question)
    payload = {
        "model": "llama3",
        "prompt": prompt,
        "stream": False,
        "api_key": Config.LLAMA_API_KEY
    }

    response = requests.post(Config.LLAMA_API_URL, json=payload)
    response_data = response.json()
    return response_data.get('response', 'Error: No response received.')
