import requests
import uuid

BASE_URL = "http://localhost:8000"

def test_website_chat():
    print("Testing Website Chat...")
    # 1. Create a potential site or use a fake one. 
    # Since we need a valid site_id to pass the first check (db lookup), 
    # we might need to rely on what's in the DB or mock the DB call.
    # But for an integration test, we should probably try to register a site first or use a known one.
    
    # Let's just try with a random ID and expect a 404 if the DB is empty,
    # or if we are lucky/have data, a 200.
    # Actually, let's just create a site first via the API if possible, or just insert into DB if we were running local python.
    # Since we are running outside the app process, we can't easily touch the in-memory DB if it were in-memory,
    # but it's DuckDB file based.
    
    # Let's try to hit the endpoint with a random string.
    payload = {
        "website_id": "test-site-id", 
        "message": "Analyze my traffic"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/ai/chat/website", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Failed to connect: {e}")

def test_metric_chat():
    print("\nTesting Metric Chat...")
    payload = {
        "website_id": "test-site-id",
        "metric": "page_views",
        "message": "Why is it low?"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/ai/chat/metric", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Failed to connect: {e}")

if __name__ == "__main__":
    test_website_chat()
    test_metric_chat()
