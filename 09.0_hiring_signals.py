import json
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# --- Load Environment Variables ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# 1. Define the strict JSON schema for Hiring Signals
class TechRole(BaseModel):
    job_title: str = Field(description="The title of the open position (e.g., 'Machine Learning Engineer', 'Data Scientist').")
    url: str = Field(description="A direct link to the job posting.")
    focus_area: str = Field(description="A brief 1-sentence summary of what this role focuses on (e.g., 'Building generative AI models', 'Maintaining legacy backend servers').")

class HiringSignals(BaseModel):
    is_hiring_tech: bool = Field(description="True if they have open software, data, or engineering roles. False otherwise.")
    hiring_summary: str = Field(description="A 2-3 sentence executive summary of their current tech hiring velocity. Are they aggressively hiring AI talent, maintaining legacy systems, or showing zero tech hiring footprint?")
    open_roles: list[TechRole] = Field(description="A list of up to 5 relevant open technical, engineering, or AI-related roles.")

def find_hiring_signals(folder_path: str, company_name: str):
    output_json_path = os.path.join(folder_path, "hiring_signals.json")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found. Please check your .env file.")
        return
        
    client = genai.Client(api_key=api_key)
    search_tool = types.Tool(google_search=types.GoogleSearch())
    
    config = types.GenerateContentConfig(
        tools=[search_tool],
        response_mime_type="application/json",
        response_schema=HiringSignals,
        temperature=0.2 
    )
    
    # 2. Prompt: Force Gemini to use advanced job board search operators
    prompt = f"""
    Use Google Search Grounding to audit the current tech and engineering hiring footprint for the company: {company_name}.
    
    CRITICAL INSTRUCTIONS:
    Do not just search their homepage. Use advanced search operators to hunt across massive job aggregators and applicant tracking systems. 
    Examples of good search queries:
    - "{company_name}" (AI OR "machine learning" OR engineer OR data) jobs
    - site:linkedin.com/jobs/view "{company_name}"
    - site:greenhouse.io "{company_name}"
    - site:jobs.lever.co "{company_name}"
    
    Please provide:
    1. A boolean flag indicating if they are currently hiring any software, data, or technical talent.
    2. A `hiring_summary` assessing their modernization trajectory based on these roles (e.g., are they hiring AI visionaries or just IT support desk?).
    3. Up to 5 specific `open_roles` with direct URLs. Prioritize AI, machine learning, data science, and advanced engineering roles over general IT.
    """
    
    print(f"\nQuerying Gemini 3.1 Pro Preview with Search Grounding for tech hiring signals at {company_name}...")
    
    try:
        response = client.models.generate_content(
            model="gemini-3.1-pro-preview",
            contents=prompt,
            config=config
        )
        
        # Clean up any markdown code block wrappers if Gemini included them
        clean_text = response.text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        elif clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()

        with open(output_json_path, 'w', encoding='utf-8') as f:
            f.write(clean_text)
            
        print(f"Successfully saved hiring signals data to: {output_json_path}")
        
    except Exception as e:
        print(f"  [!] Error generating hiring signals: {e}")

if __name__ == "__main__":
    if os.path.exists("config.json"):
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        
        target_folder = config.get("domain_folder")
        company_name = config.get("proper_company_name", target_folder.split('.')[0].capitalize())
        
        print(f"[+] Automating hiring signal extraction for: {company_name}")
        find_hiring_signals(target_folder, company_name)
    else:
        print("Error: config.json not found. Run 00_run_pipeline.py first.")