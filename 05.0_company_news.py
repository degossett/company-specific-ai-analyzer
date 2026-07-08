import json
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# --- Load Environment Variables ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# 1. Define our strict JSON schema for News
class NewsItem(BaseModel):
    headline: str = Field(description="The headline of the news article or press release.")
    date: str = Field(description="The publication date of the news (Format: YYYY-MM-DD or Month DD, YYYY).")
    url: str = Field(description="The exact, working URL to the full article or press release.")
    summary: str = Field(description="A brief one to two sentence summary of the news event.")
    source_type: str = Field(description="Indicate if this is from 'Internal Website' or 'External News'.")

class CompanyNews(BaseModel):
    # This description instructs Pydantic/Gemini to keep it in order
    news_items: list[NewsItem] = Field(
        description="A list of up to 10 of the most recent news events or press releases, sorted chronologically from newest to oldest."
    )

def find_news(folder_path: str, company_name: str):
    # Updated to follow prefix-free naming conventions
    input_json_path = os.path.join(folder_path, "llm_insights.json")
    output_json_path = os.path.join(folder_path, "news.json")
    
    if not os.path.exists(input_json_path):
        print(f"Error: Could not find '{input_json_path}'. Please check your pipeline order.")
        return

    print(f"Reading insights from: {input_json_path}")
    with open(input_json_path, 'r', encoding='utf-8') as f:
        company_context = json.load(f)
    
    # Extract the domain to use the site: operator
    domain = folder_path.strip("/\\")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found. Please check your .env file.")
        return
        
    client = genai.Client(api_key=api_key)
    search_tool = types.Tool(google_search=types.GoogleSearch())
    
    config = types.GenerateContentConfig(
        tools=[search_tool],
        response_mime_type="application/json",
        response_schema=CompanyNews,
        temperature=0.1 # Keep it low for structural and factual precision
    )
    
    # 2. Optimized prompt directing both internal search and Google News style monitoring
    prompt = f"""
    Review the following context for our target company, {company_name}: {json.dumps(company_context)}
    
    Use Google Search to act as a real-time financial and corporate news crawler for {company_name}. 
    Find up to 10 of the most recent and significant news events, press releases, or media mentions regarding this company.
    
    Execute your searches to explicitly find and cross-reference:
    1. Internal coverage: Search 'site:{domain}' to find recent press rooms, blogs, or news updates direct from the company.
    2. External coverage: Search major news aggregators, Google News, financial hubs, and PR wires for recent articles mentioning {company_name}.
    
    CRITICAL INSTRUCTIONS:
    - Prioritize recent developments.
    - Organize the final JSON `news_items` list in strict chronological order, starting with the newest item first.
    - Ensure all links provided are active, direct source URLs.
    """
    
    print(f"Querying Gemini 3.1 Pro Preview with Search Grounding for chronological news updates on {company_name}...")
    
    response = client.models.generate_content(
        model="gemini-3.1-pro-preview",
        contents=prompt,
        config=config
    )
    
    with open(output_json_path, 'w', encoding='utf-8') as f:
        f.write(response.text)
        
    print(f"Successfully saved chronological news data to: {output_json_path}")

if __name__ == "__main__":
    if os.path.exists("config.json"):
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        
        target_folder = config.get("domain_folder")
        company_name = config.get("proper_company_name", target_folder.split('.')[0].capitalize())
        print(f"[+] Automating real-time news retrieval for: {company_name}")
        find_news(target_folder, company_name)
    else:
        print("Error: config.json not found. Run 00_run_pipeline.py first.")