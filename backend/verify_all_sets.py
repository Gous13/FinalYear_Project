from services.code_evaluator import evaluate_code
import sqlite3
import os
import json

def verify_all_coding_sets():
    db_path = os.path.join(os.getcwd(), 'instance', 'synapselink.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, set_id, difficulty, title, test_cases_json FROM assessment_questions WHERE skill_name='CODING'")
    questions = cursor.fetchall()
    
    solutions = {
        "Sum of Array Elements": """
import sys
input_data = sys.stdin.read().split()
if input_data:
    n = int(input_data[0])
    nums = [int(x) for x in input_data[1:n+1]]
    print(sum(nums))
""",
        "Palindrome Check": """
import sys, re
s = sys.stdin.read().strip()
clean = re.sub(r'[^a-zA-Z0-9]', '', s).lower()
print("true" if clean == clean[::-1] else "false")
""",
        "Find the Maximum": """
import sys
input_data = sys.stdin.read().split()
if input_data:
    n = int(input_data[0])
    nums = [int(x) for x in input_data[1:n+1]]
    if nums: print(max(nums))
""",
        "FizzBuzz Sequence": """
import sys
n_str = sys.stdin.read().strip()
if n_str:
    n = int(n_str)
    res = []
    for i in range(1, n+1):
        if i % 3 == 0 and i % 5 == 0: res.append("FizzBuzz")
        elif i % 3 == 0: res.append("Fizz")
        elif i % 5 == 0: res.append("Buzz")
        else: res.append(str(i))
    print(" ".join(res))
""",
        "Vowel Counter": """
import sys
s = sys.stdin.read().strip()
vowels = "aeiou"
count = sum(1 for char in s.lower() if char in vowels)
print(count)
""",
        "Fibonacci Number": """
import sys
n_str = sys.stdin.read().strip()
if n_str:
    n = int(n_str)
    if n <= 0: print(0)
    elif n == 1: print(1)
    else:
        a, b = 0, 1
        for _ in range(2, n+1):
            a, b = b, a + b
        print(b)
"""
    }
    
    set_scores = {1: 0, 2: 0, 3: 0}
    
    for q_id, set_id, diff, title, tc_json in questions:
        print(f"Testing {title} (Set {set_id}, {diff})...")
        code = solutions.get(title)
        if not code:
            print(f"  ❌ No solution found for {title}")
            continue
            
        result = evaluate_code("python", code, tc_json)
        passed = result['passed_count']
        total = result['total_count']
        points = (60 if diff == 'hard' else 40) * (passed / total if total > 0 else 0)
        
        print(f"  Result: {passed}/{total} Passed -> {points} points")
        set_scores[set_id] += points

    print("\n--- Final Set Scores ---")
    for s_id, score in set_scores.items():
        print(f"Set {s_id}: {round(score)}%")
        
    conn.close()

if __name__ == "__main__":
    verify_all_coding_sets()
