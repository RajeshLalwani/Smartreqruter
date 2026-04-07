import os
import sys

# Add the root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Resume_Parser.parser import ResumeParser

def test_parser():
    print("Testing ML/DL Resume Parser initialization...")
    parser = ResumeParser()
    
    # Create a dummy text file to simulate a resume
    test_file = "test_resume.txt"
    with open(test_file, 'w') as f:
        f.write("""
        John Doe
        johndoe@email.com
        555-123-4567
        
        Software Engineer with 5 years of experience building scalable web applications.
        
        Skills:
        - Python, Django, Flask
        - JavaScript, React, Node.js
        - Docker, AWS, CI/CD
        - Deep Learning, Machine Learning, TensorFlow
        
        Education:
        Bachelor of Science in Computer Science - University of Tech 2020
        """)
        
    print(f"\nParsing {test_file}...")
    result = parser.parse(test_file)
    
    print("\nExtraction Results:")
    print("-------------------")
    print(f"Skills: {result.get('skills')}")
    print(f"Email: {result.get('email')}")
    print(f"Phone: {result.get('phone')}")
    
    # Clean up
    if os.path.exists(test_file):
        os.remove(test_file)
        
if __name__ == "__main__":
    test_parser()
