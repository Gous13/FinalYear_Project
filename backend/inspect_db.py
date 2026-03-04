import sqlite3
import os

def inspect_db():
    db_path = os.path.join(os.getcwd(), 'instance', 'synapselink.db')
    if not os.path.exists(db_path):
        print("DB not found")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("--- Assessment Questions ---")
    cursor.execute("SELECT id, skill_name, set_id, difficulty, title FROM assessment_questions")
    rows = cursor.fetchall()
    for row in rows:
        print(f"ID: {row[0]}, Skill: {row[1]}, Set: {row[2]}, Diff: {row[3]}, Title: {row[4]}")
        
    print("\n--- Question Counts per Skill and Set ---")
    cursor.execute("SELECT skill_name, set_id, COUNT(*) FROM assessment_questions GROUP BY skill_name, set_id")
    rows = cursor.fetchall()
    for row in rows:
        print(f"Skill: {row[0]}, Set: {row[1]}, Count: {row[2]}")

    conn.close()

if __name__ == "__main__":
    inspect_db()
