from llama_parse import LlamaParse
import os
from typing import Dict, Any
import io
from dotenv import load_dotenv

class ResumeParser:
    def __init__(self):
        load_dotenv()
        self.llama_cloud_api_key = os.getenv("LLAMA_CLOUD_API_KEY")
        self.llama_cloud_base_url = os.getenv("LLAMA_CLOUD_BASE_URL")
        
        if not self.llama_cloud_api_key:
            raise ValueError("LLAMA_CLOUD_API_KEY environment variable is not set")

    def parse(self, file) -> Dict[str, Any]:
        """Parse resume file and extract relevant information using LlamaParse."""
        try:
            # Initialize LlamaParse with resume-specific configuration
            parser = LlamaParse(
                api_key=self.llama_cloud_api_key,
                base_url=self.llama_cloud_base_url,
                result_type="markdown",
                content_guideline_instruction="This is a resume, gather related facts together and format as structured data with these sections: SKILLS, EXPERIENCE, EDUCATION"
            )
            
            # Handle both file-like objects and bytes
            if hasattr(file, 'read'):
                file_content = file.read()
            else:
                file_content = file
                
            # Save content temporarily if needed
            temp_file = None
            if isinstance(file_content, bytes):
                temp_file = "temp_resume"
                with open(temp_file, "wb") as f:
                    f.write(file_content)
                document = parser.load_data(temp_file)
                os.remove(temp_file)
            else:
                document = parser.load_data(io.BytesIO(file_content))

            # Extract sections from the parsed markdown
            parsed_data = {
                'skills': self._extract_section(document.text, "SKILLS"),
                'experience': self._extract_section(document.text, "EXPERIENCE"),
                'education': self._extract_section(document.text, "EDUCATION"),
                'raw_text': document.text
            }
            
            return parsed_data
        except Exception as e:
            raise Exception(f"Error parsing resume: {str(e)}")

    def _extract_section(self, text: str, section_name: str) -> list:
        """Extract a specific section from the parsed markdown text."""
        try:
            # Find the section in the markdown text
            section_start = text.find(f"# {section_name}")
            if section_start == -1:
                return []
            
            # Find the next section or end of text
            next_section = text.find("# ", section_start + 2)
            if next_section == -1:
                section_content = text[section_start:]
            else:
                section_content = text[section_start:next_section]
            
            # Split into bullet points and clean up
            bullet_points = [
                line.strip('- ').strip() 
                for line in section_content.split('\n') 
                if line.strip().startswith('-')
            ]
            
            return bullet_points
        except Exception:
            return []