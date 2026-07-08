import json
import os
import re
from collections import deque
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import markdownify
from openai import OpenAI
import requests

# --- Load Environment Variables ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Set up DeepSeek Client
api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise ValueError("DEEPSEEK_API_KEY not found in .env file.")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)

def is_meaningful_peer_page(text, url):
    """Filters peer pages for company capabilities or AI references."""
    text_lower = text.lower()
    url_lower = url.lower()
    ai_pattern = r'\b(artificial intelligence|ai|machine learning|llm|automation|neural network|analytics|predictive)\b'
    context_pattern = r'\b(about us|services|solutions|what we do|platform|products|technology)\b'
    
    return bool(re.search(ai_pattern, text_lower)) or bool(re.search(ai_pattern, url_lower)) or \
           bool(re.search(context_pattern, text_lower)) or bool(re.search(context_pattern, url_lower))

def spider_peer_website(start_url, max_depth=2):
    """Fast mini-crawler that scans a peer site and aggregates text context."""
    base_domain = urlparse(start_url).netloc.replace('www.', '')
    visited = set()
    queue = deque([(start_url, 0)])
    aggregated_markdown = []
    
    print(f"    -> Spiddering {base_domain} (Max Depth: {max_depth})...")
    
    while queue:
        current_url, depth = queue.popleft()
        if current_url in visited or len(visited) >= 15: # Cap at 15 pages per peer to keep it fast
            continue
            
        visited.add(current_url)
        try:
            response = requests.get(current_url, timeout=8)
            if response.status_code != 200 or 'text/html' not in response.headers.get('Content-Type', ''):
                continue
                
            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = soup.get_text(separator=' ', strip=True)
            
            if is_meaningful_peer_page(page_text, current_url):
                md_content = markdownify.markdownify(str(soup), heading_style="ATX")
                aggregated_markdown.append(f"--- PAGE URL: {current_url} ---\n{md_content}\n")
                
            if depth < max_depth:
                for link in soup.find_all('a', href=True):
                    next_url = urljoin(current_url, link['href']).split('#')[0]
                    if base_domain in urlparse(next_url).netloc and next_url not in visited:
                        queue.append((next_url, depth + 1))
        except Exception:
            continue
            
    return "\n".join(aggregated_markdown)

def evaluate_peer_ai(company_name, markdown_text):
    """Sends peer web context to DeepSeek to analyze their AI posture."""
    system_prompt = """
    You are an expert competitive intelligence analyst. Analyze the provided web markdown context of a company.
    Provide a concise summary (EXACTLY 2 to 4 sentences) outlining their current artificial intelligence, machine learning, technology automation, or advanced data analytics initiatives.
    Be strictly factual based on the text. If they show no visible signs of AI initiatives or advanced tech deployment, explicitly state that their AI posture appears entirely nascent or non-existent.
    """
    
    try:
        response = client.chat.completions.create(
            model="deepseek-v4-flash", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Company: {company_name}\n\nContext:\n{markdown_text}"}
            ],
            temperature=0.1
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error analyzing peer AI footprint: {str(e)}"

def main(folder_path):
    # Updated paths to adhere to the prefix-free naming convention
    peers_json_path = os.path.join(folder_path, "peers.json")
    output_json_path = os.path.join(folder_path, "peer_ai_analysis.json")
    
    if not os.path.exists(peers_json_path):
        print(f"Error: Could not find '{peers_json_path}'. Run script 03.0 first.")
        return
        
    with open(peers_json_path, 'r', encoding='utf-8') as f:
        peer_data = json.load(f)
        
    peers_list = peer_data.get("peers", []) if isinstance(peer_data, dict) else peer_data
    
    print(f"\nLoaded {len(peers_list)} peers from index. Starting automated analysis pipeline...")
    
    analyzed_peers = []
    
    for peer in peers_list:
        name = peer.get("company_name")
        url = peer.get("homepage_url")
        
        print(f"\n[+] Processing Peer: {name} ({url})")
        
        # 1. Automated Step 01: Crawl/Spider
        context_md = spider_peer_website(url)
        
        # 2. Automated Step 02: Evaluate with LLM
        if context_md.strip():
            print(f"    -> Sending context to DeepSeek for analysis...")
            ai_summary = evaluate_peer_ai(name, context_md)
        else:
            print(f"    [-] No crawlable context found for {name}. Setting default posture.")
            ai_summary = "Could not evaluate AI posture due to restricted or un-crawlable web infrastructure."
            
        print(f"    -> Summary: {ai_summary}")
        
        analyzed_peers.append({
            "company_name": name,
            "homepage_url": url,
            "base_description": peer.get("description", ""),
            "ai_initiatives_summary": ai_summary
        })
        
    # 3. Save to unified JSON without numeric prefix
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(analyzed_peers, f, indent=4)
        
    print(f"\n[!] Success! Peer AI Competitive Analysis saved to: {output_json_path}")

if __name__ == "__main__":
    if os.path.exists("config.json"):
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        
        target_folder = config.get("domain_folder")
        print(f"[+] Automating competitive analysis loop for folder: {target_folder}")
        main(target_folder)
    else:
        print("Error: config.json not found. Run 00_run_pipeline.py first.")