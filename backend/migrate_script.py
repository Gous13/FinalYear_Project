
import os
import sqlite3
from datetime import datetime

db_path = 'instance/synapselink.db'
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def get_columns(table_name):
    cursor.execute(f"PRAGMA table_info({table_name});")
    return [col[1] for col in cursor.fetchall()]

def table_exists(table_name):
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
    return cursor.fetchone() is not None

def migrate():
    print("Starting manual migration...")
    
    # 1. Handle skill_assessments (legacy MCQ vs new StudentSkill)
    if table_exists('skill_assessments'):
        cols = get_columns('skill_assessments')
        if 'question_text' in cols and 'user_id' not in cols:
            print("Detected legacy MCQ table in 'skill_assessments'. Renaming to 'mcq_assessment_questions'...")
            if table_exists('mcq_assessment_questions'):
                cursor.execute("DROP TABLE mcq_assessment_questions;")
            cursor.execute("ALTER TABLE skill_assessments RENAME TO mcq_assessment_questions;")
    
    if table_exists('student_skills') and not table_exists('skill_assessments'):
        print("Renaming 'student_skills' to 'skill_assessments'...")
        cursor.execute("ALTER TABLE student_skills RENAME TO skill_assessments;")
    
    # 2. Update columns in skill_assessments (StudentSkill)
    if table_exists('skill_assessments'):
        cols = get_columns('skill_assessments')
        if 'assessment_score' in cols and 'score' not in cols:
            print("Renaming 'assessment_score' to 'score' in 'skill_assessments'...")
            cursor.execute("ALTER TABLE skill_assessments RENAME COLUMN assessment_score TO score;")
    
    # 3. Update columns in assessment_questions
    if table_exists('assessment_questions'):
        cols = get_columns('assessment_questions')
        if 'question_title' in cols and 'title' not in cols:
            print("Renaming 'question_title' to 'title' in 'assessment_questions'...")
            cursor.execute("ALTER TABLE assessment_questions RENAME COLUMN question_title TO title;")
        if 'question_text' in cols and 'description' not in cols:
            print("Renaming 'question_text' to 'description' in 'assessment_questions'...")
            cursor.execute("ALTER TABLE assessment_questions RENAME COLUMN question_text TO description;")
        if 'table_schema' not in cols:
            print("Adding 'table_schema' to 'assessment_questions'...")
            cursor.execute("ALTER TABLE assessment_questions ADD COLUMN table_schema TEXT;")

    # 4. Update columns in assessment_attempts
    if table_exists('assessment_attempts'):
        cols = get_columns('assessment_attempts')
        if 'timestamp' in cols and 'created_at' not in cols:
            print("Renaming 'timestamp' to 'created_at' in 'assessment_attempts'...")
            cursor.execute("ALTER TABLE assessment_attempts RENAME COLUMN timestamp TO created_at;")
        if 'set_id' in cols and 'question_id' not in cols:
            print("Note: assessment_attempts schema change (set_id -> question_id) might need data migration. Renaming for now if possible...")
            # SQLite doesn't always support RENAME COLUMN in older versions, but it should on modern ones.
            try:
                cursor.execute("ALTER TABLE assessment_attempts RENAME COLUMN set_id TO question_id;")
            except Exception as e:
                print(f"Warning: Could not rename set_id to question_id: {e}")

    # 5. Handle mcq_assessment_results vs skill_assessment_results
    if table_exists('skill_assessment_results') and not table_exists('mcq_assessment_results'):
        print("Renaming 'skill_assessment_results' to 'mcq_assessment_results'...")
        cursor.execute("ALTER TABLE skill_assessment_results RENAME TO mcq_assessment_results;")

    conn.commit()
    print("Migration finished successfully.")

try:
    migrate()
except Exception as e:
    print(f"Migration failed: {e}")
finally:
    conn.close()
