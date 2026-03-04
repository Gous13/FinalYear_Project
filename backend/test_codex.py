import requests
import json

def test_codex():
    # Attempting to use CodeX API which is free and requires no key
    url = "https://api.codex.design/"
    payload = {
        "code": "public class Main { public static void main(String[] args) { System.out.println(\"Hello CodeX\"); } }",
        "language": "java",
        "input": ""
    }
    try:
        # CodeX API expects form-data or JSON? Docs say usually JSON
        response = requests.post(url, data=payload, timeout=15)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_codex()
