import json
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# --- Load Environment Variables ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# 1. Define the strict JSON schema for Industry Context
class IndustryTrend(BaseModel):
    trend_name: str = Field(description="A short name for the trend (e.g., 'Rising Delinquency Rates', 'AI-Driven Underwriting').")
    description: str = Field(description="A 1-2 sentence description of how this trend is impacting the sector right now.")

class IndustryContext(BaseModel):
    industry_name: str = Field(description="The specific sector the company operates in (e.g., 'Subprime Auto Finance', 'SaaS Healthcare').")
    macro_paragraph: str = Field(description="A highly factual, 3-5 sentence executive summary of the current macroeconomic conditions, challenges, and technological shifts facing this specific industry in 2026.")
    key_trends: list[IndustryTrend] = Field(description="A list of 3-4 major trends currently reshaping this sector.")

def generate_industry_context(folder_path: str, company_name: str):
    # Updated to follow prefix-free naming conventions
    input_json_path = os.path.join(folder_path, "llm_insights.json")
    output_json_path = os.path.join(folder_path, "industry_context.json")
    
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
        response_schema=IndustryContext,
        temperature=0.3 # Slightly higher to allow for fluid paragraph generation while staying factual
    )
    
    # 2. The Prompt: Force 2026 context and AI implications
    prompt = f"""
    Review the following context for our target company, {company_name}: 
    {json.dumps(company_context)}
    
    Identify the precise industry and market sector this company operates in. Then, use Google Search Grounding to research the current state of that specific industry as of 2026.
    
    Please provide:
    1. The exact name of the industry.
    2. A `macro_paragraph`: A polished, executive-level paragraph (3-5 sentences) summarizing the macroeconomic headwinds, affordability/pricing pressures, and competitive dynamics facing this industry in 2026. 
    3. `key_trends`: Extract 3-4 distinct trends currently shaping the market. At least one of these trends MUST focus on how Artificial Intelligence is being deployed within this specific sector (e.g., AI in collections, automated underwriting, predictive customer service).
    
    Ensure all insights reflect current 2026 data.
    """
    
    print(f"\nQuerying Gemini 3.1 Pro Preview with Search Grounding for 2026 industry context on {company_name}...")
    
    try:
        response = client.models.generate_content(
            model="gemini-3.1-pro-preview",
            contents=prompt,
            config=config
        )
        
        with open(output_json_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
            
        print(f"Successfully saved industry context data to: {output_json_path}")
        
    except Exception as e:
        print(f"  [!] Error generating industry context: {e}")

if __name__ == "__main__":
    if os.path.exists("config.json"):
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        
        target_folder = config.get("domain_folder")
        company_name = config.get("proper_company_name", target_folder.split('.')[0].capitalize())
        
        print(f"[+] Automating industry context extraction for: {company_name}")
        generate_industry_context(target_folder, company_name)
    else:
        print("Error: config.json not found. Run 00_run_pipeline.py first.")