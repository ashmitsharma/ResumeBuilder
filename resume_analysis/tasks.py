from celery import Celery
import os
from resume_analysis.database import save_resume_analysis_sync, SaveResumeAnalysis
from typing import Dict


celery_app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0', result_expires=300)

@celery_app.task(name='tasks.full_resume_analysis')
def full_resume_analysis(resume_file_path: str, job_description: str):
    from resume_analysis.langchain_test import ResumeAnalyzer
    from resume_analysis.document_process import extract_text_from_pdf, extract_text_from_word
    import asyncio
    
    # Extract text from file based on extension
    try:
        file_extension = os.path.splitext(resume_file_path)[1].lower()
        
        # Create an async function to call the async extraction functions
        async def extract_text():
            if file_extension == ".pdf":
                return await extract_text_from_pdf(resume_file_path)
            elif file_extension in [".docx", ".doc"]:
                return await extract_text_from_word(resume_file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
        
        # Run the async function in a new event loop
        resume_text = asyncio.run(extract_text())
        
        # Perform analysis
        analyzer = ResumeAnalyzer()
        result = analyzer.get_missing_keywords(resume_text, job_description)
        

        # Create a SaveResumeAnalysis Pydantic object
        resume_data = SaveResumeAnalysis(
            task_id=full_resume_analysis.request.id,
            resume_text=resume_text,
            job_description=job_description,
            analysis_results=result
        )

        # Pass the object to the sync function
        save_resume_analysis_sync(resume_data)
            
        return {
            "analysis": result,
            "task_id": full_resume_analysis.request.id
        }
        
    except Exception as e:
        # Return error information
        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error_message": str(e)
        }
    finally:
        # Clean up the file after processing
        try:
            if os.path.exists(resume_file_path):
                os.remove(resume_file_path)
        except Exception as cleanup_error:
            print(f"Error removing temporary file {resume_file_path}: {str(cleanup_error)}")
        
@celery_app.task(name='tasks.generate_resume')
def generate_resume(analysis_dict: Dict):
    # Import here to avoid circular imports
    from resume_analysis.langchain_test import ResumeAnalyzer
    from resume_analysis.document_process import generate_resume_from_json
    import asyncio
    
    analyzer = ResumeAnalyzer()
    result = analyzer.get_structured_resume_data(resume_data=analysis_dict["resume_text"],
        missing_keywords_data=analysis_dict["analysis_results"],
        job_description=analysis_dict["job_description"])
    
    pdf_result = asyncio.run(generate_resume_from_json(result))
    
    if pdf_result:
        return {
            "pdf": {
                "filename": pdf_result["filename"],
                "pdf_path": pdf_result["pdf_path"],
                "download_url": pdf_result["download_url"]
            }
        }
    else:
        return {
            "status": "error",
            "result": result,
            "error_message": "Failed to generate PDF resume"
        }


@celery_app.task(name='tasks.generate_resume_with_keyword')
def generate_resume_with_keyword(resume_file_path: str, missing_keywords: str):
    from resume_analysis.langchain_test import ResumeAnalyzer
    from resume_analysis.document_process import extract_text_from_pdf, extract_text_from_word, generate_resume_from_json
    import asyncio

    # Extract text from file based on extension
    try:
        file_extension = os.path.splitext(resume_file_path)[1].lower()
        
        # Create an async function to call the async extraction functions
        async def extract_text():
            if file_extension == ".pdf":
                return await extract_text_from_pdf(resume_file_path)
            elif file_extension in [".docx", ".doc"]:
                return await extract_text_from_word(resume_file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
        
        # Run the async function in a new event loop
        resume_text = asyncio.run(extract_text())
        
        # Perform analysis
        analyzer = ResumeAnalyzer()
        result = analyzer.get_structured_resume_from_keywords(resume_text, missing_keywords)

        pdf_result = asyncio.run(generate_resume_from_json(result))
    
        if pdf_result:
            return {
                "pdf": {
                    "filename": pdf_result["filename"],
                    "pdf_path": pdf_result["pdf_path"],
                    "download_url": pdf_result["download_url"]
                }
            }
        else:
            return {
                "status": "error",
                "result": result,
                "error_message": "Failed to generate PDF resume"
            }
    except Exception as e:
        # Return error information
        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error_message": str(e)
        }
    finally:
        # Clean up the file after processing
        try:
            if os.path.exists(resume_file_path):
                os.remove(resume_file_path)
        except Exception as cleanup_error:
            print(f"Error removing temporary file {resume_file_path}: {str(cleanup_error)}")
