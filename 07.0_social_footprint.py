import json
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# --- Load Environment Variables ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# 1. Define Schemas
class SocialChannel(BaseModel):
    platform: str = Field(description="The name of the platform (e.g., LinkedIn, X/Twitter, YouTube).")
    profile_url: str = Field(description="The direct, working URL to the company's official profile page.")
    handle: str = Field(description="The account handle or username.")
    follower_count: str = Field(description="The approximate number of followers or subscribers.")
    video_count: str = Field(description="FOR YOUTUBE: The total number of videos uploaded. Otherwise 'N/A'.")
    notes: str = Field(description="Brief note on what this specific profile is used for.")

class ChannelList(BaseModel):
    channels: list[SocialChannel] = Field(description="A list of discovered profiles.")

class DigitalFootprint(BaseModel):
    channels: list[SocialChannel]
    digital_presence_summary: str

def get_platform_data(client, company_name, platform_instructions):
    """Fires a focused, single-platform search query to prevent the LLM from skipping tasks."""
    search_tool = types.Tool(google_search=types.GoogleSearch())
    config = types.GenerateContentConfig(
        tools=[search_tool],
        response_mime_type="application/json",
        response_schema=ChannelList,
        temperature=0.1 
    )
    
    prompt = f"""
    You are auditing the digital brand of "{company_name}".
    {platform_instructions}
    Extract the profile URL, handle, subscriber/follower count, and any relevant metrics.
    """
    try:
        response = client.models.generate_content(
            model="gemini-3.1-pro-preview",
            contents=prompt,
            config=config
        )
        return json.loads(response.text).get("channels", [])
    except Exception as e:
        print(f"  [!] Error fetching data for {company_name}: {e}")
        return []

def find_social_footprint(folder_path: str, company_name: str):
    # Updated to follow prefix-free naming conventions
    input_json_path = os.path.join(folder_path, "llm_insights.json")
    output_json_path = os.path.join(folder_path, "social_footprint.json")
    
    if not os.path.exists(input_json_path):
        print(f"Error: Could not find '{input_json_path}'. Please check your pipeline order.")
        return

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found. Please check your .env file.")
        return
        
    client = genai.Client(api_key=api_key)
    all_channels = []
    
    # --- Execute Targeted Searches ---
    print(f"\nScanning YouTube for {company_name}...")
    yt_instructions = f"Use Search Grounding to evaluate `youtube.com/results?search_query=\"{company_name}\"`. Find ALL fragmented or legacy channels. Extract exact subscriber and video counts."
    all_channels.extend(get_platform_data(client, company_name, yt_instructions))
    
    print(f"Scanning X/Twitter for {company_name}...")
    # Updated: Enforcing your exact profile user layout search layout structure
    x_instructions = f"Use Search Grounding to evaluate the search layout of `x.com/search?q=\"{company_name}\"&f=user`. Explicitly isolate active corporate handles or customer care accounts matching the company name."
    all_channels.extend(get_platform_data(client, company_name, x_instructions))
    
    print(f"Scanning LinkedIn for {company_name}...")
    # Updated: Forces Google to search the public company directory to bypass login walls
    corp_instructions = f"Use Search Grounding to evaluate `site:linkedin.com/company/ \"{company_name}\"`. Find their official corporate LinkedIn page. Extract the exact profile URL and the total follower count from the search snippets."
    all_channels.extend(get_platform_data(client, company_name, corp_instructions))
    
    # --- Generate Final Synthesis ---
    print(f"Synthesizing {len(all_channels)} discovered channels into final report...")
    synthesis_config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=DigitalFootprint,
        temperature=0.3
    )
    
    synthesis_prompt = f"""
    Review the following social channels discovered for {company_name}:
    {json.dumps(all_channels, indent=2)}
    
    Format this data exactly into the `channels` array. Then, write a 2-3 sentence `digital_presence_summary` assessing their footprint, particularly highlighting if they have duplicate or abandoned YouTube or Twitter accounts.
    """
    
    final_response = client.models.generate_content(
        model="gemini-3.1-pro-preview",
        contents=synthesis_prompt,
        config=synthesis_config
    )
    
    with open(output_json_path, 'w', encoding='utf-8') as f:
        f.write(final_response.text)
        
    print(f"\nSuccessfully saved comprehensive social footprint data to: {output_json_path}")

if __name__ == "__main__":
    if os.path.exists("config.json"):
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        
        target_folder = config.get("domain_folder")
        company_name = config.get("proper_company_name", target_folder.split('.')[0].capitalize())
        print(f"[+] Automating social footprint extraction for: {company_name}")
        find_social_footprint(target_folder, company_name)
    else:
        print("Error: config.json not found. Run 00_run_pipeline.py first.")