from services.code_evaluator import evaluate_code
import sqlite3
import os
import json

def verify_java_cloud_sets():
    print("Verifying Java Cloud Fallback for all coding sets...")
    db_path = os.path.join(os.getcwd(), 'instance', 'synapselink.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, set_id, difficulty, title, test_cases_json FROM assessment_questions WHERE skill_name='CODING'")
    questions = cursor.fetchall()
    
    solutions = {
        "Sum of Array Elements": """
import java.util.Scanner;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        if (sc.hasNextInt()) {
            int n = sc.nextInt();
            long sum = 0;
            for (int i = 0; i < n; i++) {
                if (sc.hasNextInt()) sum += sc.nextInt();
            }
            System.out.println(sum);
        }
    }
}
""",
        "Palindrome Check": """
import java.util.Scanner;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        if (sc.hasNextLine()) {
            String s = sc.nextLine();
            String clean = s.replaceAll("[^a-zA-Z0-9]", "").toLowerCase();
            String reversed = new StringBuilder(clean).reverse().toString();
            System.out.println(clean.equals(reversed) ? "true" : "false");
        }
    }
}
""",
        "Find the Maximum": """
import java.util.Scanner;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        if (sc.hasNextInt()) {
            int n = sc.nextInt();
            int max = Integer.MIN_VALUE;
            for (int i = 0; i < n; i++) {
                if (sc.hasNextInt()) {
                    int val = sc.nextInt();
                    if (val > max) max = val;
                }
            }
            System.out.println(max);
        }
    }
}
""",
        "FizzBuzz Sequence": """
import java.util.Scanner;
import java.util.ArrayList;
import java.util.List;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        if (sc.hasNextInt()) {
            int n = sc.nextInt();
            List<String> res = new ArrayList<>();
            for (int i = 1; i <= n; i++) {
                if (i %3 == 0 && i % 5 == 0) res.add("FizzBuzz");
                else if (i % 3 == 0) res.add("Fizz");
                else if (i % 5 == 0) res.add("Buzz");
                else res.add(String.valueOf(i));
            }
            System.out.println(String.join(" ", res));
        }
    }
}
""",
        "Vowel Counter": """
import java.util.Scanner;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        if (sc.hasNextLine()) {
            String s = sc.nextLine().toLowerCase();
            int count = 0;
            for (char c : s.toCharArray()) {
                if ("aeiou".indexOf(c) != -1) count++;
            }
            System.out.println(count);
        }
    }
}
""",
        "Fibonacci Number": """
import java.util.Scanner;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        if (sc.hasNextInt()) {
            int n = sc.nextInt();
            if (n <= 0) System.out.println(0);
            else if (n == 1) System.out.println(1);
            else {
                long a = 0, b = 1;
                for (int i = 2; i <= n; i++) {
                    long t = a + b;
                    a = b;
                    b = t;
                }
                System.out.println(b);
            }
        }
    }
}
"""
    }
    
    for q_id, set_id, diff, title, tc_json in questions:
        print(f"Testing {title} (Set {set_id}, {diff}) via Cloud...")
        code = solutions.get(title)
        result = evaluate_code("java", code, tc_json)
        print(f"  Result: {result['passed_count']}/{result['total_count']} Passed")
        if result['passed_count'] != result['total_count']:
             print(f"  ⚠️ FAIL: {json.dumps(result['results'], indent=2)}")

    conn.close()

if __name__ == "__main__":
    verify_java_cloud_sets()
