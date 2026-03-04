import requests
import json

def test_piston():
    url = "https://emkc.org/api/v2/piston/execute"
    payload = {
        "language": "java",
        "version": "*",
        "files": [
            {
                "name": "Main.java",
                "content": "public class Main { public static void main(String[] args) { System.out.println(\"Hello Piston\"); } }"
            }
        ]
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_piston()
