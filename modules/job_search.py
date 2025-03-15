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
                model="gpt-4o-search-preview",  # Using standard GPT-4 model
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
            if "api_key" in str(e).lower():
                print("OpenAI API key error. Please check your .env file has a valid OPENAI_API_KEY")
            elif "model" in str(e).lower():
                print("Model error. Falling back to gpt-3.5-turbo...")
                try:
                    response = openai.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a job search assistant. Search for relevant jobs based on the candidate's profile and return exactly 3 most relevant positions from the last 24 hours."},
                            {"role": "user", "content": query}
                        ],
                        temperature=0.7
                    )
                    jobs = self._parse_job_listings(response.choices[0].message.content)
                    return self._score_and_rank_jobs(jobs, resume_data)
                except Exception as e2:
                    print(f"Fallback error: {str(e2)}")
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
        required_fields = ['title', 'company', 'location', 'description']
        
        for line in response_text.split('\n'):
            line = line.strip()
            if not line:
                if current_job and all(field in current_job for field in required_fields):
                    jobs.append(current_job.copy())
                current_job = {}
                continue
                
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                current_job[key] = value
                
        if current_job and all(field in current_job for field in required_fields):
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

def get_sample_resume_data() -> Dict:
    """Sample resume data for testing"""
    return {
        'skills': ['Python', 'Machine Learning', 'Data Analysis', 'SQL', 'Deep Learning'],
        'experience': [
            'Machine Learning Engineer at TechCorp - Developed and deployed ML models',
            'Data Scientist at DataCo - Performed data analysis and visualization'
        ],
        'education': [
            'MS in Computer Science',
            'BS in Mathematics'
        ]
    }

def test_job_searcher():
    """Test function to demonstrate JobSearcher functionality"""
    # Initialize the JobSearcher
    searcher = JobSearcher()
    
    # Sample filters
    filters = {
        "location": "New York",
        "remote": True,
        "min_salary": 100000
    }
    
    print("\nSearching for jobs...\n")
    
    try:
        # Get job recommendations
        resume_data = get_sample_resume_data()
        results = searcher.search_jobs(resume_data, filters)
        
        # Pretty print the results
        print("Search Results:")
        print("==============")
        
        if not results:
            print("No matching jobs found.")
            return
            
        for job in results:
            print(f"\n🎯 {job['title']}")
            print(f"🏢 {job['company']}")
            print(f"📍 {job['location']}")
            print(f"💰 {job.get('salary', 'Not specified')}")
            print(f"\nDescription:\n{job['description']}\n")
            print(f"Match Score: {job.get('match_score', 'N/A')}")
            print("-" * 50)
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    # Ensure environment variables are loaded
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in environment variables")
    else:
        # Run the test
        test_job_searcher()