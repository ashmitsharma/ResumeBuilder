# Resume Builder

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the root directory with the following content:
```
OPENAI_API_KEY=your_openai_api_key_here
```
Replace `your_openai_api_key_here` with your actual OpenAI API key.

## Running the Application

1. Start the Fast API application:
```bash
python upload_file.py
```

2. Start the Celery worker for background tasks:
```bash
celery -A resume_analysis.tasks worker --loglevel=info
```

## Project Structure

- `upload_file.py`: Main FastAPI application
- `resume_analysis/`: Package containing resume analysis functionality
  - `tasks.py`: Celery tasks for asynchronous processing
  - `document_process.py`: Document processing utilities
  - `database.py`: Database operations
- `templates/`: HTML templates
- `generated_pdfs/`: Directory for storing generated PDF files
- `uploads/`: Directory for storing uploaded files


