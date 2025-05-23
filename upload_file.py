from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends, Body
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import uuid
from celery.result import AsyncResult
from resume_analysis.tasks import full_resume_analysis, celery_app, generate_resume, generate_resume_with_keyword
from resume_analysis.database import get_resume_analysis, get_db
from sqlalchemy.ext.asyncio import AsyncSession



app = FastAPI()

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Making Upload dir if it does not exist
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/generate-resume-with-keyword/")
async def upload_files(resume: UploadFile = File(...), missing_keywords: str = Body(...)):
     # Save the uploaded file with a unique name
    file_extension = os.path.splitext(resume.filename)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    try:
        # Save the file to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(resume.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
    finally:
        # Close the file
        resume.file.close()
    
    # Queue the Celery task that will handle both file processing and analysis
    task = generate_resume_with_keyword.delay(file_path, missing_keywords)

    return {
        "task_id": task.id,
        "status_url": f"/task-status/{task.id}",
        "message": "Analysis task queued successfully"
    }

@app.post("/upload/")
async def upload_files(resume: UploadFile = File(...), job_description: str = Body(...)):
    # Save the uploaded file with a unique name
    file_extension = os.path.splitext(resume.filename)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    try:
        # Save the file to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(resume.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
    finally:
        # Close the file
        resume.file.close()
    
    # Queue the Celery task that will handle both file processing and analysis
    task = full_resume_analysis.delay(file_path, job_description)
    
    # Return the task ID and a URL to check the status
    return {
        "task_id": task.id,
        "status_url": f"/task-status/{task.id}",
        "message": "Analysis task queued successfully"
    }

@app.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)
    
    response = {
        "task_id": task_id,
        "status": task_result.status,
    }
    
    # If the task is complete, include the result
    if task_result.status == "SUCCESS":
        response["result"] = task_result.result
    elif task_result.status == "FAILURE":
        response["error"] = str(task_result.result)
    
    return response

@app.post("/generate-resume/{task_id}")
async def generate_structured_resume(task_id: str,  db: AsyncSession = Depends(get_db)):
    # Get the saved analysis data from the database
    analysis_data = await get_resume_analysis(task_id, db)
    
    if not analysis_data:
        raise HTTPException(status_code=404, detail="Analysis data not found. Please run analysis first.")
    
    # Convert the stored analysis results from JSON string to dict
    analysis_dict = analysis_data.to_dict()
    
    # from resume_analysis.langchain_test import ResumeAnalyzer
    task = generate_resume.delay(analysis_dict)

    return {
        "task_id": task.id,
        "status_url": f"/task-status/{task.id}"
    }

@app.get("/resume/download/{filename}")
async def download_pdf(filename: str):
    PDF_DIR="generated_pdfs"
    file_path = os.path.join(PDF_DIR, filename)
    if os.path.exists(file_path):
        # Check if file is not empty
        if os.path.getsize(file_path) > 0:
            return FileResponse(
                path=file_path,
                filename="resume.pdf", 
                media_type="application/pdf",
                headers={
                    "Content-Disposition": "attachment; filename=resume.pdf",
                    "Content-Type": "application/pdf"
                }
            )
        else:
            return JSONResponse(content={"error": "PDF file is empty"}, status_code=500)
    else:
        print(f"PDF file not found: {file_path}")
        return JSONResponse(content={"error": "File not found"}, status_code=404)


# Run the application with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("upload_file:app", host="0.0.0.0", port=8000, reload=True)