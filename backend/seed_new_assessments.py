import json
import os
from app import create_app
from extensions import db
import models

def seed_sql_questions():
    app = create_app()
    # Force instance-relative path to be absolute
    db_path = os.path.join(os.getcwd(), 'instance', 'synapselink.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    
    with app.app_context():
        db.create_all()
        from models.assessment_models import AssessmentQuestion
        AssessmentQuestion.query.filter_by(skill_name='SQL').delete()

        easy_q = AssessmentQuestion(
            skill_name='SQL',
            difficulty='easy',
            title='List Employee Names in Marketing',
            description="You are given a table 'employees' and 'departments'.\nWrite a query to find the names of all employees who work in the 'Marketing' department.\nResult should contain only the 'name' column.",
            input_format="Tables: employees (id, name, dept_id), departments (id, name)",
            output_format="A single column 'name'",
            sample_input="Employees: (1, 'Alice', 1), (2, 'Bob', 2). Depts: (1, 'Marketing'), (2, 'Sales')",
            sample_output="'Alice'",
            constraints="Return names as they appear in the table.",
            schema_details="CREATE TABLE departments (id INTEGER PRIMARY KEY, name TEXT NOT NULL); CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT NOT NULL, dept_id INTEGER, FOREIGN KEY(dept_id) REFERENCES departments(id));",
            test_cases_json=json.dumps([
                {"is_sample": True, "setup_sql": "INSERT INTO departments VALUES (1, 'Marketing'), (2, 'Sales'); INSERT INTO employees VALUES (1, 'Alice', 1), (2, 'Bob', 2);", "expected_results": [["Alice"]]},
                {"is_sample": False, "setup_sql": "INSERT INTO departments VALUES (1, 'Marketing'), (2, 'Sales'), (3, 'Engineering'); INSERT INTO employees VALUES (1, 'John', 1), (2, 'Jane', 1), (3, 'Mike', 2), (4, 'Sarah', 3);", "expected_results": [["John"], ["Jane"]]}
            ])
        )

        hard_q = AssessmentQuestion(
            skill_name='SQL',
            difficulty='hard',
            title='Find Departments with High Average Salary',
            description="Write a query to list the names of all departments where the average salary of employees is greater than 50,000.\nResult should contain the department name and the average salary (aliased as 'avg_salary').",
            input_format="Tables: departments (id, name), employees (id, name, salary, dept_id)",
            output_format="Columns: name, avg_salary",
            sample_input="Depts: (1, 'HR'). Employees: (1, 'A', 60000, 1), (2, 'B', 40000, 1)",
            sample_output="'HR', 50000",
            constraints="Average salary should be exact.",
            schema_details="CREATE TABLE departments (id INTEGER PRIMARY KEY, name TEXT NOT NULL); CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT NOT NULL, salary INTEGER, dept_id INTEGER, FOREIGN KEY(dept_id) REFERENCES departments(id));",
            test_cases_json=json.dumps([
                {"is_sample": True, "setup_sql": "INSERT INTO departments VALUES (1, 'IT'), (2, 'HR'); INSERT INTO employees VALUES (1, 'Dev1', 60000, 1), (2, 'Dev2', 70000, 1), (3, 'HR1', 40000, 2);", "expected_results": [["IT", 65000.0]]},
                {"is_sample": False, "setup_sql": "INSERT INTO departments VALUES (1, 'Sales'), (2, 'R&D'), (3, 'Mgmt'); INSERT INTO employees VALUES (1, 'S1', 40000, 1), (2, 'S2', 45000, 1), (3, 'R1', 90000, 2), (4, 'R2', 10000, 2), (5, 'M1', 100000, 3);", "expected_results": [["R&D", 50000.0], ["Mgmt", 100000.0]]}
            ])
        )

        db.session.add(easy_q)
        db.session.add(hard_q)
        db.session.commit()
        print("SQL Questions seeded successfully.")

if __name__ == "__main__":
    seed_sql_questions()
