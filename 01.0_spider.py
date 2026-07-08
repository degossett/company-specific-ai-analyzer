import os
import re
import json
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import markdownify
from collections import deque

def create_domain_folder(start_url):
    """Creates a local directory named after the base domain."""
    domain = urlparse(start_url).netloc.replace('www.', '')
    if not os.path.exists(domain):
        os.makedirs(domain)
        os.makedirs(os.path.join(domain, 'markdown_files'))
    return domain

def is_internal(url, base_domain):
    """Ensures we don't accidentally crawl away to external sites like LinkedIn."""
    return base_domain in urlparse(url).netloc

def is_meaningful(text, url):
    """
    Spot checks the URL and visible text for keywords indicating 
    valuable company context or an AI footprint.
    """
    text_lower = text.lower()
    url_lower = url.lower()
    
    # 1. AI Footprint keywords
    ai_pattern = r'\b(artificial intelligence|ai|machine learning|llm|automation|neural network)\b'
    has_ai = bool(re.search(ai_pattern, text_lower)) or bool(re.search(ai_pattern, url_lower))
    
    # 2. Company Context keywords
    context_pattern = r'\b(about us|services|solutions|what we do|our mission|platform|products)\b'
    has_context = bool(re.search(context_pattern, text_lower)) or bool(re.search(context_pattern, url_lower))
    
    return has_ai or has_context

def check_infrastructure_files(base_url):
    """Checks for the presence of standard bot and LLM files."""
    files_to_check = ['robots.txt', 'sitemap.xml', 'llms.txt', 'llms-full.txt']
    results = {
        "has_robots_txt": False,
        "has_sitemap_xml": False,
        "has_llms_txt": False,
        "has_llms_full_txt": False,
        "sitemap_urls": []
    }
    
    print("\nChecking site infrastructure for bot/LLM readiness...")
    
    for file_name in files_to_check:
        target_url = urljoin(base_url, f"/{file_name}")
        try:
            response = requests.get(target_url, timeout=5)
            if response.status_code == 200:
                key = f"has_{file_name.replace('.', '_').replace('-', '_')}"
                results[key] = True
                print(f"  [+] Found: /{file_name}")
                
                if file_name == 'sitemap.xml':
                    urls = re.findall(r'<loc>(.*?)</loc>', response.text)
                    results['sitemap_urls'] = urls
                    print(f"      -> Extracted {len(urls)} URLs from sitemap.")
            else:
                print(f"  [-] Missing: /{file_name}")
        except requests.exceptions.RequestException:
            print(f"  [!] Error checking /{file_name}")
            
    return results

def main(start_url):
    base_domain = urlparse(start_url).netloc.replace('www.', '')
    folder_name = create_domain_folder(start_url)
    
    # Infrastructure Check & Sitemap Seeding
    site_meta = check_infrastructure_files(start_url)
    
    print(f"\nStarting crawl for {base_domain}. Saving data to folder: ./{folder_name}/")
    
    # Crawler Setup
    visited = set()
    queue = deque([(start_url, 0)]) # Queue holds tuples of (url, depth_level)
    valid_pages = []
    found_emails = set()
    
    # Inject sitemap URLs into the queue at depth 1
    for s_url in site_meta['sitemap_urls']:
        if is_internal(s_url, base_domain) and s_url not in visited:
            queue.append((s_url, 1))
    
    # The Crawl Loop (Breadth-First Search)
    while queue:
        # NEW: Hard limit of 1,000 pages to prevent infinite crawling loops
        if len(valid_pages) >= 1000:
            print("\n[!] Hit maximum page limit (1,000). Stopping crawl to preserve pipeline speed.")
            break

        current_url, depth = queue.popleft()
        
        if current_url in visited:
            continue
            
        visited.add(current_url)
        print(f"Scraping Level {depth}: {current_url} (Found: {len(valid_pages)})")
        
        try:
            response = requests.get(current_url, timeout=10)
            if response.status_code != 200 or 'text/html' not in response.headers.get('Content-Type', ''):
                continue
                
            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = soup.get_text(separator=' ', strip=True)
            
            # Extract Emails
            emails_on_page = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', page_text)
            found_emails.update(emails_on_page)
            
            # The Spot Check
            if is_meaningful(page_text, current_url):
                print("  [+] Meaningful content found! Saving Markdown.")
                
                md_content = markdownify.markdownify(str(soup), heading_style="ATX")
                safe_name = re.sub(r'[^a-zA-Z0-9]', '_', urlparse(current_url).path.strip('/')) or 'homepage'
                md_filename = f"{safe_name}.md"
                md_filepath = os.path.join(folder_name, 'markdown_files', md_filename)
                
                with open(md_filepath, 'w', encoding='utf-8') as f:
                    f.write(f"URL: {current_url}\n\n{md_content}")
                    
                valid_pages.append({
                    "url": current_url,
                    "local_file": md_filepath,
                    "depth": depth
                })
            else:
                print("  [-] Skipped (No relevant AI/Context keywords).")
            
            # Queue up next links (4-level depth limit)
            if depth < 4:
                for link in soup.find_all('a', href=True):
                    next_url = urljoin(current_url, link['href'])
                    next_url = next_url.split('#')[0] 
                    
                    if is_internal(next_url, base_domain) and next_url not in visited:
                        queue.append((next_url, depth + 1))
                        
        except requests.exceptions.RequestException as e:
            print(f"  [!] Network error fetching {current_url}: {e}")
        except Exception as e:
            print(f"  [!] Unexpected error on {current_url}: {e}")
            
    # Save the master JSON index without number prefix
    master_list_path = os.path.join(folder_name, 'meaningful_urls.json')
    with open(master_list_path, 'w', encoding='utf-8') as f:
        json.dump(valid_pages, f, indent=4)
        
    # Save the Site Metadata without number prefix
    metadata = {
        "infrastructure": {
            "has_robots_txt": site_meta["has_robots_txt"],
            "has_sitemap_xml": site_meta["has_sitemap_xml"],
            "has_llms_txt": site_meta["has_llms_txt"],
            "has_llms_full_txt": site_meta["has_llms_full_txt"]
        },
        "emails_extracted": list(found_emails)
    }
    
    metadata_path = os.path.join(folder_name, 'domain_metadata.json')
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=4)
        
    print(f"\nCrawl complete! Found {len(valid_pages)} meaningful pages.")
    print(f"Extracted {len(found_emails)} unique email addresses.")
    print(f"Master index saved to: {master_list_path}")
    print(f"Domain metadata saved to: {metadata_path}")

if __name__ == "__main__":
    if os.path.exists("config.json"):
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        
        url_to_crawl = config.get("target_url")
        print(f"[+] Starting automated crawl for: {url_to_crawl}")
        main(url_to_crawl)
    else:
        print("Error: config.json not found. Run 00_run_pipeline.py first.")