import os
from datetime import datetime, timedelta
from typing import List, Dict
import openai
from dotenv import load_dotenv

class JobSearcher:
    def __init__(self):
        load_dotenv()
        openai.api_key = os.getenv("OPENAI_API_KEY")

    def search_jobs(self, resume_data: Dict, filters: Dict) -> List[Dict]:
        """
        Search for jobs based on resume data and user filters
        """
        # Construct the search query based on resume and filters
        query = self._construct_search_query(resume_data, filters)
        
        try:
            # Use OpenAI to get job recommendations
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a job search assistant. Search for relevant jobs based on the candidate's profile and return exactly 3 most relevant positions from the last 24 hours."},
                    {"role": "user", "content": query}
                ],
                temperature=0.7
            )
            
            # Parse the response into structured job listings
            jobs = self._parse_job_listings(response.choices[0].message.content)
            return self._score_and_rank_jobs(jobs, resume_data)
        except Exception as e:
            print(f"Error in job search: {str(e)}")
            return []

    def _construct_search_query(self, resume_data: Dict, filters: Dict) -> str:
        """Construct a search query based on resume data and filters"""
        skills = ', '.join(resume_data.get('skills', [])[:5])  # Top 5 skills
        experience = resume_data.get('experience', [])[0] if resume_data.get('experience') else ""
        
        query = f"""
        Find jobs matching this candidate profile:
        Skills: {skills}
        Recent Experience: {experience}
        Location: {filters.get('location', 'Any')}
        Remote: {'Yes' if filters.get('remote') else 'No preference'}
        Minimum Salary: ${filters.get('min_salary', 0):,}
        
        Please format each job as:
        Title: [job title]
        Company: [company name]
        Location: [location]
        Salary: [salary range if available]
        Description: [brief job description]
        URL: [job posting URL]
        """
        return query

    def _parse_job_listings(self, response_text: str) -> List[Dict]:
        """Parse the OpenAI response into structured job listings"""
        jobs = []
        current_job = {}
        
        for line in response_text.split('\n'):
            line = line.strip()
            if not line:
                if current_job:
                    jobs.append(current_job.copy())
                    current_job = {}
                continue
                
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                current_job[key] = value
                
        if current_job:
            jobs.append(current_job)
            
        return jobs

    def _score_and_rank_jobs(self, jobs: List[Dict], resume_data: Dict) -> List[Dict]:
        """Score and rank jobs based on match with resume"""
        for job in jobs:
            score = 0
            job_desc = job.get('description', '').lower()
            
            # Score based on skills match
            for skill in resume_data.get('skills', []):
                if skill.lower() in job_desc:
                    score += 1
                    
            # Score based on experience match
            for exp in resume_data.get('experience', []):
                if any(keyword in job_desc for keyword in exp.lower().split()):
                    score += 0.5
                    
            job['match_score'] = score
            
        return sorted(jobs, key=lambda x: x.get('match_score', 0), reverse=True)