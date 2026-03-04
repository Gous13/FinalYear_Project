import sqlite3
import os

def migrate():
    db_path = os.path.join(os.getcwd(), 'instance', 'synapselink.db')
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Add set_id to assessment_questions
    try:
        cursor.execute("ALTER TABLE assessment_questions ADD COLUMN set_id INTEGER;")
        print("Added set_id to assessment_questions")
    except sqlite3.OperationalError as e:
        print(f"assessment_questions: {e}")

    # Add assigned_set_id to skill_assessments
    try:
        cursor.execute("ALTER TABLE skill_assessments ADD COLUMN assigned_set_id INTEGER;")
        print("Added assigned_set_id to skill_assessments")
    except sqlite3.OperationalError as e:
        print(f"skill_assessments: {e}")

    conn.commit()
    conn.close()
    print("Migration check complete.")

if __name__ == "__main__":
    migrate()
