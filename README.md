# Business Directory Scraper

A tool to scrape business directories (clinics, schools, restaurants, etc.) and extract key information using AI.

## Features

- Scrape web pages using LangChain HTML loader
- Extract business data: Name, Address, Phone, Email, Services, Website URL
- Store data in Chroma vector database
- Web UI with Streamlit

## Tech Stack

- Python 3.12+
- LangChain
- Chroma
- Streamlit
- HuggingFace Embeddings
- Cerebras LLM (preferred)

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables in `.env`:
   - `CEREBRAS_API_KEY=your_key`

## Usage

Run the Streamlit app: `streamlit run frontend/app.py`

Enter a business directory URL and click "Scrape Directory" to extract data.

## Project Structure

```
business_directory_scraper/
├── backend/
│   └── scraper.py
├── frontend/
│   └── app.py
├── tools/
├── config/
├── requirements.txt
├── README.md
├── .gitignore
└── Dockerfile
```

## Deployment

Use Docker: `docker build -t scraper .` then `docker run scraper`

Or deploy Streamlit app to Streamlit Cloud.