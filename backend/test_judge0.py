import requests
import json

def test_judge0():
    # Attempting to use Judge0 public demo instance
    url = "https://ce.judge0.com/submissions?base64_encoded=false&wait=true"
    payload = {
        "source_code": "public class Main { public static void main(String[] args) { System.out.println(\"Hello Judge0\"); } }",
        "language_id": 62, # Java (OpenJDK 13.0.1)
        "stdin": ""
    }
    try:
        response = requests.post(url, json=payload, timeout=15)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_judge0()
