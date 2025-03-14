import asyncio
import aiohttp
import openai
from typing import Dict, Optional
import os
from dotenv import load_dotenv

class CompanyResearcher:
    def __init__(self):
        load_dotenv()
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.company_cache = {}
        if os.name == 'nt':  # Windows specific event loop policy
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    async def research_company(self, company_name: str) -> Dict:
        """
        Asynchronously gather information about a company
        """
        # Check cache first
        if company_name in self.company_cache:
            return self.company_cache[company_name]

        try:
            # Use a timeout context to ensure connections are properly closed
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                tasks = [
                    self._get_company_overview(session, company_name),
                    self._get_recent_news(session, company_name),
                    self._get_employee_reviews(session, company_name)
                ]
                results = await asyncio.gather(*tasks)

            # Combine and analyze the gathered information
            company_info = self._analyze_company_data(*results)
            
            # Cache the results
            self.company_cache[company_name] = company_info
            return company_info

        except Exception as e:
            print(f"Error researching company {company_name}: {str(e)}")
            return {
                "company_name": company_name,
                "error": "Unable to gather company information",
                "status": "failed"
            }

    async def _get_company_overview(self, session: aiohttp.ClientSession, company_name: str) -> Dict:
        """Get general company information using OpenAI"""
        try:
            response = await openai.AsyncOpenAI().chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a company research assistant. Provide key information about the company."},
                    {"role": "user", "content": f"Provide a brief overview of {company_name}, including industry, size, and key business areas. Summarize into 1-3 sentences. Don't output sources"}
                ]
            )
            return {"overview": response.choices[0].message.content}
        except Exception as e:
            print(f"Error in company overview: {str(e)}")
            if "api_key" in str(e).lower():
                return {"overview": "API key error - please check your OpenAI API key configuration"}
            return {"overview": f"Company overview not available: {str(e)}"}

    async def _get_recent_news(self, session: aiohttp.ClientSession, company_name: str) -> Dict:
        """Get recent news about the company"""
        try:
            response = await openai.AsyncOpenAI().chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a news research assistant. Provide recent developments about the company."},
                    {"role": "user", "content": f"What are the most significant recent developments or news about {company_name} in the last 6 months? Summarize into 1-3 sentences. Don't output Sources."}
                ]
            )
            return {"recent_news": response.choices[0].message.content}
        except Exception as e:
            print(f"Error in recent news: {str(e)}")
            if "api_key" in str(e).lower():
                return {"recent_news": "API key error - please check your OpenAI API key configuration"}
            return {"recent_news": f"Recent news not available: {str(e)}"}

    async def _get_employee_reviews(self, session: aiohttp.ClientSession, company_name: str) -> Dict:
        """Get employee reviews and culture information"""
        try:
            response = await openai.AsyncOpenAI().chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a workplace culture analyst. Provide insights about the company's work culture."},
                    {"role": "user", "content": f"What is known about {company_name}'s work culture, benefits, and employee satisfaction? Summarize into 1-3 sentences. Don't output sources."}
                ]
            )
            return {"culture": response.choices[0].message.content}
        except Exception as e:
            print(f"Error in employee reviews: {str(e)}")
            if "api_key" in str(e).lower():
                return {"culture": "API key error - please check your OpenAI API key configuration"}
            return {"culture": f"Culture information not available: {str(e)}"}

    def _analyze_company_data(self, overview: Dict, news: Dict, culture: Dict) -> Dict:
        """Combine and analyze all gathered company information"""
        return {
            "overview": overview.get("overview", "Not available"),
            "recent_developments": news.get("recent_news", "Not available"),
            "culture_and_benefits": culture.get("culture", "Not available"),
            "analysis_timestamp": asyncio.get_event_loop().time(),
            "data_freshness": "24h"
        }

    def get_cached_research(self, company_name: str) -> Optional[Dict]:
        """Retrieve cached company research if available"""
        return self.company_cache.get(company_name)

    def clear_cache(self, company_name: Optional[str] = None):
        """Clear research cache for a specific company or all companies"""
        if company_name:
            self.company_cache.pop(company_name, None)
        else:
            self.company_cache.clear()

async def test_researcher():
    """Test function to demonstrate CompanyResearcher functionality"""
    # Initialize the CompanyResearcher
    researcher = CompanyResearcher()
    
    # Test with a well-known company
    company_name = "Microsoft"
    print(f"\nResearching {company_name}...\n")
    
    try:
        # Get company research
        result = await researcher.research_company(company_name)
        
        # Pretty print the results
        print("Research Results:")
        print("================")
        print("\nCompany Overview:")
        print(result['overview'])
        print("\nRecent Developments:")
        print(result['recent_developments'])
        print("\nCulture and Benefits:")
        print(result['culture_and_benefits'])
        
        # Test cache
        print("\nTesting cache...")
        cached_result = researcher.get_cached_research(company_name)
        print(f"Cache hit successful: {cached_result is not None}")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    # Run the test function when the file is executed directly
    asyncio.run(test_researcher())