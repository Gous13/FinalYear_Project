from services.code_evaluator import evaluate_code
import json

def verify_java_fallback():
    print("Testing Java execution with transparent Judge0 fallback...")
    
    java_code = """
public class Main {
    public static void main(String[] args) {
        java.util.Scanner sc = new java.util.Scanner(System.in);
        if (sc.hasNextInt()) {
            int n = sc.nextInt();
            System.out.println(n * 2);
        }
    }
}
"""
    test_cases = [
        {"input": "5", "expected_output": "10"},
        {"input": "100", "expected_output": "200"}
    ]
    test_cases_json = json.dumps(test_cases)
    
    result = evaluate_code("java", java_code, test_cases_json)
    
    print(f"Result: {json.dumps(result, indent=2)}")
    
    if result.get('passed_count') == 2:
        print("\n✅ VERIFICATION SUCCESSFUL: Java code executed via Cloud Fallback!")
    else:
        print("\n❌ VERIFICATION FAILED.")

if __name__ == "__main__":
    verify_java_fallback()
