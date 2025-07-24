import os
import json
import openai
import google.generativeai as genai
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    def __init__(self):
        self.provider = os.environ.get("LLM_PROVIDER", "gemini").lower()
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        self.gemini_api_key = os.environ.get("GEMINI_API_KEY")
        
        # Initialize the selected provider
        if self.provider == "openai":
            if not self.openai_api_key:
                raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER is set to 'openai'")
            openai.api_key = self.openai_api_key
            print("�� Using OpenAI as LLM provider")
        elif self.provider == "gemini":
            if not self.gemini_api_key:
                raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER is set to 'gemini'")
            genai.configure(api_key=self.gemini_api_key)
            print("🤖 Using Google Gemini as LLM provider")
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    def parse_resume(self, text: str) -> Dict[str, Any]:
        """Parse resume text using the configured LLM provider"""
        try:
            if self.provider == "openai":
                return self._parse_with_openai(text)
            elif self.provider == "gemini":
                return self._parse_with_gemini(text)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
        except Exception as e:
            print(f"❌ LLM parsing failed: {str(e)}")
            # Fallback to basic parsing
            return self._basic_parse(text)
    
    def _parse_with_openai(self, text: str) -> Dict[str, Any]:
        """Parse resume using OpenAI GPT"""
        prompt = self._get_resume_parsing_prompt(text)
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a resume parser. Extract structured information from resume text and return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.1
        )
        
        content = response.choices[0].message.content
        return self._parse_json_response(content)
    
    def _parse_with_gemini(self, text: str) -> Dict[str, Any]:
        """Parse resume using Google Gemini"""
        prompt = self._get_resume_parsing_prompt(text)
        
        # Try different Gemini models in order of preference
        gemini_models = ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro']
        
        for model_name in gemini_models:
            try:
                print(f"🔄 Trying Gemini model: {model_name}")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                
                if response.text:
                    content = response.text
                    print(f" Successfully used Gemini model: {model_name}")
                    return self._parse_json_response(content)
                    
            except Exception as e:
                print(f" Model {model_name} failed: {str(e)}")
                continue
        
        # If all models fail, raise an exception
        raise Exception("All Gemini models failed to respond")
    
    def _get_resume_parsing_prompt(self, text: str) -> str:
        """Get the prompt for resume parsing"""
        return f"""
        Parse the following resume text and extract structured information. Return a JSON object with the following structure:
        {{
            "fullName": "extracted full name",
            "email": "extracted email",
            "phone": "extracted phone number",
            "location": "extracted location",
            "summary": "extracted professional summary",
            "experience": [
                {{
                    "title": "job title",
                    "company": "company name",
                    "startDate": "start date",
                    "endDate": "end date",
                    "current": false,
                    "description": "job description"
                }}
            ],
            "education": [
                {{
                    "degree": "degree name",
                    "field": "field of study",
                    "institution": "institution name",
                    "graduationYear": "graduation year"
                }}
            ],
            "skills": ["skill1", "skill2", "skill3"],
            "certifications": ["cert1", "cert2"],
            "projects": [
                {{
                    "name": "project name",
                    "description": "project description",
                    "technologies": ["tech1", "tech2"]
                }}
            ]
        }}

        Resume text:
        {text}

        Extract as much information as possible. If a field is not found, use empty string or empty array.
        Return only valid JSON without any additional text or formatting.
        """
    
    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON response from LLM"""
        try:
            # Clean the response to extract JSON
            content = content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            
            content = content.strip()
            
            # Parse JSON
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Raw content: {content}")
            # Return basic structure if JSON parsing fails
            return self._basic_parse("")
    
    def _basic_parse(self, text: str) -> Dict[str, Any]:
        """Basic parsing without LLM (fallback)"""
        import re
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        email = email_match.group() if email_match else ""
        
        # Extract phone
        phone_pattern = r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phone_match = re.search(phone_pattern, text)
        phone = phone_match.group() if phone_match else ""
        
        # Extract skills (basic keywords)
        skill_keywords = [
            'python', 'javascript', 'java', 'react', 'node.js', 'sql', 'mongodb',
            'aws', 'docker', 'kubernetes', 'git', 'html', 'css', 'typescript',
            'angular', 'vue', 'php', 'ruby', 'go', 'rust', 'c++', 'c#', '.net',
            'machine learning', 'ai', 'data science', 'devops', 'cloud computing'
        ]
        skills = [skill for skill in skill_keywords if skill.lower() in text.lower()]
        
        return {
            "fullName": "",
            "email": email,
            "phone": phone,
            "location": "",
            "summary": "",
            "experience": [],
            "education": [],
            "skills": skills,
            "certifications": [],
            "projects": []
        }
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the current LLM provider"""
        return {
            "provider": self.provider,
            "available": self.openai_api_key is not None or self.gemini_api_key is not None,
            "openai_configured": self.openai_api_key is not None,
            "gemini_configured": self.gemini_api_key is not None
        } 