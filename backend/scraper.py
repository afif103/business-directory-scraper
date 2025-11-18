import os
import re
import json

from langchain_community.document_loaders import WebBaseLoader

try:
    from langchain_community.document_loaders import SeleniumURLLoader

    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

# Load environment variables for API keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


def extract_location_from_url(url: str, llm):
    """
    Extract location information from the URL or page content.
    """
    # Simple extraction from URL
    if "city=" in url or "location=" in url:
        # Parse query params
        from urllib.parse import urlparse, parse_qs

        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        location = params.get("city", params.get("location", [None]))[0]
        if location:
            return location

    # Use LLM to extract location from page content
    if SELENIUM_AVAILABLE:
        loader = SeleniumURLLoader(urls=[url])
        documents = loader.load()
    else:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        loader = WebBaseLoader(url, requests_kwargs={"headers": headers})
        documents = loader.load()
    text = " ".join([doc.page_content for doc in documents])

    prompt = f"Extract the primary city or location from this text. Return only the city name, nothing else. If none, say 'unknown'. Text: {text[:2000]}"
    response = llm.invoke(prompt)
    location = response.content.strip()
    # Clean up the response
    location = location.split("\n")[0].split(".")[0].strip()
    if "unknown" in location.lower() or not location:
        return None
    return location


def get_all_page_urls(url: str):
    """
    Detect and collect all pagination URLs from a directory site.
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        from urllib.parse import urljoin, urlparse

        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.content, "html.parser")

        page_urls = [url]  # Start with the main URL

        # Look for pagination links with common patterns
        pagination_selectors = [
            "div.pagination",
            "div.pager",
            "nav.pagination",
            "ul.pagination",
            ".pagination",
            ".pager",
            "div.page-numbers",
            "nav.page-navigation",
        ]

        for selector in pagination_selectors:
            pagination = soup.select_one(selector)
            if pagination:
                links = pagination.find_all("a", href=True)
                for link in links:
                    href = link["href"]
                    full_url = urljoin(url, href)
                    if (
                        full_url not in page_urls
                        and urlparse(full_url).netloc == urlparse(url).netloc
                    ):
                        page_urls.append(full_url)

        # Look for "next" links
        next_links = soup.find_all("a", string=re.compile(r"next|Next|NEXT|>", re.I))
        for link in next_links:
            href = link.get("href")
            if href:
                full_url = urljoin(url, href)
                if (
                    full_url not in page_urls
                    and urlparse(full_url).netloc == urlparse(url).netloc
                ):
                    page_urls.append(full_url)

        # Look for links with numeric paths (e.g., /2, /3)
        numeric_links = soup.find_all("a", href=re.compile(r"/\d+/?$"))
        for link in numeric_links:
            href = link["href"]
            full_url = urljoin(url, href)
            if (
                full_url not in page_urls
                and urlparse(full_url).netloc == urlparse(url).netloc
            ):
                page_urls.append(full_url)
                # Generate more based on this pattern
                base = href.rsplit("/", 1)[0] + "/"
                for i in range(2, 21):
                    new_href = f"{base}{i}"
                    new_full = urljoin(url, new_href)
                    if new_full not in page_urls:
                        page_urls.append(new_full)

        # Generate page URLs if pattern detected (e.g., ?page=2, /page/2)
        parsed = urlparse(url)
        if "page" in parsed.query or "/page/" in url:
            for i in range(2, 21):  # Try pages 2-20
                if "page" in parsed.query:
                    new_query = re.sub(r"page=\d+", f"page={i}", parsed.query)
                    new_url = parsed._replace(query=new_query).geturl()
                else:
                    new_url = url.rstrip("/") + f"/page/{i}"
                page_urls.append(new_url)
        else:
            # Try common pagination patterns
            for i in range(2, 21):
                page_urls.append(f"{url.rstrip('/')}/page/{i}")
                page_urls.append(f"{url}?page={i}")
                page_urls.append(f"{url}&page={i}")
                page_urls.append(f"{url.rstrip('/')}/{i}")  # For sites like /2, /3

        # Remove duplicates and limit
        page_urls = list(
            dict.fromkeys(page_urls)
        )  # Remove duplicates while preserving order
        return page_urls[:20]  # Limit to 20 pages

    except Exception as e:
        print(f"Pagination detection failed: {e}")
        return [url]


def scrape_business_directory(url: str, max_businesses: int = 20, api_key: str = None):
    """
    Scrape a business directory page and extract business information.
    Use advanced fallbacks if initial method fails.
    """
    # Get all page URLs for pagination
    page_urls = get_all_page_urls(url)
    print(f"Found {len(page_urls)} pages to scrape")

    # Initialize LLM
    groq_key = api_key or GROQ_API_KEY
    llm = ChatGroq(model="llama-3.1-8b-instant", api_key=groq_key)

    # Define prompt for extraction
    prompt_template = """
    Extract business information from the following text. Output ONLY a valid JSON array of objects, where each object has keys: name, address, phone, email, services, website_url.

    Extract every single business listing, including all names, addresses, phones, and details. List as many as possible.

    If information is not available, use null or empty string.

    Do not include any text before or after the JSON array.

    Text: {context}
    """

    prompt = ChatPromptTemplate.from_template(prompt_template)
    chain = prompt | llm

    all_businesses = []
    seen = set()
    unique_businesses = []
    result = "No data extracted."

    for page_url in page_urls:
        if len(unique_businesses) >= max_businesses:
            break  # Stop if we have enough
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(page_url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            text = soup.get_text()
            if len(text.strip()) <= 500:
                continue  # Skip pages with insufficient content
            if len(text.strip()) < 500:  # Lower threshold to include main pages
                continue
            try:
                result = chain.invoke({"context": text}).content
            except Exception as e:
                print(f"LLM extraction failed for {page_url}: {e}")
                result = "Error extracting data from page."
                continue
            businesses = parse_businesses(result)
            if businesses:
                for business in businesses:
                    if not isinstance(business, dict):
                        continue
                    name = (business.get("name") or "").lower().strip()
                    address = (business.get("address") or "").lower().strip()
                    key = (name, address)
                    if key not in seen and key[0]:
                        seen.add(key)
                        unique_businesses.append(business)
            print(
                f"Loaded page: {page_url}, businesses extracted: {len(businesses) if 'businesses' in locals() else 0}, total unique: {len(unique_businesses)}"
            )
        except Exception as e:
            print(f"Failed to load {page_url}: {e}")
            continue

    businesses = unique_businesses
    if businesses and len(businesses) > 0:
        # Remove duplicates based on name and address
        unique_businesses = []
        seen = set()
        for business in businesses:
            if not isinstance(business, dict):
                continue
            name = (business.get("name") or "").lower().strip()
            address = (business.get("address") or "").lower().strip()
            key = (name, address)
            if key not in seen and key[0]:  # Ensure name is not empty
                seen.add(key)
                unique_businesses.append(business)
        return unique_businesses[:max_businesses]

    # If no businesses found, return raw text
    print("No businesses extracted. Returning raw text.")
    return result  # Fallback to raw text


def parse_businesses(text):
    """
    Parse the LLM output into a list of business dictionaries.
    """
    # Clean the text: remove markdown code blocks if present
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        # Try to parse as JSON directly
        businesses = json.loads(text)
        if isinstance(businesses, list):
            return businesses
    except json.JSONDecodeError:
        pass

    try:
        # Try to find JSON array in text
        start = text.find("[")
        end = text.rfind("]") + 1
        if start != -1 and end > start:
            json_str = text[start:end]
            businesses = json.loads(json_str)
            if isinstance(businesses, list):
                return businesses
    except json.JSONDecodeError:
        pass

    # Fallback: return empty list to trigger fallback in scraper
    return []


if __name__ == "__main__":
    # Example usage
    url = "https://example.com/business-directory"  # Replace with actual URL
    businesses = scrape_business_directory(url)
    print(businesses)
