import sqlite3
import os
import json

def debug_scoring():
    db_path = os.path.join(os.getcwd(), 'instance', 'synapselink.db')
    if not os.path.exists(db_path):
        print("DB not found")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("--- Recent Assessment Attempts ---")
    cursor.execute("""
        SELECT a.id, a.skill_name, a.question_id, q.title, a.score, a.passed, a.created_at
        FROM assessment_attempts a
        JOIN assessment_questions q ON a.question_id = q.id
        ORDER BY a.created_at DESC
        LIMIT 20
    """)
    rows = cursor.fetchall()
    for row in rows:
        print(f"AttemptID: {row[0]}, Skill: {row[1]}, Q: {row[3]}, Score: {row[4]}, Passed: {row[5]}")

    print("\n--- Detailed Seed Data for CODING ---")
    cursor.execute("SELECT id, set_id, difficulty, title, test_cases_json FROM assessment_questions WHERE skill_name='CODING'")
    rows = cursor.fetchall()
    for row in rows:
        tc = json.loads(row[4])
        print(f"ID: {row[0]}, Set: {row[1]}, Diff: {row[2]}, Title: {row[3]}, TC_Count: {len(tc)}")
        for i, case in enumerate(tc):
            print(f"  TC {i+1}: Input={repr(case.get('input'))}, Expected={repr(case.get('expected_output'))}")

    conn.close()

if __name__ == "__main__":
    debug_scoring()
