# Resume Builder

A web application that helps users build and analyze resumes using AI.

## Features

- Upload and analyze resumes
- Generate PDF resumes
- AI-powered resume analysis and suggestions
- Asynchronous processing with Celery

## Installation

1. Clone the repository:
```bash
git clone https://github.com/ashmitsharma/ResumeBuilder.git
cd ResumeBuilder
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Linux/Mac
source venv/bin/activate
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with the following content:
```
OPENAI_API_KEY=your_openai_api_key_here
```
Replace `your_openai_api_key_here` with your actual OpenAI API key.

## Running the Application

1. Start the Flask application:
```bash
python upload_file.py
```

2. Start the Celery worker for background tasks:
```bash
celery -A resume_analysis.tasks worker --loglevel=info
```

## Project Structure

- `upload_file.py`: Main Flask application
- `resume_analysis/`: Package containing resume analysis functionality
  - `tasks.py`: Celery tasks for asynchronous processing
  - `document_process.py`: Document processing utilities
  - `database.py`: Database operations
- `templates/`: HTML templates
- `generated_pdfs/`: Directory for storing generated PDF files
- `uploads/`: Directory for storing uploaded files

## Usage

1. Navigate to the web application in your browser
2. Upload your resume
3. View the analysis and suggestions
4. Generate a PDF version of your resume

## License

[MIT](https://choosealicense.com/licenses/mit/)
