import asyncio
import os
import fitz
import docx
import uuid
# import pdfkit
from weasyprint import HTML, CSS
from fastapi.templating import Jinja2Templates

async def extract_text_from_pdf(pdf_path):
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
    text = ""
    try:
        doc = fitz.open(pdf_path)
        
        for page in doc:
            text += page.get_text() + "\n"
            
        doc.close()
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")
        
    return text

async def extract_text_from_word(docx_path):
    if not os.path.exists(docx_path):
        raise FileNotFoundError(f"Word document not found: {docx_path}")
        
    text = ""
    try:
        doc = docx.Document(docx_path)
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
    except Exception as e:
        raise Exception(f"Error extracting text from Word document: {str(e)}")
        
    return text

async def generate_resume_from_json(resume_data): 
    templates = Jinja2Templates(directory="templates")
    
    PDF_DIR = "generated_pdfs"
    os.makedirs(PDF_DIR, exist_ok=True)
    
    # Generate a unique filename for the PDF
    filename = f"resume_{uuid.uuid4().hex}.pdf"
    pdf_path = os.path.join(PDF_DIR, filename)
    
    # First, ensure resume_data is a dictionary
    if not isinstance(resume_data, dict):
        raise TypeError("resume_data must be a dictionary")
        
    # Safely get nested values
    def safe_get(data, *keys, default=""):
        """Safely get nested dictionary values"""
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
        
    # Get personal information
    personal_info = resume_data.get("Personal Information", {})
    
    formatted_data = {
        "basicDetails": {
            "name": safe_get(resume_data, "Personal Information", "Name"),
            "position": safe_get(resume_data, "Most_Match_ROLE"),
            "email": safe_get(resume_data, "Personal Information", "Email"),
            "linkedin": safe_get(resume_data, "Personal Information", "LinkedIn"),
            "location": "",  # Not available in the input data
            "phone": safe_get(resume_data, "Personal Information", "Phone number")
        },
        "summary": safe_get(resume_data, "Professional Summary"),
        "experience": [
            {
                "company": safe_get(exp, "Company"),
                "position": safe_get(exp, "Title"),
                "location": safe_get(exp, "location"),
                "startDate": safe_get(exp, "start_date"),
                "endDate": safe_get(exp, "end_date"),
                "description": "\n".join(exp["Descriptions"]) if isinstance(exp.get("Descriptions"), list) else str(exp.get("Descriptions", ""))
            } for exp in resume_data.get("Work Experience", [])
        ],
        "education": [
            {
                "institution": safe_get(edu, "Institution"),
                "degree": safe_get(edu, "Degree"),
                "location": safe_get(edu, "location"),
                "startDate": safe_get(edu, "start_date"),
                "endDate": safe_get(edu, "end_date")
            } for edu in resume_data.get("Education", [])
        ],
        "skills": resume_data.get("Skills", []),
        "certifications": [
            {
                "title": cert["Title"] if isinstance(cert, dict) and "Title" in cert else cert,
                "description": cert["Description"] if isinstance(cert, dict) and "Description" in cert else ""
            } for cert in resume_data.get("Certifications", [])
        ],
        "projects": [
            {
                "title": safe_get(proj, "Title"),
                "description": "\n".join(proj["Description"]) if isinstance(proj.get("Description"), list) else str(proj.get("Description", ""))
            } for proj in resume_data.get("Projects", [])
        ]
    }
    
    # Render template with formatted data
    html_content = templates.get_template("resume/resume.html").render(
        resume=formatted_data
    )
    
    
    try:  
        # Save the HTML content to a temporary file
        temp_html_path = os.path.join(PDF_DIR, f"temp_{uuid.uuid4().hex}.html")
        with open(temp_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        print(f"Temporary HTML file created at {temp_html_path}")
                  
        # Generate the PDF
        # pdfkit.from_file(temp_html_path, pdf_path, options=options)
        HTML(filename=temp_html_path).write_pdf(
        pdf_path,
        stylesheets=[CSS(string='@page { size: A4; margin: 5mm; }')]
        )
        
        # Verify PDF was created and has content
        if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
            print(f"PDF generated successfully at {pdf_path}")
        else:
            print(f"PDF generation failed or created empty file at {pdf_path}")
            return None
            
        # Clean up the temporary HTML file
        try:
            os.remove(temp_html_path)
            print(f"Temporary HTML file removed: {temp_html_path}")
        except Exception as e:
            print(f"Warning: Could not remove temporary HTML file: {str(e)}")
            
        # Return the PDF filename and path
        return {
            "filename": filename,
            "pdf_path": pdf_path,
            "download_url": f"/resume/download/{filename}"
        }
        
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        return None
