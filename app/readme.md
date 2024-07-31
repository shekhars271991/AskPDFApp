# Flask Document Processing Application

## Overview

This Flask application provides functionality for uploading PDF documents, extracting and chunking text, generating embeddings, and interacting with a LLaMA model for classification and query answering. It uses Redis for storing document metadata, chunks, and embeddings.


## Prerequisites

1. **Python 3.7+**: Ensure you have Python 3.7 or higher installed.
2. **Redis**: Make sure Redis is installed and running on your local machine or accessible remotely.
3. **LLaMA Model**: You should have the LLaMA model running on port `11434`. Adjust the port and URL in the code if necessary.

## Installation

1. **Clone the Repository**

    ```bash
    git clone https://github.com/your-username/your-repo.git
    cd your-repo
    ```

2. **Create and Activate a Virtual Environment**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install Dependencies**

    ```bash
    pip install -r requirements.txt
    ```

4. **Create the Upload Directory**

    Ensure the `UPLOAD_DIRECTORY` exists or create it:

    ```bash
    mkdir -p AskPDF/backend_llama/uploadedFiles
    ```

## Configuration

1. **Configure Redis**: Make sure your Redis server is running on `localhost:6379`. Adjust `redis_client` settings in `redis_service.py` if needed.
2. **Configure LLaMA**: Ensure the LLaMA model is accessible at `http://localhost:11434/api/generate`. Adjust the URL in `classification_service.py` and `llama_service.py` if necessary.

## Running the Application

1. **Run the Flask Application**

    ```bash
    python app.py
    ```

    The application will start on `http://127.0.0.1:5000`.

2. **Access the Application**

    Open your browser and go to `http://127.0.0.1:5000` to interact with the application through its endpoints.

## API Endpoints

- **POST `/ask`**: Accepts a query and role, processes it, and returns an answer.
- **POST `/upload`**: Uploads a PDF document, processes it, and stores the text chunks and embeddings in Redis.
- **GET `/documents`**: Lists all uploaded documents with their metadata.
- **DELETE `/delete`**: Deletes a document by its name from the filesystem and Redis.

## Testing

1. **Run Tests**

    You can run tests using a testing framework like `pytest`. Ensure you have `pytest` installed.

    ```bash
    pip install pytest
    pytest
    ```

## Contributing

Feel free to fork the repository and submit pull requests. Please follow the contribution guidelines and ensure your changes are well-tested.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any questions or feedback, please reach out to [your-email@example.com](mailto:your-email@example.com).



