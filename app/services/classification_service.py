import requests

def classify_task_type(query):
    classification_prompt = f"""
    Classify the following query as either 'summarization' or 'question-answering':

    Query: {query}
    """
    classification_payload = {
        "model": "llama3",
        "prompt": classification_prompt,
        "max_tokens": 10,
        "temperature": 0,
        "stream": False
    }

    response = requests.post("http://localhost:11434/api/generate", json=classification_payload)
    response_data = response.json()
    classification = response_data.get('response', 'qa').strip().lower()
    return classification if classification in ['summarization', 'qa'] else 'qa'
