import streamlit as st
import os
from dotenv import load_dotenv
import openai
from modules.resume_parser import ResumeParser
from modules.job_search import JobSearcher
from modules.company_research import CompanyResearcher
from modules.application_tracker import ApplicationTracker
from modules.chat_interface import ChatInterface

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OpenAI API key not found in environment variables")

class AIRecruiterApp:
    def __init__(self):
        self.initialize_session_state()
        self.resume_parser = ResumeParser()
        self.job_searcher = JobSearcher()
        self.company_researcher = CompanyResearcher()
        self.application_tracker = ApplicationTracker()
        self.chat_interface = ChatInterface()

    def initialize_session_state(self):
        if 'resume_data' not in st.session_state:
            st.session_state.resume_data = None
        if 'job_history' not in st.session_state:
            st.session_state.job_history = []
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []

    def handle_file_upload(self, file):
        """Handle resume file upload with proper error handling"""
        try:
            if file.size > 5 * 1024 * 1024:  # 5MB limit
                st.error("File size too large. Please upload a file smaller than 5MB.")
                return None
                
            # Check file type
            if not file.name.lower().endswith(('.doc', '.docx')):
                st.error("Please upload only DOC or DOCX files.")
                return None
                
            return self.resume_parser.parse(file)
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            return None

    def generate_welcome_message(self, resume_data):
        """Generate a personalized welcome message based on resume analysis"""
        try:
            current_company = None
            suitable_roles = []
            
            # Extract current company from most recent experience
            if resume_data.get('experience'):
                most_recent = resume_data['experience'][0]
                # Look for company name in the most recent experience
                companies = [word for word in most_recent.split() if word.isupper() and len(word) > 1]
                if companies:
                    current_company = companies[0]
            
            # Analyze skills to suggest suitable roles
            skills = resume_data.get('skills', [])
            if skills:
                response = openai.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a career advisor. Based on the skills provided, suggest 2-3 most suitable job roles. Return them as a comma-separated list."},
                        {"role": "user", "content": f"Skills: {', '.join(skills)}"}
                    ],
                    temperature=0.7
                )
                suitable_roles = [role.strip() for role in response.choices[0].message.content.split(',')]
            
            # Construct welcome message
            welcome_msg = "👋 Welcome! Based on your resume, "
            if current_company:
                welcome_msg += f"I see you're currently at {current_company}. "
            
            if suitable_roles:
                welcome_msg += f"Your skills make you a strong candidate for roles like {', '.join(suitable_roles)}. "
            
            welcome_msg += "\nHow can I help you with your job search today?"
            
            return welcome_msg
        except Exception as e:
            print(f"Error generating welcome message: {str(e)}")
            return "👋 Welcome! I've analyzed your resume. How can I help you with your job search today?"

    def main(self):
        st.title("My Helpful AI Recruiter")
        
        # Sidebar for user controls
        with st.sidebar:
            st.header("Upload Resume")
            resume_file = st.file_uploader(
                "Upload your resume (DOC/DOCX)", 
                type=['doc', 'docx'],
                help="Upload your resume in DOC or DOCX format (max 5MB)"
            )
            
            if resume_file and (st.session_state.resume_data is None):
                with st.spinner("Analyzing your resume..."):
                    parsed_data = self.handle_file_upload(resume_file)
                    if parsed_data:
                        st.session_state.resume_data = parsed_data
                        welcome_message = self.generate_welcome_message(parsed_data)
                        st.session_state.messages = [{"role": "assistant", "content": welcome_message}]
                        st.success("Resume analyzed successfully!")

            # Job search filters
            st.header("Job Search Filters")
            location = st.text_input("Location", "")
            remote = st.checkbox("Remote Work")
            min_salary = st.number_input("Minimum Salary", min_value=0, value=0)
            
        # Main content area
        if st.session_state.resume_data is None:
            st.info("Please upload your resume to get started!")
            return

        # Chat interface
        self.chat_interface.display_chat()
        user_input = st.chat_input("Type your question here...")
        
        if user_input:
            self.chat_interface.process_user_input(
                user_input,
                self.job_searcher,
                self.company_researcher,
                self.application_tracker
            )

        # Application tracking section
        with st.expander("View Application History"):
            self.application_tracker.display_applications()

if __name__ == "__main__":
    app = AIRecruiterApp()
    app.main()