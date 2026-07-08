import json
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# --- Load Environment Variables ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# 1. Define the strict JSON schema for Executives
class Executive(BaseModel):
    name: str = Field(description="Full name of the executive.")
    title: str = Field(description="Current job title / corporate role (e.g., CEO, CFO, CTO).")
    tenure: str = Field(description="Estimated start year or length of time with the company. Use 'Unknown' if not found.")
    previous_background: str = Field(description="A 1-2 sentence summary of their notable prior experience or past companies.")
    linkedin_url: str = Field(description="A direct link to their professional LinkedIn profile if found, otherwise an empty string.")

class LeadershipTeam(BaseModel):
    executives: list[Executive] = Field(description="A roster of the key C-suite and executive leaders for the organization.")

def find_leadership(folder_path: str, company_name: str):
    # Updated to follow prefix-free naming conventions
    input_json_path = os.path.join(folder_path, "llm_insights.json")
    output_json_path = os.path.join(folder_path, "leadership.json")
    
    if not os.path.exists(input_json_path):
        print(f"Error: Could not find '{input_json_path}'. Please check your pipeline order.")
        return

    print(f"Reading insights from: {input_json_path}")
    with open(input_json_path, 'r', encoding='utf-8') as f:
        company_context = json.load(f)
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found. Please check your .env file.")
        return
        
    client = genai.Client(api_key=api_key)
    search_tool = types.Tool(google_search=types.GoogleSearch())
    
    config = types.GenerateContentConfig(
        tools=[search_tool],
        response_mime_type="application/json",
        response_schema=LeadershipTeam,
        temperature=0.2 
    )
    
    # Updated Prompt: Dropped the guess-work and injected company_name directly
    prompt = f"""
    Review the following context for our target company, {company_name}: {json.dumps(company_context)}
    
    Use Google Search Grounding to find the current, key executive leadership team (C-Suite, EVPs, SVPs) for {company_name}.
    
    For each executive, identify their name, exact title, tenure/start date with {company_name}, a quick summary of where they worked previously, and their professional LinkedIn profile URL.
    Verify information across reliable business directories, press releases, or official profiles to ensure the leadership team roster is completely current.
    """
    
    print(f"Querying Gemini 3.1 Pro Preview with Search Grounding for executive metadata of {company_name}...")
    
    response = client.models.generate_content(
        model="gemini-3.1-pro-preview",
        contents=prompt,
        config=config
    )
    
    with open(output_json_path, 'w', encoding='utf-8') as f:
        f.write(response.text)
        
    print(f"Successfully saved leadership team data to: {output_json_path}")

if __name__ == "__main__":
    if os.path.exists("config.json"):
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        
        target_folder = config.get("domain_folder")
        company_name = config.get("proper_company_name", target_folder.split('.')[0].capitalize())
        print(f"[+] Automating leadership extraction for: {company_name}")
        find_leadership(target_folder, company_name)
    else:
        print("Error: config.json not found. Run 00_run_pipeline.py first.")