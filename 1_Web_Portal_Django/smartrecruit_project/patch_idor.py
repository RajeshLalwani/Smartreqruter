import os
import re
import glob

# The directory containing the Django views
views_dir = r"C:\Users\ASUS\Documents\Tech Elecon Pvt. Ltd\Project\SmartRecruit\1_Web_Portal_Django\smartrecruit_project\jobs"

# Find all python files starting with 'views'
view_files = glob.glob(os.path.join(views_dir, "views*.py"))

# Regex patterns to find vulnerable lookups. We target simple lookups that don't already check user/recruiter
pattern1 = re.compile(r"get_object_or_404\(\s*Application\s*,\s*id\s*=\s*application_id\s*\)")
pattern2 = re.compile(r"get_object_or_404\(\s*Application\s*,\s*pk\s*=\s*application_id\s*\)")

# Replacement string
replacement = "get_authorized_application(request, application_id)"

patched_files_count = 0
patch_count = 0

for file_path in view_files:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Step 1: Ensure security is imported
    if "from .security import get_authorized_application" not in content and (pattern1.search(content) or pattern2.search(content)):
        # Inject import right below from django.shortcuts import ...
        content = re.sub(
            r"(from django\.shortcuts import.*)",
            r"\1\nfrom .security import get_authorized_application",
            content,
            count=1
        )
        # Fallback if no django.shortcuts
        if "from .security import get_authorized_application" not in content:
             content = "from .security import get_authorized_application\n" + content

    # Step 2: Replace vulnerable usages
    original_content = content
    content = pattern1.sub(replacement, content)
    content = pattern2.sub(replacement, content)
    
    if content != original_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        patched_files_count += 1
        
        # Count replacements
        diff1 = len(pattern1.findall(original_content)) - len(pattern1.findall(content))
        diff2 = len(pattern2.findall(original_content)) - len(pattern2.findall(content))
        
        # Just manual counting of instances patched roughly
        patch_count += (len(re.findall(r"get_authorized_application\(request, application_id\)", content)) - 
                        len(re.findall(r"get_authorized_application\(request, application_id\)", original_content)))

print(f"Patched {patched_files_count} files.")
print(f"Total vulnerable instances secured: {patch_count}")
