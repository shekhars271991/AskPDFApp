import os
import uuid
def chunk_text(text, chunk_size=500):
    words = text.split()
    chunks = [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
    return chunks

def get_unique_filename(filename):
    original_filename = filename
    filename_prefix = original_filename[:3] if len(original_filename) >= 3 else original_filename
    filename, file_extension = os.path.splitext(original_filename)
    unique_filename = f"{filename_prefix}_{str(uuid.uuid4())[:8]}{file_extension}"
    return unique_filename