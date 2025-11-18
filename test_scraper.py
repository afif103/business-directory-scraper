import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from backend.scraper import scrape_business_directory

url = "https://www.businesslist.ph/location/zamboanga-city"
print("Testing scraper with URL:", url)
result = scrape_business_directory(url)
print("Result type:", type(result))
print("Result length:", len(result) if isinstance(result, list) else "N/A")
if isinstance(result, list) and result:
    print("First business:", result[0])
elif isinstance(result, str):
    print("Raw text preview:", result[:500])
else:
    print("No results found")
