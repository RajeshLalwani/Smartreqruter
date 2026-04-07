import os
import ast
import subprocess

PROJECT_DIR = r"C:\Users\ASUS\Documents\Tech Elecon Pvt. Ltd\Project\SmartRecruit\1_Web_Portal_Django\smartrecruit_project"

def check_python_syntax():
    print("--- Checking Python Syntax ---")
    errors = 0
    for root, _, files in os.walk(PROJECT_DIR):
        if 'venv' in root or '.venv' in root or '__pycache__' in root:
            continue
        for f in files:
            if f.endswith('.py'):
                path = os.path.join(root, f)
                try:
                    with open(path, 'r', encoding='utf-8') as file:
                        source = file.read()
                    ast.parse(source, filename=path)
                except SyntaxError as e:
                    print(f"Syntax Error in {path}: {e}")
                    errors += 1
                except Exception as e:
                    print(f"Error reading {path}: {e}")
    if errors == 0:
        print("All Python files have valid syntax.\n")
    else:
        print(f"Found {errors} syntax errors.\n")

def check_django():
    print("--- Running manage.py check ---")
    os.chdir(PROJECT_DIR)
    result = subprocess.run(['python', 'manage.py', 'check'], capture_output=True, text=True)
    if result.returncode == 0:
        print("manage.py check passed.")
        if result.stderr:
            print("Warnings:")
            print(result.stderr)
    else:
        print("manage.py check failed:")
        print(result.stderr)
        print(result.stdout)
    print("\n")

if __name__ == "__main__":
    check_python_syntax()
    check_django()
