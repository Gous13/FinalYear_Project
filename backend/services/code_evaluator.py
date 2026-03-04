import subprocess
import os
import json
import tempfile
import shutil
import requests

def normalize_output(text):
    """Normalize whitespace and line endings for comparison (Case-insensitive)"""
    if text is None: return ""
    return " ".join(text.strip().split()).lower()

# Mapping for cloud fallback
JUDGE0_LANGUAGE_IDS = {
    'python': 100,      # Python (3.12.5)
    'java': 62,         # Java (OpenJDK 13.0.1)
    'c': 50,            # C (GCC 9.2.0)
    'c++': 54,          # C++ (GCC 9.2.0)
    'cpp': 54,          # C++ (GCC 9.2.0)
    'javascript': 102,  # JavaScript (Node.js 22.08.0)
    'js': 102
}

def evaluate_via_cloud(language, code, test_cases):
    """Transparently fallback to Judge0 Cloud API for evaluation"""
    lang_id = JUDGE0_LANGUAGE_IDS.get(language.lower())
    if not lang_id:
        return None # Fallback not configured for this language

    passed_count = 0
    results = []
    
    for tc in test_cases:
        input_str = tc.get('input', '')
        if isinstance(input_str, (list, dict)):
            input_str = json.dumps(input_str)
        else:
            input_str = str(input_str)
            
        expected_output = str(tc.get('expected_output', ''))
        
        # Using Judge0 CE public instance
        url = "https://ce.judge0.com/submissions?base64_encoded=false&wait=true"
        payload = {
            "source_code": code,
            "language_id": lang_id,
            "stdin": input_str
        }
        
        try:
            response = requests.post(url, json=payload, timeout=20)
            if response.status_code in [200, 201]:
                data = response.json()
                actual_output = data.get('stdout', '')
                status_id = data.get('status', {}).get('id')
                status_desc = data.get('status', {}).get('description', 'Execution Failed')
                
                if status_id == 3: # Accepted
                    if normalize_output(actual_output) == normalize_output(expected_output):
                        passed_count += 1
                        results.append({"passed": True, "message": "Test case passed (Cloud)"})
                    else:
                        results.append({
                            "passed": False,
                            "message": "Wrong Answer (Cloud)",
                            "expected": expected_output,
                            "actual": actual_output
                        })
                else:
                    msg = status_desc
                    if data.get('compile_output'):
                        msg += f":\n{data.get('compile_output')}"
                    elif data.get('stderr'):
                        msg += f":\n{data.get('stderr')}"
                    results.append({"passed": False, "message": f"Cloud {msg}"})
            else:
                results.append({"passed": False, "message": f"Cloud Service Error (HTTP {response.status_code})"})
        except Exception as e:
            results.append({"passed": False, "message": f"Cloud Connection Error: {str(e)}"})
            
    return {
        "passed_count": passed_count,
        "total_count": len(test_cases),
        "results": results,
        "score": (passed_count / len(test_cases) * 100) if test_cases else 0
    }

def evaluate_code(language, code, test_cases_json):
    """
    Evaluates code in various languages by running it against test cases.
    Supported: python, java, c, cpp, javascript
    Includes transparent Judge0 fallback for missing local environments.
    """
    try:
        test_cases = json.loads(test_cases_json)
    except Exception:
        return {"error": "Invalid test cases format"}

    passed_count = 0
    total_count = len(test_cases)
    results = []

    # Create a temporary directory for local execution attempt
    temp_dir = tempfile.mkdtemp()
    language = language.lower().strip()
    
    try:
        # Language specific setup
        if language == 'python':
            file_name = "solution.py"
            run_cmd = ["python", file_name]
            compile_cmd = None
        elif language == 'java':
            file_name = "Main.java"
            compile_cmd = ["javac", file_name]
            run_cmd = ["java", "Main"]
        elif language == 'c':
            file_name = "solution.c"
            compile_cmd = ["gcc", file_name, "-o", "solution"]
            run_cmd = [os.path.join(".", "solution") if os.name != 'nt' else "solution.exe"]
        elif 'c++' in language or 'cpp' in language:
            file_name = "solution.cpp"
            compile_cmd = ["g++", file_name, "-o", "solution"]
            run_cmd = [os.path.join(".", "solution") if os.name != 'nt' else "solution.exe"]
        elif language in ['javascript', 'js']:
            file_name = "solution.js"
            run_cmd = ["node", file_name]
            compile_cmd = None
        else:
            return {"error": f"Language {language} not supported"}

        # Write code to file for local run attempt
        file_path = os.path.join(temp_dir, file_name)
        with open(file_path, "w", encoding='utf-8') as f:
            f.write(code)

        # 1. Try local compilation if required
        if compile_cmd:
            try:
                comp_proc = subprocess.run(
                    compile_cmd, 
                    cwd=temp_dir, 
                    capture_output=True, 
                    text=True, 
                    timeout=15
                )
                if comp_proc.returncode != 0:
                    return {
                        "passed_count": 0,
                        "total_count": total_count,
                        "results": [{"passed": False, "message": f"Compilation Error:\n{comp_proc.stderr}"}],
                        "score": 0
                    }
            except FileNotFoundError:
                # Local compiler missing -> Trigger Cloud Fallback
                return evaluate_via_cloud(language, code, test_cases)

        # 2. Try running test cases locally
        for tc in test_cases:
            input_str = tc.get('input', '')
            if isinstance(input_str, (list, dict)):
                input_str = json.dumps(input_str)
            else:
                input_str = str(input_str)
                
            expected_output = str(tc.get('expected_output', ''))
            
            try:
                run_proc = subprocess.run(
                    run_cmd,
                    cwd=temp_dir,
                    input=input_str,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                actual_output = run_proc.stdout
                
                if run_proc.returncode != 0:
                    results.append({
                        "passed": False, 
                        "message": f"Runtime Error:\n{run_proc.stderr or run_proc.stdout}"
                    })
                elif normalize_output(actual_output) == normalize_output(expected_output):
                    passed_count += 1
                    results.append({"passed": True, "message": "Test case passed"})
                else:
                    results.append({
                        "passed": False,
                        "message": "Wrong Answer",
                        "expected": expected_output,
                        "actual": actual_output
                    })
                    
            except FileNotFoundError:
                # Local runtime missing -> Trigger Cloud Fallback for remaining cases
                # Note: To be simple, if one fails due to missing runtime, we switch to cloud for the WHOLE set
                return evaluate_via_cloud(language, code, test_cases)
            except subprocess.TimeoutExpired:
                results.append({"passed": False, "message": "Time Limit Exceeded"})
            except Exception as e:
                results.append({"passed": False, "message": f"Execution Error: {str(e)}"})

    finally:
        # Cleanup temp directory
        try:
            shutil.rmtree(temp_dir)
        except:
            pass

    return {
        "passed_count": passed_count,
        "total_count": total_count,
        "results": results,
        "score": (passed_count / total_count * 100) if total_count > 0 else 0
    }
