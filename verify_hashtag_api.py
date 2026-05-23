import requests
import json

def test_api():
    url = "http://127.0.0.1:8000/api/dashboard-intelligence"
    params = {"profile_url": "https://www.instagram.com/nasa"}
    
    print(f"Sending GET request to {url} with params {params}...")
    try:
        response = requests.get(url, params=params, timeout=90)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("API response successfully received! Structure keys:")
            print(list(data.keys()))
            
            if "hashtags_analysis" in data:
                print("\n[SUCCESS] 'hashtags_analysis' key found in payload!")
                print(json.dumps(data["hashtags_analysis"], indent=2))
            else:
                print("\n[ERROR] 'hashtags_analysis' key missing in payload!")
        else:
            print(f"Failed to fetch data: {response.text}")
    except Exception as e:
        print(f"Network error or timeout: {str(e)}")

if __name__ == "__main__":
    test_api()
