import requests
import json

def test_ieee_api():
    session = requests.Session()
    # Get cookies
    session.get("https://ieeexplore.ieee.org", timeout=10)

    headers = {
        'Host': 'ieeexplore.ieee.org',
        'Content-Type': "application/json",
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Origin': 'https://ieeexplore.ieee.org',
        'Referer': 'https://ieeexplore.ieee.org/search/searchresult.jsp'
    }

    payload = {
        "queryText": "LLM Agents",
        "returnFacets": ["ALL"],
        "returnType": "SEARCH",
        "rowsPerPage": 1
    }

    try:
        response = session.post(
            "https://ieeexplore.ieee.org/rest/search",
            headers=headers,
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        if 'records' in data and len(data['records']) > 0:
            record = data['records'][0]
            print("Keys in record:", record.keys())
            print("Title:", record.get('articleTitle'))
            print("Access Type:", record.get('accessType')) # Checking for this
            print("Is Locked:", record.get('isLocked')) # Or this
            print("Display Content:", record.get('displayContentType'))
            print("Full Record:", json.dumps(record, indent=2))
        else:
            print("No records found.")
            print(data)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_ieee_api()
