import json
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# --- Load Environment Variables ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# 1. Define the strict JSON schema for Industry AI Context
class AIUseCase(BaseModel):
    use_case: str = Field(description="Name of the AI use case (e.g., 'Automated Underwriting', 'Predictive Maintenance').")
    details: str = Field(description="A 1-2 sentence description of how leading companies are applying this right now.")

class IndustryAI(BaseModel):
    ai_paragraph: str = Field(description="A highly compelling, 3-5 sentence executive paragraph summarizing the current state of Artificial Intelligence adoption in this specific industry in 2026, and why it is critical for survival/growth.")
    use_cases: list[AIUseCase] = Field(description="A list of 2-3 specific, real-world examples of AI deployment in this sector.")

def generate_industry_ai(folder_path: str, company_name: str):
    input_json_path = os.path.join(folder_path, "llm_insights.json")
    output_json_path = os.path.join(folder_path, "industry_ai.json")
    
    if not os.path.exists(input_json_path):
        print(f"Error: Could not find '{input_json_path}'. Please run the core evaluation script first.")
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
        response_schema=IndustryAI,
        temperature=0.1 # LOWERED: Forces stricter adherence to JSON formatting
    )
    
    prompt = f"""
    Review the following business context for our target company, {company_name}:
    {json.dumps(company_context)}
    
    First, identify the precise industry and market sector this company operates in based on the context.
    Then, use Google Search Grounding to research the current state of Artificial Intelligence (including Generative AI, machine learning, and automation) within that specific sector as of 2026.
    
    Please provide:
    1. An `ai_paragraph`: A polished, executive-level paragraph (3-5 sentences) summarizing how AI is actively transforming this specific industry. Discuss what leading competitors are doing, the ROI they are seeing, and why adopting AI is no longer optional.
    2. `use_cases`: Extract 2-3 specific, real-world ways AI is being applied right now in this industry sector.
    
    Ensure all insights reflect current 2026 technological trends. Do not include any placeholder footnotes or citations like [1].
    """
    
    print(f"\nQuerying Gemini 3.1 Pro Preview with Search Grounding for AI trends related to {company_name}...")
    
    # THE RETRY LOOP: Try up to 3 times to get valid JSON
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.1-pro-preview",
                contents=prompt,
                config=config
            )
            
            # Clean up markdown code block wrappers
            clean_text = response.text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            elif clean_text.startswith("```"):
                clean_text = clean_text[3:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
            clean_text = clean_text.strip()

            # SELF-HEALING CHECK: Force Python to parse it. If it fails, it jumps to the 'except' block.
            json.loads(clean_text) 

            # If it passes the test, save the pure JSON text and break the loop
            with open(output_json_path, 'w', encoding='utf-8') as f:
                f.write(clean_text)
                
            print(f"Successfully saved industry AI data to: {output_json_path}")
            break # Success! Exit the loop.
            
        except json.JSONDecodeError:
            print(f"  [!] Attempt {attempt + 1} yielded malformed JSON. Retrying...")
        except Exception as e:
            print(f"  [!] Error generating industry AI context: {e}")
            break # If it's an API failure (not a JSON failure), exit to prevent an infinite loop.

if __name__ == "__main__":
    if os.path.exists("config.json"):
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        
        target_folder = config.get("domain_folder")
        company_name = config.get("proper_company_name", target_folder.split('.')[0].capitalize())
        
        print(f"[+] Automating industry AI context extraction for: {company_name}")
        generate_industry_ai(target_folder, company_name)
    else:
        print("Error: config.json not found. Run 00_run_pipeline.py first.")