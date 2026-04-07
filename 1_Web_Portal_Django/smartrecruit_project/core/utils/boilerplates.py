"""
core/utils/boilerplates.py
==========================
Language-specific starter code for the Polyglot Coding Assessment Engine.
"""

BOILERPLATES = {
    'python': 'def solution():\n    # Write your logic here\n    print("Hello, SmartRecruit")\n\nsolution()',
    
    'javascript': 'function solution() {\n    // Write your logic here\n    console.log("Hello, SmartRecruit");\n}\n\nsolution();',
    
    'go': 'package main\n\nimport "fmt"\n\nfunc main() {\n    // Write your logic here\n    fmt.Println("Hello, SmartRecruit")\n}',
    
    'rust': 'fn main() {\n    // Write your logic here\n    println!("Hello, SmartRecruit");\n}',
    
    'java': 'public class Main {\n    public static void main(String[] args) {\n        // Write your logic here\n        System.out.println("Hello, SmartRecruit");\n    }\n}',

    'cpp': '#include <iostream>\n\nint main() {\n    // Write your logic here\n    std::cout << "Hello, SmartRecruit" << std::endl;\n    return 0;\n}',
}

def get_boilerplate(language: str) -> str:
    """Return the starter code for a given language."""
    return BOILERPLATES.get(language.lower(), BOILERPLATES['python'])
