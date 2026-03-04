import sqlite3
import json
import os

db_path = os.path.join(os.getcwd(), 'instance', 'synapselink.db')
print(f"Connecting to {db_path}...")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. DROP AND RECREATE TABLES
print("Dropping and recreating tables for schema sync...")
cursor.executescript("""
DROP TABLE IF EXISTS assessment_questions;
CREATE TABLE assessment_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_name TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    input_format TEXT,
    output_format TEXT,
    sample_input TEXT,
    sample_output TEXT,
    constraints TEXT,
    schema_details TEXT,
    test_cases_json TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
""")

# 2. SEED DATA
print("Seeding SQL questions with fixed logic...")

# Easy Question
easy_desc = "Write a query to find the names of all employees in the 'Marketing' department.\nResult should contain only the 'name' column."
easy_schema = "CREATE TABLE departments (id INTEGER PRIMARY KEY, name TEXT NOT NULL); CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT NOT NULL, dept_id INTEGER, FOREIGN KEY(dept_id) REFERENCES departments(id));"
easy_tests = json.dumps([
    {"is_sample": True, "setup_sql": "INSERT INTO departments VALUES (1, 'Marketing'), (2, 'Sales'); INSERT INTO employees VALUES (1, 'Alice', 1), (2, 'Bob', 2);", "expected_results": [["Alice"]]},
    {"is_sample": False, "setup_sql": "INSERT INTO departments VALUES (1, 'Marketing'), (2, 'Sales'), (3, 'Engineering'); INSERT INTO employees VALUES (1, 'John', 1), (2, 'Jane', 1), (3, 'Mike', 2), (4, 'Sarah', 3);", "expected_results": [["John"], ["Jane"]]}
])

# Hard Question - Fixed "at least" description to match the 50,000 check
hard_desc = "Write a query to list the names of all departments where the average salary of employees is AT LEAST 50,000.\nResult should contain the department name and the average salary (alias: 'avg_salary')."
hard_schema = "CREATE TABLE departments (id INTEGER PRIMARY KEY, name TEXT NOT NULL); CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT NOT NULL, salary INTEGER, dept_id INTEGER, FOREIGN KEY(dept_id) REFERENCES departments(id));"
hard_tests = json.dumps([
    {"is_sample": True, "setup_sql": "INSERT INTO departments VALUES (1, 'IT'), (2, 'HR'); INSERT INTO employees VALUES (1, 'Dev1', 60000, 1), (2, 'Dev2', 70000, 1), (3, 'HR1', 40000, 2);", "expected_results": [["IT", 65000.0]]},
    {"is_sample": False, "setup_sql": "INSERT INTO departments VALUES (1, 'Sales'), (2, 'R&D'), (3, 'Mgmt'); INSERT INTO employees VALUES (1, 'S1', 40000, 1), (2, 'S2', 45000, 1), (3, 'R1', 90000, 2), (4, 'R2', 10000, 2), (5, 'M1', 100000, 3);", "expected_results": [["R&D", 50000.0], ["Mgmt", 100000.0]]}
])

cursor.execute("""
INSERT INTO assessment_questions (skill_name, difficulty, title, description, input_format, output_format, sample_input, sample_output, constraints, schema_details, test_cases_json)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", ('SQL', 'easy', 'Marketing Personnel', easy_desc, 'employees(id, name, dept_id), departments(id, name)', 'name', 'Employees in Marketing', 'Alice', 'None', easy_schema, easy_tests))

cursor.execute("""
INSERT INTO assessment_questions (skill_name, difficulty, title, description, input_format, output_format, sample_input, sample_output, constraints, schema_details, test_cases_json)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", ('SQL', 'hard', 'High-Profit Departments', hard_desc, 'departments(id, name), employees(id, name, salary, dept_id)', 'name, avg_salary', 'IT (Avg 65000)', 'IT, 65000', 'Exact average', hard_schema, hard_tests))

conn.commit()
conn.close()
print("Seed finished.")
