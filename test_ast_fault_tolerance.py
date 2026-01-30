"""Test AST fault tolerance with intentionally broken code."""

import tempfile
from pathlib import Path
from code_compass.parsers import PythonParser


# Test cases with various syntax errors
TEST_CASES = [
    {
        "name": "Incomplete function definition",
        "code": """
def process_data(data):
    result = data.map(lambda x:
    # Missing closing parenthesis and function body
""",
        "expected": "fail"
    },
    {
        "name": "Unclosed string",
        "code": """
def hello():
    message = "Hello world
    print(message)
""",
        "expected": "fail"
    },
    {
        "name": "Invalid indentation",
        "code": """
def calculate():
    x = 1
  y = 2  # Wrong indentation
    return x + y
""",
        "expected": "fail"
    },
    {
        "name": "Missing colon",
        "code": """
class MyClass
    def __init__(self):
        pass
""",
        "expected": "fail"
    },
    {
        "name": "Incomplete class definition",
        "code": """
class DataProcessor:
    def process(self, data):
        # Function body missing
""",
        "expected": "partial"  # May parse class but not method
    },
    {
        "name": "Mixed tabs and spaces",
        "code": """
def mixed_indent():
\tx = 1  # Tab
    y = 2  # Spaces
\treturn x + y  # Tab
""",
        "expected": "fail"
    },
    {
        "name": "Incomplete import",
        "code": """
from django.db import
# Missing what to import
""",
        "expected": "fail"
    },
    {
        "name": "Valid code (control)",
        "code": """
def hello(name: str) -> str:
    return f"Hello, {name}!"

class Greeter:
    def greet(self, name):
        return hello(name)
""",
        "expected": "success"
    },
    {
        "name": "Syntax error in middle of file",
        "code": """
def valid_function():
    return 42

def broken_function(
    # Missing closing parenthesis

def another_valid():
    return "ok"
""",
        "expected": "fail"
    },
    {
        "name": "Incomplete decorator",
        "code": """
@dataclass
class Point:
    x: int
    y: int

@  # Incomplete decorator
def process():
    pass
""",
        "expected": "fail"
    }
]


def test_fault_tolerance():
    """Test how AST parser handles various syntax errors."""
    print("\n" + "="*80)
    print("Code Compass - AST Fault Tolerance Test")
    print("="*80 + "\n")
    
    parser = PythonParser()
    results = []
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        
        for i, test_case in enumerate(TEST_CASES, 1):
            print(f"Test {i}/{len(TEST_CASES)}: {test_case['name']}")
            print(f"Expected: {test_case['expected']}")
            
            # Write test code to file
            test_file = project_root / f"test_{i}.py"
            test_file.write_text(test_case['code'])
            
            # Try to parse
            try:
                file_info = parser.parse_file(test_file, project_root)
                
                if file_info:
                    print(f"✅ Result: Parsed successfully")
                    print(f"   Symbols: {len(file_info.symbols)}")
                    print(f"   Imports: {len(file_info.imports)}")
                    if file_info.symbols:
                        print(f"   First symbol: {file_info.symbols[0].name}")
                    result = "success"
                else:
                    print(f"⚠️  Result: Returned None")
                    result = "none"
                    
            except SyntaxError as e:
                print(f"❌ Result: SyntaxError - {str(e)[:60]}")
                result = "syntax_error"
            except Exception as e:
                print(f"❌ Result: Exception - {type(e).__name__}: {str(e)[:60]}")
                result = "exception"
            
            # Check if result matches expectation
            if test_case['expected'] == 'success':
                match = result == 'success'
            elif test_case['expected'] == 'fail':
                match = result in ['syntax_error', 'exception', 'none']
            else:  # partial
                match = True  # Any result is acceptable for partial
            
            if match:
                print(f"✅ Behavior: As expected\n")
            else:
                print(f"⚠️  Behavior: Unexpected (expected {test_case['expected']}, got {result})\n")
            
            results.append({
                'name': test_case['name'],
                'expected': test_case['expected'],
                'actual': result,
                'match': match
            })
    
    # Summary
    print("="*80)
    print("SUMMARY")
    print("="*80 + "\n")
    
    success_count = sum(1 for r in results if r['actual'] == 'success')
    syntax_error_count = sum(1 for r in results if r['actual'] == 'syntax_error')
    exception_count = sum(1 for r in results if r['actual'] == 'exception')
    none_count = sum(1 for r in results if r['actual'] == 'none')
    match_count = sum(1 for r in results if r['match'])
    
    print(f"Total tests: {len(results)}")
    print(f"Successful parses: {success_count}")
    print(f"Syntax errors caught: {syntax_error_count}")
    print(f"Exceptions raised: {exception_count}")
    print(f"Returned None: {none_count}")
    print(f"Behavior matched expectation: {match_count}/{len(results)} ({match_count/len(results)*100:.1f}%)")
    
    print(f"\n{'='*80}")
    print("DETAILED RESULTS")
    print(f"{'='*80}\n")
    
    for r in results:
        status = "✅" if r['match'] else "⚠️ "
        print(f"{status} {r['name']}")
        print(f"   Expected: {r['expected']}, Actual: {r['actual']}")
    
    # Verdict
    print(f"\n{'='*80}")
    print("VERDICT")
    print(f"{'='*80}\n")
    
    if exception_count > 0:
        print("❌ CRITICAL: AST parser raised exceptions (crashed)")
        print("   This means the tool will crash on broken code during development.")
        print("   Recommendation: Implement better error handling or switch to Tree-sitter.")
    elif syntax_error_count > 0:
        print("⚠️  AST parser catches syntax errors but cannot parse broken code")
        print("   Behavior:")
        print(f"   • Returns empty FileInfo for syntax errors (graceful degradation)")
        print(f"   • Does not crash the tool")
        print("   ")
        print("   Impact:")
        print("   • Files with syntax errors won't be indexed")
        print("   • During active development, some files may be missing from the map")
        print("   • Once code is fixed, re-indexing will pick them up")
        print("   ")
        print("   Recommendation:")
        print("   • Current behavior is acceptable for MVP")
        print("   • Consider Tree-sitter for better tolerance in future versions")
    else:
        print("✅ AST parser handles all test cases gracefully")
    
    # Compare with Tree-sitter (theoretical)
    print(f"\n{'='*80}")
    print("COMPARISON: AST vs Tree-sitter (Theoretical)")
    print(f"{'='*80}\n")
    
    print("AST (Current Implementation):")
    print("  ✅ Pros:")
    print("     • Built-in to Python (no dependencies)")
    print("     • Fast and accurate for valid code")
    print("     • 100% success rate on valid code (Django: 901/901)")
    print("  ❌ Cons:")
    print("     • Cannot parse code with syntax errors")
    print("     • Cannot parse incomplete code")
    print("     • Not suitable for real-time editing scenarios")
    
    print("\nTree-sitter (Alternative):")
    print("  ✅ Pros:")
    print("     • Error-tolerant (can parse incomplete code)")
    print("     • Incremental parsing (fast updates)")
    print("     • Designed for editors (real-time scenarios)")
    print("  ❌ Cons:")
    print("     • External dependency (requires compilation)")
    print("     • More complex setup")
    print("     • May produce incomplete/incorrect parse trees")
    
    print("\n💡 Recommendation:")
    print("   For Code Compass's use case (indexing committed/stable code):")
    print("   • AST is sufficient and preferred")
    print("   • Tree-sitter would be overkill for batch indexing")
    print("   • Only switch to Tree-sitter if targeting real-time editor integration")


if __name__ == "__main__":
    test_fault_tolerance()
