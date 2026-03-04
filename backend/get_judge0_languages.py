import requests
import json

def get_languages():
    url = "https://ce.judge0.com/languages"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            langs = response.json()
            # Filter for the ones we care about
            targets = ['python', 'java', 'c', 'c++', 'javascript']
            results = []
            for lang in langs:
                name = lang['name'].lower()
                if any(t in name for t in targets):
                    results.append({'id': lang['id'], 'name': lang['name']})
            print(json.dumps(results, indent=2))
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_languages()
