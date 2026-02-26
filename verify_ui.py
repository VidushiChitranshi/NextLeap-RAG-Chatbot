import requests
import json

BASE_URL = "http://localhost:8003"

def test_health():
    print("Testing health check (GET /)...")
    try:
        response = requests.get(BASE_URL)
        if response.status_code == 200:
            print("[+] Header/Index page is accessible.")
        else:
            print(f"[-] Index page failed with status {response.status_code}")
    except Exception as e:
        print(f"[-] Error connecting to server: {e}")

def test_chat():
    print("\nTesting chat endpoint (POST /chat)...")
    payload = {"message": "What is the fee for the PM fellowship?"}
    try:
        response = requests.post(f"{BASE_URL}/chat", json=payload)
        if response.status_code == 200:
            data = response.json()
            print("[+] Chat endpoint responded.")
            print(f"   Answer: {data.get('answer')[:100]}...")
            print(f"   Citations: {data.get('citations')}")
            print(f"   Success: {data.get('success')}")
            if not data.get('success'):
                print(f"   Error detail: {data.get('error')}")
        else:
            print(f"[-] Chat endpoint failed with status {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"[-] Error during chat test: {e}")

def test_clear():
    print("\nTesting clear history (POST /clear)...")
    try:
        response = requests.post(f"{BASE_URL}/clear")
        if response.status_code == 200:
            print("[+] Clear history success.")
        else:
            print(f"[-] Clear history failed with status {response.status_code}")
    except Exception as e:
        print(f"[-] Error during clear test: {e}")

if __name__ == "__main__":
    test_health()
    test_chat()
    test_clear()
