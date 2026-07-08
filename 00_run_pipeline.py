import os
import json
import requests
import subprocess
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI

# Load environmental keys to fetch the proper name from the API immediately
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Define the exact order of your pipeline
PIPELINE_SCRIPTS = [
    "01.0_spider.py",
    "02.0_evaluate.py",
    "03.0_find_peers.py",
    "04.0_peer_analysis.py",
    "05.0_company_news.py",
    "06.0_leadership.py",
    "07.0_social_footprint.py",
    "08.0_industry_context.py", # Make sure this matches your active script preferences
    "09.0_hiring_signals.py", 
    "10.0_industry_ai.py",
    "11.0_generate_report.py" 
]

def glean_proper_company_name(url):
    """Hits the homepage and lets DeepSeek cleanly isolate the formal business name."""
    print(f"[+] Scraping homepage metadata to lock in official company name...")
    try:
        response = requests.get(url, timeout=8)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Pull text components most likely containing the clean corporate name
        title_text = soup.title.string if soup.title else ""
        h1_text = soup.find('h1').get_text() if soup.find('h1') else ""
        
        # Fallback to domain structure if the page fetch is restricted
        domain_fallback = urlparse(url).netloc.replace('www.', '').split('.')[0].capitalize()
        
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            return domain_fallback
            
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        
        system_prompt = "You are a clean corporate data parser. Respond ONLY with the official, properly capitalized corporate name extracted from the text."
        user_prompt = f"URL Domain: {url}\nPage Title: {title_text}\nMain Header: {h1_text}"
        
        completion = client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1
        )
        return completion.choices[0].message.content.strip()
    except Exception:
        # Secure fallback if network blocks us at initialization
        return urlparse(url).netloc.replace('www.', '').split('.')[0].capitalize()

def setup_target():
    """Checks for env variables (headless), otherwise prompts for URL and depth."""
    print("="*50)
    print("   AI COMPETITIVE INTELLIGENCE PIPELINE INIT")
    print("="*50)
    
    # NEW: Check for Headless Environment Variables first
    start_url = os.getenv("TARGET_URL")
    if not start_url:
        start_url = input("Enter the target company's main URL (e.g., https://exeterfinance.com): ").strip()
    
    if not start_url:
        print("Error: URL cannot be blank.")
        return None
        
    if not start_url.startswith('http'):
        start_url = 'https://' + start_url
        
    domain_folder = urlparse(start_url).netloc.replace('www.', '')
    
    # NEW: Check for Headless Depth Variable
    depth_env = os.getenv("CRAWL_DEPTH")
    if depth_env:
        max_depth = int(depth_env)
    else:
        depth_input = input("Enter maximum crawl depth (Press Enter for default: 4): ").strip()
        max_depth = int(depth_input) if depth_input.isdigit() else 4
    
    # Glean the crisp proper name immediately 
    proper_name = glean_proper_company_name(start_url)
    
    config_data = {
        "target_url": start_url,
        "domain_folder": domain_folder,
        "proper_company_name": proper_name,
        "max_depth": max_depth
    }
    
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4)
        
    print(f"\n[+] Target Locked!")
    print(f"    Folder Name:  {domain_folder}")
    print(f"    Proper Name:  {proper_name}")
    print(f"    Crawl Depth:  {max_depth}")
    print(f"    Saved to root config.json.\n")
    return domain_folder

def run_script(script_name):
    """Executes a python script and monitors its output"""
    if not os.path.exists(script_name):
        print(f"\n[!] WARNING: {script_name} not found in directory. Skipping...")
        return True 
        
    print("-" * 50)
    print(f">>> EXECUTING: {script_name}")
    print("-" * 50)
    
    try:
        subprocess.run(["python", script_name], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n[X] CRITICAL ERROR: {script_name} crashed with exit code {e.returncode}.")
        return False

def main():
    target = setup_target()
    if not target:
        return
        
    print("Beginning automated execution of pipeline...")
    for script in PIPELINE_SCRIPTS:
        success = run_script(script)
        if not success:
            print("\n[!] Pipeline halted due to error. Fix the script and try again.")
            break
            
    print("\n" + "="*50)
    print(f"PIPELINE COMPLETE FOR: {target}")
    print("="*50)

if __name__ == "__main__":
    main()
