# My Helpful AI Recruiter

An AI-powered Streamlit chatbot designed to assist users in their job search by recommending suitable positions, conducting company research, and tracking job applications.

## Features

- **Resume Analysis**: Upload and analyze resumes to extract key skills, experiences, and qualifications
- **Smart Job Search**: Get personalized job recommendations based on your resume and preferences
- **Company Research**: Automated gathering of company information, culture, and recent developments
- **Application Tracking**: Track and manage your job applications with status updates
- **Secure Data Handling**: Protected storage of personal information and API keys

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file based on `.env.template` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   DATABASE_PATH=./data/applications.db
   ```

## Usage

1. Start the application:
   ```bash
   streamlit run app.py
   ```

2. Upload your resume when prompted

3. Use the chatbot to:
   - Search for jobs matching your profile
   - Research companies
   - Track your job applications
   - View application statistics

## Commands

Here are some example commands you can use with the chatbot:

- "Find jobs matching my profile"
- "Tell me about [Company Name]"
- "Track my application for [Position] at [Company]"
- "Show me my application statistics"
- "Update application status for [Company]"

## Project Structure

```
├── app.py                 # Main Streamlit application
├── requirements.txt       # Project dependencies
├── .env                   # Environment variables (create from .env.template)
├── data/                  # Data storage directory
│   └── applications.json  # Job applications database
└── modules/              
    ├── resume_parser.py        # Resume parsing functionality
    ├── job_search.py          # Job search and recommendation
    ├── company_research.py    # Company information gathering
    ├── application_tracker.py # Application tracking system
    └── chat_interface.py     # Chat interface handling
```

## Security

- API keys and sensitive data are stored in environment variables
- User data is stored locally in JSON format
- No personal information is shared with external services except as needed for job searches

## Dependencies

- streamlit
- openai
- python-docx
- python-dotenv
- pandas
- requests
- aiohttp
- tqdm

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.