import json
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# --- Load Environment Variables ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# 1. Define our strict JSON schema
class Peer(BaseModel):
    company_name: str = Field(description="Name of the peer organization.")
    homepage_url: str = Field(description="The active homepage URL of the company.")
    description: str = Field(description="A brief description of the company, strictly no more than two sentences.")

class PeerGroup(BaseModel):
    peers: list[Peer] = Field(description="A list of up to 8 peer organizations that are direct competitors.")

# Updated to accept the company_name directly
def find_peers(folder_path: str, company_name: str):
    # Construct paths using the new prefix-free naming convention
    input_json_path = os.path.join(folder_path, "llm_insights.json")
    output_json_path = os.path.join(folder_path, "peers.json")
    
    # Check if the input file actually exists inside the provided folder
    if not os.path.exists(input_json_path):
        print(f"Error: Could not find '{input_json_path}'. Please check your pipeline order.")
        return

    # 2. Load the existing company context
    print(f"Reading insights from: {input_json_path}")
    with open(input_json_path, 'r', encoding='utf-8') as f:
        company_context = json.load(f)
    
    # 3. Initialize the Gemini client explicitly using the loaded key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found. Please check your .env file.")
        return
        
    client = genai.Client(api_key=api_key)
    
    # 4. Enable Google Search Grounding
    search_tool = types.Tool(google_search=types.GoogleSearch())
    
    # Configure the request to return structured JSON grounded in search results
    config = types.GenerateContentConfig(
        tools=[search_tool],
        response_mime_type="application/json",
        response_schema=PeerGroup,
        temperature=0.2 
    )
    
    # 5. Prompt: Injecting the proper company name directly instead of making Gemini guess
    prompt = f"""
    Review the following context for our target company, {company_name}: 
    {json.dumps(company_context)}
    
    Based on their industry and business model, search the web to find up to 8 direct competitor organizations for {company_name}. 
    For each competitor, provide their exact, working homepage URL and a brief description. 
    Strictly limit the description to no more than two sentences per company. Do not exceed 8 peers.
    """
    
    print(f"Querying Gemini 3.1 Pro Preview with Search Grounding to find competitors for {company_name}...")
    
    # 6. Call the API
    response = client.models.generate_content(
        model="gemini-3.1-pro-preview",
        contents=prompt,
        config=config
    )
    
    # 7. Save the output JSON file directly back into the company's folder
    with open(output_json_path, 'w', encoding='utf-8') as f:
        f.write(response.text)
        
    print(f"Successfully saved peer group data to: {output_json_path}")

if __name__ == "__main__":
    if os.path.exists("config.json"):
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        
        target_folder = config.get("domain_folder")
        company_name = config.get("proper_company_name", target_folder.split('.')[0].capitalize())
        
        print(f"[+] Automating peer discovery for: {company_name}")
        find_peers(target_folder, company_name)
    else:
        print("Error: config.json not found. Run 00_run_pipeline.py first.")