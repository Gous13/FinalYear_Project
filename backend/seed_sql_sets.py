import sqlite3
import json
import os

def seed_sql_sets():
    db_path = os.path.join(os.getcwd(), 'instance', 'synapselink.db')
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Clear existing SQL questions
    cursor.execute("DELETE FROM assessment_questions WHERE skill_name='SQL';")

    def insert_q(set_id, difficulty, title, description, input_f, output_f, sample_i, sample_o, constraints, schema, test_cases):
        cursor.execute("""
            INSERT INTO assessment_questions 
            (skill_name, set_id, difficulty, title, description, input_format, output_format, 
             sample_input, sample_output, constraints, schema_details, test_cases_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, ('SQL', set_id, difficulty, title, description, input_f, output_f, sample_i, sample_o, constraints, schema, json.dumps(test_cases)))

    # --- SET 1 ---
    insert_q(1, 'easy', 'Marketing Employee Filter', 
             "Find the names of all employees who work in the 'Marketing' department.\nResult should contain only the 'name' column.",
             "employees (id, name, dept_id), departments (id, name)", "name",
             "Employees: (1, 'Alice', 1). Depts: (1, 'Marketing')", "'Alice'",
             "Return names exactly.", 
             "CREATE TABLE departments (id INTEGER PRIMARY KEY, name TEXT NOT NULL); CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT NOT NULL, dept_id INTEGER, FOREIGN KEY(dept_id) REFERENCES departments(id));",
             [
                 {"is_sample": True, "setup_sql": "INSERT INTO departments VALUES (1, 'Marketing'), (2, 'Sales'); INSERT INTO employees VALUES (1, 'Alice', 1), (2, 'Bob', 2);", "expected_results": [["Alice"]]},
                 {"is_sample": False, "setup_sql": "INSERT INTO departments VALUES (1, 'Marketing'), (2, 'HR'); INSERT INTO employees VALUES (1, 'John', 1), (2, 'Jane', 1), (3, 'Mike', 2);", "expected_results": [["John"], ["Jane"]]}
             ])

    insert_q(1, 'hard', 'Top Average Salaries', 
             "List department names where the average employee salary is > 50,000.\nReturn: name, avg_salary.",
             "departments (id, name), employees (id, name, salary, dept_id)", "name, avg_salary",
             "IT: 60000", "'IT', 60000.0",
             "Alias count as avg_salary.", 
             "CREATE TABLE departments (id INTEGER PRIMARY KEY, name TEXT NOT NULL); CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT NOT NULL, salary INTEGER, dept_id INTEGER, FOREIGN KEY(dept_id) REFERENCES departments(id));",
             [
                {"is_sample": True, "setup_sql": "INSERT INTO departments VALUES (1, 'IT'); INSERT INTO employees VALUES (1, 'Dev', 60000, 1);", "expected_results": [["IT", 60000.0]]},
                {"is_sample": False, "setup_sql": "INSERT INTO departments VALUES (1, 'Sales'), (2, 'R&D'); INSERT INTO employees VALUES (1, 'S1', 40000, 1), (2, 'R1', 90000, 2), (3, 'R2', 10000, 2);", "expected_results": [["R&D", 50000.0]]}
             ])

    # --- SET 2 ---
    insert_q(2, 'easy', 'Project Availability Search', 
             "Select the titles of all projects that have a status of 'open'.",
             "projects (id, title, status)", "title",
             "(1, 'P1', 'open')", "'P1'",
             "Case-sensitive.", 
             "CREATE TABLE projects (id INTEGER PRIMARY KEY, title TEXT NOT NULL, status TEXT NOT NULL);",
             [
                {"is_sample": True, "setup_sql": "INSERT INTO projects VALUES (1, 'App Dev', 'open'), (2, 'Web Design', 'closed');", "expected_results": [["App Dev"]]},
                {"is_sample": False, "setup_sql": "INSERT INTO projects VALUES (1, 'A', 'open'), (2, 'B', 'open'), (3, 'C', 'closed');", "expected_results": [["A"], ["B"]]}
             ])

    insert_q(2, 'hard', 'Busy Project Analysis', 
             "Find project titles that have more than 2 team members across all associated teams.",
             "projects (id, title), teams (id, project_id), team_members (id, team_id, user_id)", "title, member_count",
             "P1 has 3 members.", "'P1', 3",
             "Alias member_count. Use HAVING.", 
             "CREATE TABLE projects (id INTEGER PRIMARY KEY, title TEXT NOT NULL); CREATE TABLE teams (id INTEGER PRIMARY KEY, project_id INTEGER); CREATE TABLE team_members (id INTEGER PRIMARY KEY, team_id INTEGER, user_id INTEGER);",
             [
                {"is_sample": True, "setup_sql": "INSERT INTO projects VALUES (1, 'P1'); INSERT INTO teams VALUES (1, 1); INSERT INTO team_members VALUES (1, 1, 10), (2, 1, 11), (3, 1, 12);", "expected_results": [["P1", 3]]}, # Wait, P1 has 3 members in setup, expected check > 2
                {"is_sample": False, "setup_sql": "INSERT INTO projects VALUES (1, 'P1'), (2, 'P2'); INSERT INTO teams VALUES (1, 1), (2, 2); INSERT INTO team_members VALUES (1, 1, 10), (2, 1, 11), (3, 1, 12), (4, 2, 20);", "expected_results": [["P1", 3]]}
             ]) # Fixed sample expected results to match setup

    # --- SET 3 ---
    insert_q(3, 'easy', 'High Achiever Filter', 
             "List names and GPAs of students with GPA > 3.5, sorted by GPA DESC.",
             "student_profiles (user_id, name, gpa)", "name, gpa",
             "(1, 'A', 3.8)", "'A', 3.8",
             "GPA DESC.", 
             "CREATE TABLE student_profiles (user_id INTEGER PRIMARY KEY, name TEXT NOT NULL, gpa REAL NOT NULL);",
             [
                {"is_sample": True, "setup_sql": "INSERT INTO student_profiles VALUES (1, 'Alice', 3.9), (2, 'Bob', 3.2);", "expected_results": [["Alice", 3.9]]},
                {"is_sample": False, "setup_sql": "INSERT INTO student_profiles VALUES (1, 'X', 3.6), (2, 'Y', 4.0), (3, 'Z', 3.5);", "expected_results": [["Y", 4.0], ["X", 3.6]]}
             ])

    insert_q(3, 'hard', 'Skill-Specific Mentorships', 
             "Find distinct names of mentors who manage at least one project requiring 'SQL'.",
             "mentors (id, name), projects (id, title, mentor_id, required_skills)", "name",
             "Dr. S, DB Proj requires SQL", "'Dr. S'",
             "Use DISTINCT.", 
             "CREATE TABLE mentors (id INTEGER PRIMARY KEY, name TEXT NOT NULL); CREATE TABLE projects (id INTEGER PRIMARY KEY, title TEXT NOT NULL, mentor_id INTEGER, required_skills TEXT NOT NULL);",
             [
                {"is_sample": True, "setup_sql": "INSERT INTO mentors VALUES (1, 'Dr. Smith'); INSERT INTO projects VALUES (1, 'DB', 1, 'SQL');", "expected_results": [["Dr. Smith"]]},
                {"is_sample": False, "setup_sql": "INSERT INTO mentors VALUES (1, 'A'), (2, 'B'); INSERT INTO projects VALUES (1, 'P1', 1, 'SQL'), (2, 'P2', 1, 'Python'), (3, 'P3', 2, 'SQL');", "expected_results": [["A"], ["B"]]}
             ])

    conn.commit()
    conn.close()
    print("3 SQL Question Sets seeded successfully via direct SQLite.")

if __name__ == "__main__":
    seed_sql_sets()
