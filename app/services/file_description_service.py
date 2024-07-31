import requests
from config.config import Config



def summarize_llama(filecontents):
    summarization_prompt = f"""
    Please summarize the content of this file below. 
    Focus on extracting key themes, main ideas, and essential details that would help in understanding the context. 
    Additionally, provide a brief overview of the topics covered so that related files on similar subjects or with relevant information can be easily identified and looked up
    summary should not be more than 500 characters:

    Query: {filecontents}
    """
    classification_payload = {
        "model": "llama3",
        "prompt": summarization_prompt,
        "max_tokens": 10,
        "temperature": 0,
        "stream": False
    }

    response = requests.post("http://localhost:11434/api/generate", json=classification_payload)
    response_data = response.json()
    response_data = response.json()
    return response_data.get('response', 'Error: No response received.')