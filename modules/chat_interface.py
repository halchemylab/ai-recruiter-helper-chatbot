import streamlit as st
from typing import Dict, List
import openai
from .job_search import JobSearcher
from .company_research import CompanyResearcher
from .application_tracker import ApplicationTracker
from dotenv import load_dotenv
import os

class ChatInterface:
    def __init__(self):
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        # Initialize OpenAI API key
        load_dotenv()
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise ValueError("OpenAI API key not found in environment variables")

    def display_chat(self):
        """Display the chat messages in the Streamlit interface"""
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

    def process_user_input(self, 
                          user_input: str, 
                          job_searcher: JobSearcher,
                          company_researcher: CompanyResearcher,
                          application_tracker: ApplicationTracker):
        """Process user input and generate appropriate response"""
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Analyze user intent
        intent = self._analyze_intent(user_input)
        
        try:
            # Handle different user intents
            if intent["type"] == "search_jobs":
                response = self._handle_job_search(job_searcher)
            elif intent["type"] == "company_info":
                response = self._handle_company_research(company_researcher, intent["company"])
            elif intent["type"] == "track_application":
                response = self._handle_application_tracking(application_tracker, intent["data"])
            elif intent["type"] == "get_stats":
                response = self._handle_statistics(application_tracker)
            else:
                response = self._generate_general_response(user_input)

            # Add assistant's response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
            
        except Exception as e:
            error_msg = f"I apologize, but I encountered an error: {str(e)}"
            st.session_state.messages.append({"role": "assistant", "content": error_msg})

    def _analyze_intent(self, user_input: str) -> Dict:
        """Analyze user input to determine their intent"""
        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": """You are an intent classifier for a job search assistant.
                     Return a JSON object with these fields:
                     - type: one of [search_jobs, company_info, track_application, get_stats, general]
                     - company: company name (for company_info intent)
                     - data: application data (for track_application intent)
                     
                     Example responses:
                     {"type": "search_jobs"}
                     {"type": "company_info", "company": "Microsoft"}
                     {"type": "track_application", "data": {"position": "Developer", "company": "Google"}}"""},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.3
            )
            
            # Parse the response as a structured intent object
            intent_text = response.choices[0].message.content.strip()
            import json
            try:
                return json.loads(intent_text)
            except json.JSONDecodeError:
                # Fallback parsing for non-JSON responses
                intent_text = intent_text.lower()
                if "search" in intent_text and "job" in intent_text:
                    return {"type": "search_jobs"}
                elif "company" in intent_text:
                    company = self._extract_company_name(intent_text)
                    return {"type": "company_info", "company": company}
                elif "application" in intent_text or "track" in intent_text:
                    data = self._extract_application_data(intent_text)
                    return {"type": "track_application", "data": data}
                elif "stat" in intent_text:
                    return {"type": "get_stats"}
                
            return {"type": "general"}
                
        except Exception as e:
            print(f"Intent analysis error: {str(e)}")
            return {"type": "general"}

    def _handle_job_search(self, job_searcher: JobSearcher) -> str:
        """Handle job search requests"""
        if not st.session_state.get('resume_data'):
            return "Please upload your resume first so I can help you find relevant jobs."
        
        filters = {
            "location": st.session_state.get('location', ''),
            "remote": st.session_state.get('remote', False),
            "min_salary": st.session_state.get('min_salary', 0)
        }
        
        jobs = job_searcher.search_jobs(st.session_state.resume_data, filters)
        
        if not jobs:
            return "I couldn't find any matching jobs at the moment. Try adjusting your search criteria."
        
        # Format job results
        response = "Here are the top matching jobs for your profile:\n\n"
        for job in jobs:
            response += f"""
🎯 {job['title']}
🏢 {job['company']}
📍 {job['location']}
💰 {job['salary']}
\n{job['description']}\n
🔗 {job['url']}\n
Match Score: {job.get('match_score', 'N/A')}\n
-------------------\n"""
        
        return response

    def _handle_company_research(self, company_researcher: CompanyResearcher, company_name: str) -> str:
        """Handle company research requests"""
        import asyncio
        
        # Get company information
        company_info = asyncio.run(company_researcher.research_company(company_name))
        
        if "error" in company_info:
            return f"Sorry, I couldn't gather information about {company_name} at the moment."
        
        # Format company information
        response = f"""
Here's what I found about {company_name}:

📊 Company Overview:
{company_info['overview']}

🔄 Recent Developments:
{company_info['recent_developments']}

👥 Culture and Benefits:
{company_info['culture_and_benefits']}
"""
        return response

    def _handle_application_tracking(self, application_tracker: ApplicationTracker, data: Dict) -> str:
        """Handle application tracking requests"""
        if "add" in data:
            result = application_tracker.add_application(data["add"])
            return f"Application for {result['position']} at {result['company']} has been tracked."
        elif "update" in data:
            result = application_tracker.update_application(data["update"]["id"], data["update"]["changes"])
            return f"Application has been updated successfully."
        elif "view" in data:
            apps = application_tracker.get_all_applications(data.get("filters"))
            return self._format_applications(apps)
        
        return "I'm not sure what you want to do with the application. Please specify if you want to add, update, or view applications."

    def _handle_statistics(self, application_tracker: ApplicationTracker) -> str:
        """Handle statistics requests"""
        stats = application_tracker.get_application_statistics()
        
        response = f"""
📊 Application Statistics:

Total Applications: {stats['total_applications']}

Status Breakdown:
"""
        for status, count in stats['status_breakdown'].items():
            response += f"- {status}: {count}\n"
        
        response += f"\nSuccess Rate: {stats['success_rate']*100:.1f}%"
        
        return response

    def _generate_general_response(self, user_input: str) -> str:
        """Generate a general response for other types of queries"""
        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": """You are a helpful job search assistant. Help users with:
                    1. Finding jobs (suggest using keywords like 'search', 'find jobs', 'looking for positions')
                    2. Researching companies (suggest mentioning company names)
                    3. Tracking applications (suggest 'track application', 'update status', 'view applications')
                    4. Viewing statistics (suggest 'show stats', 'view progress')
                    
                    If the user's intent is unclear, guide them to these features."""},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return """I can help you with:
1. Finding jobs - just say "search for jobs" or mention the type of position you're looking for
2. Researching companies - mention a company name you want to learn about
3. Tracking applications - try "track application" or "view my applications"
4. Viewing statistics - say "show my application stats"

What would you like to know?"""

    @staticmethod
    def _extract_company_name(intent_analysis: str) -> str:
        """Extract company name from intent analysis"""
        # Simple extraction - can be enhanced with more sophisticated NLP
        if "company:" in intent_analysis.lower():
            return intent_analysis.split("company:")[1].strip().split()[0]
        return ""

    @staticmethod
    def _extract_application_data(intent_analysis: str) -> Dict:
        """Extract application data from intent analysis"""
        # Simple extraction - can be enhanced with more sophisticated NLP
        data = {}
        if "add application" in intent_analysis.lower():
            data["add"] = {}
        elif "update application" in intent_analysis.lower():
            data["update"] = {"id": None, "changes": {}}
        elif "view applications" in intent_analysis.lower():
            data["view"] = True
        return data

    @staticmethod
    def _format_applications(applications: List[Dict]) -> str:
        """Format applications list for display"""
        if not applications:
            return "No applications found."
            
        response = "Here are your tracked applications:\n\n"
        for app in applications:
            response += f"""
📝 {app['position']} at {app['company']}
Status: {app['status']}
Applied: {app['applied_date']}
Last Updated: {app['last_updated']}
"""
            if app['notes']:
                response += f"Notes: {app['notes']}\n"
            response += "-------------------\n"
            
        return response