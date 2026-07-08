# AI Consulting Pipeline: Automated Competitive Intelligence & AI Readiness

An enterprise-grade, modular Python pipeline designed to automate competitive intelligence gathering and assess a target company's AI readiness. By decoupling web crawling from Large Language Model (LLM) synthesis, this architecture acts as a robust, localized data pipeline—perfectly staging unstructured web data for AI agent consumption (inspired by Model Context Protocol/MCP design patterns).

The pipeline automatically spiders a target domain, analyzes its AI footprint, conducts real-time market/peer research via search grounding, and synthesizes the findings into a boardroom-ready, diplomatic Microsoft Word executive report.

## 🚀 Key Features

* **Hands-Free Orchestration:** A central controller (`00_run_pipeline.py`) manages the entire execution sequence, dynamically gleaning the proper corporate name and passing it downstream via a unified `config.json`.
* **Intelligent Web Spidering:** A breadth-first scraper that strips HTML bloat, converts pages to pure Markdown (the gold standard for LLMs), and strictly limits crawl depth/page counts to prevent infinite loops.
* **AI Infrastructure Auditing:** Automatically checks the target domain for emerging machine-readable agent endpoints (e.g., `llms.txt`, `llms-full.txt`) and IndexNow protocols.
* **Real-Time Search Grounding:** Leverages Gemini 3.1 Pro with Google Search Grounding to bypass UI anti-bot walls (like LinkedIn and ATS job boards) to pull real-time hiring signals, chronological news, and social metrics.
* **Cost-Optimized API Caching:** Maximizes DeepSeek's context caching by passing static Markdown prefixes, making deep-read evaluations incredibly cheap and fast.
* **Diplomatic Sanitizer Layer:** Automatically intercepts and reframes harsh LLM critiques (e.g., "stagnant," "deficient") into constructive, executive-friendly strategic opportunities before writing to the final Word document.
* **Self-Healing Execution:** Built-in `try...except` JSON validation blocks and automatic retry loops ensure that hallucinated or malformed LLM syntax never crashes the pipeline.

---

## 🏗️ Pipeline Architecture

The system is broken down into highly modular, decoupled scripts. This ensures that if a downstream API fails, you do not have to re-scrape the target website.

| Script | Purpose | Technology / Engine | Output |
| :--- | :--- | :--- | :--- |
| `00_run_pipeline.py` | Master orchestrator; establishes config and runs the sequence. | Python `subprocess`, DeepSeek | `config.json` |
| `01.0_spider.py` | Crawls target domain, converts HTML to Markdown, checks `llms.txt`. | `BeautifulSoup`, `markdownify` | Local `.md` files, `meaningful_urls.json` |
| `02.0_evaluate.py` | Reads local Markdown to determine company context & AI posture. | DeepSeek v4 Flash | `llm_insights.json` |
| `03.0_find_peers.py` | Identifies up to 8 direct market competitors. | Gemini 3.1 Pro (Grounding) | `peers.json` |
| `04.0_peer_analysis.py`| Spiders peer websites and evaluates their AI footprint. | DeepSeek v4 Flash | `peer_ai_analysis.json` |
| `05.0_company_news.py` | Fetches the top 10 most recent news events chronologically. | Gemini 3.1 Pro (Grounding) | `news.json` |
| `06.0_leadership.py` | Scrapes C-Suite registry, titles, and tenures. | Gemini 3.1 Pro (Grounding) | `leadership.json` |
| `07.0_social_footprint.py`| Audits digital footprint, forcing specific layout operators (X, YT). | Gemini 3.1 Pro (Grounding) | `social_footprint.json` |
| `08.0_industry_context.py`| *(Optional)* Analyzes macroeconomic industry headwinds. | Gemini 3.1 Pro (Grounding) | `industry_context.json` |
| `09.0_hiring_signals.py`| Bypasses ATS UIs to find active tech/AI engineering job postings. | Gemini 3.1 Pro (Grounding) | `hiring_signals.json` |
| `10.0_industry_ai.py` | Maps specific AI use-cases within the target's industry sector. | Gemini 3.1 Pro (Grounding) | `industry_ai.json` |
| `11.0_generate_report.py`| Synthesizes all JSON artifacts into a formatted, hyperlinked report. | GLM-5.2 (Z.AI), `python-docx` | `[Company]_Executive_Report.docx` |

---

## 🛠️ Setup & Installation

**1. Clone the repository**
```bash
git clone https://github.com/yourusername/ai-consulting-pipeline.git
cd ai-consulting-pipeline
```

**2. Install dependencies**
```bash
pip install python-dotenv requests beautifulsoup4 markdownify openai google-genai pydantic python-docx
```

**3. Configure Environment Variables**
Create a `.env` file in the root directory and add your API keys:
```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
ZAI_API_KEY=your_zai_api_key_here
```

---

## 🚀 Usage

The entire pipeline is fully automated and orchestrated through a single script.

```bash
python 00_run_pipeline.py
```

1. **Input the Target URL:** You will be prompted to enter the homepage URL (e.g., `exeterfinance.com`).
2. **Set Crawl Depth:** You will be prompted to enter a crawl depth (defaults to `4`).
3. **Execution:** The script will dynamically glean the formal corporate name, build a target directory, and fire off scripts `01.0` through `11.0` sequentially. 

---

## 📄 Output: The Executive Report

The final artifact is a `[Company_Name]_Executive_Report.docx` saved directly into the target company's folder. The document is strictly formatted with professional styling, clickable hyperlinks, and collapsible XML sections.

**Report Sections:**
1. **AI Readiness Score:** A 0-100 score with core justifications, concluding with an audit of their AI Discovery Infrastructure (`llms.txt` / IndexNow readiness).
2. **Strategic AI Opportunities:** High-ROI, prioritized recommendations generated by GLM-5.2.
3. **AI Human Capital Investment:** An analysis of their active hiring footprint (or lack thereof) mapped to specific data science/engineering requisitions.
4. **Industry AI Context:** Real-world examples of how AI is being deployed right now within their specific market sector.
5. **Peer AI Benchmarking:** A competitive matrix detailing the AI initiatives of up to 8 direct competitors.
6. **Supplemental Intelligence:** A collapsible section containing executive leadership profiles, recent chronological news, and a cleaned digital/social footprint (YouTube, X, LinkedIn).

---

## 🧠 Technical Highlights for Resume/Portfolio

* **Data Pipeline Engineering:** Constructed a robust Extraction, Transformation, and Load (ETL) pipeline replacing traditional heavy HTML scraping with lightweight Markdown transformation optimized for LLM token ingestion.
* **Agentic Search Grounding:** Leveraged Gemini's Native Search Grounding to bypass hostile UI defenses (like LinkedIn login walls and Applicant Tracking Systems) using advanced Google search operators (`site:linkedin.com/company/`).
* **Structured AI Outputs:** Enforced strict schema adherence using `Pydantic` and JSON response formatting to guarantee programmatic interoperability between disparate AI models (DeepSeek, Gemini, GLM-5.2).
* **Automated Tone Modulation:** Engineered a real-time regex sanitization layer that intercepts raw LLM outputs and reframes aggressive evaluations into diplomatic, constructive executive language.