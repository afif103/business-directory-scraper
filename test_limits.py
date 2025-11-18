import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from backend.scraper import scrape_business_directory

url = "https://www.businesslist.ph/location/zamboanga-city"

limits = [10, 20, 50, 100]

for limit in limits:
    print(f"\nTesting with max_businesses={limit}")
    try:
        result = scrape_business_directory(url, max_businesses=limit)
        if isinstance(result, list):
            print(f"Found {len(result)} businesses")
            if result:
                print("First business:", result[0])
        elif isinstance(result, str):
            print("Raw text result, length:", len(result))
        else:
            print("No results")
    except Exception as e:
        print(f"Error: {e}")
