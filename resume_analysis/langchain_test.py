import getpass
import os
import json
from typing import Dict, Any
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


class ResumeAnalyzer:
    # Class for analyzing resumes against job descriptions

    def __init__(self, model_name: str = "gpt-4o-mini", model_provider: str = "openai"):
        
        # Load environment variables
        load_dotenv()

        # Set OpenAI API key if not already set
        if not os.environ.get("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter your OpenAI API key: ")

        self.model_name = model_name
        self.model_provider = model_provider

    def _base_prompt(self, resume_data: str, job_description: str) -> str:
        # Helper function to prepare the prompt
        return f"""
        Resume Data = "{resume_data}" and Job Description = "{job_description}"
        """
    
    def get_missing_keywords(self, resume_data: str, job_description: str) -> Dict[str, Any]:
        #Function used to extract missing keyword, current_score and expected_score.
        # Initialize the chat model
        llm = init_chat_model(self.model_name, model_provider=self.model_provider).with_structured_output(method="json_mode")

        message = self._base_prompt(resume_data, job_description)

        # System message defining the analysis task
        system_message = """You are the backend engine for a resume analysis application. Given a job description and a candidate's resume, perform a technical keyword-based match analysis.

        Focus strictly on hard skills, tools, technologies, certifications, and domain-specific terms. Ignore soft skills, verbs, general responsibilities, or action words.

        Your Tasks:
        Match Scoring (current_score)
        Calculate an integer match percentage (0–100) between the resume and the job description based only on the presence of relevant technical keywords, hard skills, and domain-specific terms.

        Normalize keywords (e.g., lowercase, singular/plural forms).

        Count only meaningful, technical, or domain-relevant terms (e.g., Python, Kubernetes, AWS, CISSP).

        Missing Keywords (missing_keywords)
        Identify and return a list of missing technical keywords from the job description that are not present in the resume and that, if included, would increase the match score.

        Return only nouns or phrases that represent tools, technologies, platforms, or certifications.

        Do not include verbs, soft skills, or general terms (e.g., "collaborated", "communication").

        Improved Score (expected_score)
        Estimate the improved match percentage if all missing keywords were properly added to the resume. This must be higher than the original score if any keywords are missing.

        High Match Exception
        If the original score is 85 or above, return:

        missing_keywords: []

        improved_score: same as score

        Output Format (JSON only):
        {
        "current_score": <integer from 0 to 100>,
        "expected_score": <integer from 0 to 100>,
        "missing_keywords": [<array of technical keywords as strings>]
        }
        Strict Rules:
        Do not include action words, verbs, or general phrases in missing_keywords.
        Do not return any explanations, comments, or extra text.
        Only return the structured JSON above."""

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=message)
        ]

        response = llm.invoke(messages)

        return response
    
    def get_structured_resume_data(self, resume_data: str, missing_keywords_data: Dict[str, Any], job_description: str = "") -> Dict[str, Any]:
        # To get structured and enhanced resume data.
        json_schema = {
        "title": "ResumeData",
        "description": "Structured resume data with enhancements",
        "type": "object",
        "properties": {
            "Most_Match_ROLE": {"type": "string"},
            "Personal Information": {
                "type": "object",
                "properties": {
                    "Name": {"type": "string"},
                    "Phone number": {"type": "string"},
                    "Email": {"type": "string"},
                    "LinkedIn": {"type": "string"},
                    "GitHub/portfolio": {"type": "string"}
                },
                "required": ["Name", "Phone number", "Email", "LinkedIn", "GitHub/portfolio"]
            },
            "Professional Summary": {"type": "string"},
            "Skills": {"type": "array", "items": {"type": "string"}},
            "Work Experience": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "Company": {"type": "string"},
                        "Title": {"type": "string"},
                        "location": {"type": "string"},
                        "start_date": {"type": "string"},
                        "end_date":{"type": "string"},
                        "Descriptions": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["Company", "Title", "location", "start_date", "end_date", "Descriptions"]
                }
            },
            "Education": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "Institution": {"type": "string"},
                        "location": {"type": "string"},
                        "Degree": {"type": "string"},
                        "start_date": {"type": "string"},
                        "end_date":{"type": "string"}
                    },
                    "required": ["Institution", "Degree", "location", "start_date", "end_date"]
                }
            },
            "Certifications": {
                "type": "array",
                "items": {"type": "string"}
            },
            "Projects": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "Title": {"type": "string"},
                        "Description": {"type": "array", "items": {"type": "string"}},
                        "Technologies": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["Title", "Description", "Technologies"]
                }
            },
            "Other": {
                "type": "object",
                "properties": {
                    "Strengths": {"type": "array", "items": {"type": "string"}},
                    "Languages": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["Strengths", "Languages"]
            }
        },
        "required": ["Most_Match_ROLE", "Personal Information", "Professional Summary", "Skills", "Work Experience", "Education", "Certifications", "Projects", "Other"]
        }

        llm = init_chat_model(self.model_name, model_provider=self.model_provider).with_structured_output(json_schema)

        message = self._base_prompt(resume_data, job_description)

        missing_keywords_info = f"\n\nMissing Keywords: {missing_keywords_data.get('missing_keywords', [])}\n"

        system_message = f"""
                        You are a professional resume optimizer tasked with transforming resumes to achieve maximum alignment with specific job descriptions and also add related skills to those skills. Your role is to deeply analyze both the candidate's experience and the job description, and then reconstruct the resume to create a compelling, keyword-rich, and contextually aligned document that stands out to hiring managers and ATS systems.

                        Your tasks, in priority order:

                        1. **JOB MATCH OPTIMIZATION**:
                        - Perform a deep comparative analysis between the candidate's background and the job description.
                        - Prioritize and restructure content to elevate the most relevant experiences, skills, and accomplishments.
                        - Adjust role titles and descriptions subtly if needed to reflect alignment, while maintaining truthfulness.

                        2. **KEYWORD ENRICHMENT**:
                        - Identify critical keywords and phrases from the job description (including tools, skills, certifications, responsibilities, etc.).
                        - Seamlessly integrate all missing keywords {missing_keywords_info} across the following sections:
                            - Professional Summary
                            - Skills
                            - Work Experience
                            - Projects
                        - Use varied phrasing and synonyms to ensure natural, non-repetitive inclusion.

                        3. **ENHANCE CONTEXTUAL DEPTH IN WORK EXPERIENCE**:
                        - For each role, generate **at least 5 bullet points** that:
                            - Reflect job-specific responsibilities and achievements
                            - Include metrics, KPIs, or performance indicators to show measurable impact
                            - Use industry-specific terminology from the job description
                            - Begin with varied, dynamic action verbs
                            - Add brief context when necessary to show scope and scale (e.g., “Led a 6-member cross-functional team…”)

                        4. **CRAFT A TARGETED PROFESSIONAL SUMMARY**:
                        - Create a persuasive, 3-5 sentence summary that positions the candidate as an ideal fit for the role.
                        - Emphasize total years of experience, domain expertise, standout accomplishments, and alignment with the job's core requirements.

                        5. **STRUCTURE IN JSON FORMAT**:
                        - Organize the entire resume into the provided JSON schema format, clearly separating sections.
                        - Ensure information flows logically and highlights the candidate's match with the job.

                        6. **ROLE MATCH INSIGHT**:
                        - Based on both the resume and the job description, suggest the most suitable job titles or role variations the candidate is ideally positioned for.

                        Important notes:
                        - Go beyond surface-level edits—strategically reframe content for maximum relevance and persuasive impact.
                        - Think like a recruiter and an ATS: clarity, keyword presence, and achievement-driven framing matter.
                        - Be concise but informative; each sentence should serve a purpose.

                        Your final output **must strictly follow the specified JSON schema** while incorporating the enhancements above.
                        """

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=message)
        ]

        response = llm.invoke(messages)
        
        # Add missing keywords data
        # response["Missing Keywords"] = missing_keywords_data.get("missing_keywords", [])
        # response["Current Score"] = missing_keywords_data.get("current_score", 0)
        # response["Expected Score"] = missing_keywords_data.get("expected_score", 0)
        
        return response

    def get_structured_resume_from_keywords(self, resume_data: str, missing_keywords_data: str) -> Dict[str, Any]:
        # To get structured resume data based only on resume content and missing keywords (no job description).
        json_schema = {
        "title": "ResumeData",
        "description": "Structured resume data with enhancements",
        "type": "object",
        "properties": {
            "Most_Match_ROLE": {"type": "string"},
            "Personal Information": {
                "type": "object",
                "properties": {
                    "Name": {"type": "string"},
                    "Phone number": {"type": "string"},
                    "Email": {"type": "string"},
                    "LinkedIn": {"type": "string"},
                    "GitHub/portfolio": {"type": "string"}
                },
                "required": ["Name", "Phone number", "Email", "LinkedIn", "GitHub/portfolio"]
            },
            "Professional Summary": {"type": "string"},
            "Skills": {"type": "array", "items": {"type": "string"}},
            "Work Experience": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "Company": {"type": "string"},
                        "Title": {"type": "string"},
                        "location": {"type": "string"},
                        "start_date": {"type": "string"},
                        "end_date":{"type": "string"},
                        "Descriptions": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["Company", "Title", "location", "start_date", "end_date", "Descriptions"]
                }
            },
            "Education": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "Institution": {"type": "string"},
                        "location": {"type": "string"},
                        "Degree": {"type": "string"},
                        "start_date": {"type": "string"},
                        "end_date":{"type": "string"}
                    },
                    "required": ["Institution", "Degree", "location", "start_date", "end_date"]
                }
            },
            "Certifications": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "Title": {"type": "string"},
                        "Description": {"type": "string"},
                    },
                "required": ["Title", "Description"]
            }
            },
            "Projects": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "Title": {"type": "string"},
                        "Description": {"type": "array", "items": {"type": "string"}},
                        "Technologies": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["Title", "Description", "Technologies"]
                }
            },
            "Other": {
                "type": "object",
                "properties": {
                    "Strengths": {"type": "array", "items": {"type": "string"}},
                    "Languages": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["Strengths", "Languages"]
            }
        },
        "required": ["Most_Match_ROLE", "Personal Information", "Professional Summary", "Skills", "Work Experience", "Education", "Certifications", "Projects", "Other"]
        }

        llm = init_chat_model(self.model_name, model_provider=self.model_provider).with_structured_output(json_schema)

        # Create a message without job description
        message = f"""
        Resume Data = "{resume_data}"
        """

        missing_keywords_info = f"\n\nMissing Keywords: {missing_keywords_data}\n"

        system_message = f"""You are a professional resume optimizer that enhances resumes by incorporating specific skills and keywords. Your primary goal is to make the candidate's resume as appealing as possible.        
            
            Your tasks in order of priority:
            
            1. ANALYZE THE RESUME: Thoroughly review the resume content to understand the candidate's experience, skills, and career trajectory.
            
            2. KEYWORD OPTIMIZATION: Incorporate all the missing keywords{missing_keywords_info} naturally throughout the resume, especially in:
               - Professional Summary
               - Skills section
               - Work Experience descriptions
               - Project descriptions
            
            3. ENHANCE WORK EXPERIENCE: For each Work Experience entry, ensure there are at least 5 bullet points that:
               - Showcase the candidate's achievements and responsibilities
               - Use industry-specific terminology related to the candidate's field
               - Quantify achievements with metrics where possible
               - Begin with strong action verbs
               - Demonstrate technical and soft skills
            
            4. CREATE A PROFESSIONAL SUMMARY: Write a compelling summary that highlights the candidate's most relevant skills and experiences.
            
            5. STRUCTURE THE DATA: Parse all resume information into the specified JSON schema format.
            
            6. IDENTIFY ROLE MATCH: Based on the analysis, determine the most suitable role that matches the candidate's experience and skills.
            
            Remember: The goal is to enhance the resume by incorporating the missing keywords and optimizing the content to showcase the candidate's qualifications.
            
            The response MUST conform to the provided JSON schema structure."""

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=message)
        ]

        response = llm.invoke(messages)
        
        # # Add missing keywords data
        # response["Missing Keywords"] = missing_keywords_data.get("missing_keywords", [])
        # response["Current Score"] = missing_keywords_data.get("current_score", 0)
        # response["Expected Score"] = missing_keywords_data.get("expected_score", 0)
        
        return response

