# Business Directory Scraper

An advanced AI-powered business directory scraper built with LangChain, Streamlit, and dynamic pagination detection for general URLs.

## Features

- **AI-Powered Extraction**: Uses LLM to extract structured business data from web directories
- **Dynamic Pagination**: Automatically detects and loads pages based on the limit (e.g., 20 limit loads main + page 2)
- **General URL Support**: Works with various directory sites (e.g., yellowpages.com, businesslist.ph)
- **Advanced Fallbacks**: If initial scrape fails, uses LLM-powered web search
- **CSV Export**: Download extracted data as CSV
- **Colorful UI**: Streamlit interface with custom styling

## Setup

1. Clone the repository
2. Create virtual environment: `uv venv` or `python -m venv .venv`
3. Activate: `.venv\Scripts\activate` (Windows)
4. Install dependencies: `uv pip install -r requirements.txt` or `pip install -r requirements.txt`
5. Set up environment variables in `.env`:
   ```
   GROQ_API_KEY=your_groq_api_key
   ```
6. Run: `streamlit run frontend/app.py`

## Deployment on Streamlit Cloud

1. Push code to GitHub
2. Connect repo to Streamlit Cloud
3. Set `GROQ_API_KEY` as environment variable in Streamlit Cloud settings
4. Deploy

## API Keys

- **Groq API Key**: Required for LLM extraction (get from https://console.groq.com/)

## How It Works

1. Enter a business directory URL
2. App detects pagination, loads pages dynamically until the limit is reached
3. Uses AI to extract business info from each page
4. Deduplicates results and displays in table
5. Download as CSV