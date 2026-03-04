import sqlite3
import json
import os

def seed_coding_sets():
    db_path = os.path.join(os.getcwd(), 'instance', 'synapselink.db')
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Clear existing CODING questions
    cursor.execute("DELETE FROM assessment_questions WHERE skill_name='CODING';")

    def insert_q(set_id, difficulty, title, description, input_f, output_f, sample_i, sample_o, constraints, test_cases):
        cursor.execute("""
            INSERT INTO assessment_questions 
            (skill_name, set_id, difficulty, title, description, input_format, output_format, 
             sample_input, sample_output, constraints, test_cases_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, ('CODING', set_id, difficulty, title, description, input_f, output_f, sample_i, sample_o, constraints, json.dumps(test_cases)))

    # --- SET 1 ---
    # Easy: Sum of Array
    insert_q(1, 'easy', 'Sum of Array Elements', 
             "Write a program that reads an integer N followed by N integers. Output the sum of the N integers.",
             "An integer N, then N integers.", "The sum of the integers.",
             "3\n1 2 3", "6",
             "1 <= N <= 100",
             [
                 {"is_sample": True, "input": "3\n1 2 3", "expected_output": "6"},
                 {"is_sample": False, "input": "5\n10 -2 3 0 7", "expected_output": "18"}
             ])

    # Hard: Palindrome String
    insert_q(1, 'hard', 'Palindrome Check', 
             "Read a string and determine if it is a palindrome (reads same forward and backward), ignoring case and non-alphanumeric characters. Output 'true' or 'false'.",
             "A line of text.", "'true' or 'false'",
             "A man, a plan, a canal: Panama", "true",
             "Input length < 1000.",
             [
                 {"is_sample": True, "input": "A man, a plan, a canal: Panama", "expected_output": "true"},
                 {"is_sample": False, "input": "race a car", "expected_output": "false"},
                 {"is_sample": False, "input": "aba", "expected_output": "true"}
             ])

    # --- SET 2 ---
    # Easy: Find Maximum
    insert_q(2, 'easy', 'Find the Maximum', 
             "Read N integers and find the maximum value among them.",
             "Integer N, then N integers.", "The maximum integer.",
             "4\n1 9 4 5", "9",
             "N >= 1",
             [
                {"is_sample": True, "input": "4\n1 9 4 5", "expected_output": "9"},
                {"is_sample": False, "input": "3\n-5 -10 -2", "expected_output": "-2"}
             ])

    # Hard: FizzBuzz Sequence
    insert_q(2, 'hard', 'FizzBuzz Sequence', 
             "Given an integer N, print numbers from 1 to N. For multiples of 3, print 'Fizz'. For multiples of 5, print 'Buzz'. For multiples of both, print 'FizzBuzz'. Output should be space-separated.",
             "An integer N.", "Space separated string.",
             "5", "1 2 Fizz 4 Buzz",
             "1 <= N <= 50",
             [
                {"is_sample": True, "input": "5", "expected_output": "1 2 Fizz 4 Buzz"},
                {"is_sample": False, "input": "15", "expected_output": "1 2 Fizz 4 Buzz Fizz 7 8 Fizz Buzz 11 Fizz 13 14 FizzBuzz"}
             ])

    # --- SET 3 ---
    # Easy: Count Vowels
    insert_q(3, 'easy', 'Vowel Counter', 
             "Given a string, count the number of vowels (a, e, i, o, u) in it (regardless of case).",
             "A string.", "The count of vowels.",
             "Hello", "2",
             "String length < 100",
             [
                {"is_sample": True, "input": "Hello", "expected_output": "2"},
                {"is_sample": False, "input": "SynapseLink", "expected_output": "3"}
             ])

    # Hard: N-th Fibonacci
    insert_q(3, 'hard', 'Fibonacci Number', 
             "Calculate the N-th Fibonacci number. Fib(0)=0, Fib(1)=1, Fib(N) = Fib(N-1) + Fib(N-2).",
             "Integer N.", "The Fibonacci number.",
             "10", "55",
             "0 <= N <= 30",
             [
                {"is_sample": True, "input": "10", "expected_output": "55"},
                {"is_sample": False, "input": "0", "expected_output": "0"},
                {"is_sample": False, "input": "1", "expected_output": "1"},
                {"is_sample": False, "input": "20", "expected_output": "6765"}
             ])

    conn.commit()
    conn.close()
    print("3 logical CODING Question Sets seeded successfully.")

if __name__ == "__main__":
    seed_coding_sets()
