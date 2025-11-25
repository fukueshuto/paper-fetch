import requests
import json

def test_ieee_oa():
    session = requests.Session()
    session.get("https://ieeexplore.ieee.org", timeout=10)

    headers = {
        'Host': 'ieeexplore.ieee.org',
        'Content-Type': "application/json",
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Origin': 'https://ieeexplore.ieee.org',
        'Referer': 'https://ieeexplore.ieee.org/search/searchresult.jsp'
    }

    # Test 1: openAccess as top-level string "true"
    payload1 = {
        "queryText": "LLM",
        "returnFacets": ["ALL"],
        "returnType": "SEARCH",
        "rowsPerPage": 5,
        "openAccess": "true"
    }

    print("--- Test 1: openAccess='true' ---")
    try:
        response = session.post("https://ieeexplore.ieee.org/rest/search", headers=headers, json=payload1, timeout=20)
        data = response.json()
        if 'records' in data:
            for item in data['records']:
                print(f"Title: {item.get('articleTitle')[:30]}... | Access: {item.get('accessType')}")
        else:
            print("No records.")
    except Exception as e:
        print(e)

    # Test 2: refinements (Alternative hypothesis)
    payload2 = {
        "queryText": "LLM",
        "returnFacets": ["ALL"],
        "returnType": "SEARCH",
        "rowsPerPage": 5,
        "refinements": ["ContentType:Open Access"]
    }

    print("\n--- Test 2: refinements=['ContentType:Open Access'] ---")
    try:
        response = session.post("https://ieeexplore.ieee.org/rest/search", headers=headers, json=payload2, timeout=20)
        data = response.json()
        if 'records' in data:
            for item in data['records']:
                print(f"Title: {item.get('articleTitle')[:30]}... | Access: {item.get('accessType')}")
        else:
            print("No records.")
    except Exception as e:
        print(e)

if __name__ == "__main__":
    test_ieee_oa()
