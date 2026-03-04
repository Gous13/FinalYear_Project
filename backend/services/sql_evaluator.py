import sqlite3
import json

def evaluate_sql(user_query, schema_ddl, test_cases_json):
    """
    SQL evaluation logic:
    - execute student query on prepared SQLite test database
    - compare returned rows with expected results
    - ignore row ordering unless explicitly required
    - return number of passed test cases
    """
    try:
        test_cases = json.loads(test_cases_json)
    except Exception:
        return {"error": "Invalid test cases format"}

    passed_count = 0
    total_count = len(test_cases)
    results = []

    for tc in test_cases:
        # Create an in-memory database for each test case to ensure isolation
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        
        try:
            # 1. Setup schema
            cursor.executescript(schema_ddl)
            
            # 2. Setup initial data for the test case
            setup_sql = tc.get('setup_sql', '')
            if setup_sql:
                cursor.executescript(setup_sql)
            
            # 3. Execute user query
            cursor.execute(user_query)
            user_results = cursor.fetchall()
            
            # 4. Get expected results
            # Expected results should ideally be provided as a result of a reference query 
            # or a static list of tuples in the test case.
            expected_results = tc.get('expected_results', [])
            
            # Normalize results for comparison (ignore order)
            # We convert each row to a sorted tuple if order doesn't matter
            # Requirement says: "ignore row ordering unless explicitly required"
            # We'll assume order doesn't matter by default.
            
            def normalize(rows):
                # Sort rows and convert to list of lists for easy JSON serialization if needed
                return sorted([list(row) for row in rows])

            if normalize(user_results) == normalize(expected_results):
                passed_count += 1
                results.append({"passed": True, "message": "Test case passed"})
            else:
                results.append({
                    "passed": False, 
                    "message": "Results do not match expected output",
                    "expected": expected_results,
                    "actual": user_results
                })
                
        except sqlite3.Error as e:
            results.append({"passed": False, "message": f"SQL Error: {str(e)}"})
        finally:
            conn.close()

    return {
        "passed_count": passed_count,
        "total_count": total_count,
        "results": results,
        "score": (passed_count / total_count * 100) if total_count > 0 else 0
    }
