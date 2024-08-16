import requests
from config.config import Config
import json
MODEL = "llama3.1"

def ask_llama(context, question):
    template = """
    Answer the question based on the context below. If you can't 
    answer the question, reply "I don't know".

    Context: {context}

    Question: {question}
    """
    prompt = template.format(context=context, question=question)
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "api_key": Config.LLAMA_API_KEY
    }

    response = requests.post(Config.LLAMA_API_URL, json=payload)
    response_data = response.json()
    return response_data.get('response', 'Error: No response received.')



def summarize_llama(filecontents):
    summarization_prompt = f"""
    Please summarize the content of this file below. Focus on extracting key themes, main ideas, and essential details that would help
    in understanding the context and facilitating search that this document could be found as a related document to a search query
    Additionally, provide a brief overview of the topics covered so that related files on similar subjects or with relevant information can be 
    easily identified and looked up. summary should not be more than 250 characters:

    Query: {filecontents}
    """
    summerization_payload = {
        "model": MODEL,
        "prompt": summarization_prompt,
        "temperature": 0,
        "stream": False
    }

    response = requests.post("http://localhost:11434/api/generate", json=summerization_payload)
    response_data = response.json()
    response_data = response.json()
    return response_data.get('response', 'Error: No response received.')



# def generate_url_title(text):
#     title_prompt = f"""
#     Create a title that captures the essence of the following text, using exactly 20 characters. The title should be concise, impactful, and reflect the main theme or idea presented. \
#     Text: {text}
#     """
#     title_payload = {
#         "model": MODEL,
#         "prompt": title_prompt,
#         "stream": False
#         }

#     response = requests.post("http://localhost:11434/api/generate", json=title_payload)

#     # Parse the JSON content from the response
#     response_data = json.loads(response.content.decode('utf-8'))

#     # Extract the title from the response
#     title = response_data.get('message', {})

#     return json.dumps({'title': title})

