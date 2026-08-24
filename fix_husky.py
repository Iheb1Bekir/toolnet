import re
import sys

file_path = "husky_ur5.py"

# First, restore a clean version (remove the broken patch if present)
# We'll read the file, find the start() function, and add the keep-alive correctly.
try:
    with open(file_path, "r") as f:
        content = f.read()

    # Remove any existing broken keep-alive block (search for "KEEP THE PROCESS ALIVE")
    # We'll simply remove everything between that comment and the next function.
    # Simpler: we'll replace the entire start() function with a corrected version.
    # But we can't do that blindly. Let's remove the broken block if it exists.
    pattern = r'# ===== KEEP THE PROCESS ALIVE =====.*?# ===================================\n'
    content = re.sub(pattern, '', content, flags=re.DOTALL)

    # Now add the correct keep-alive at the end of the start() function.
    # Find where the start() function ends (the next 'def' or end of file).
    # We'll add it before the next function definition, or at the end.
    # Look for the line that defines the next function (e.g., "def changeView")
    # But we'll insert it after datapoint.goal = g and before the closing of start().
    # We'll use a marker: after "datapoint.goal = g" (which is near the end of start())
    pattern = r'(datapoint\.goal = g\s*)'
    replacement = r'\1\n\n    # ===== KEEP THE PROCESS ALIVE =====\n    # This prevents the main thread from exiting, which would close PyBullet.\n    try:\n        while True:\n            time.sleep(1)   # idle forever\n    except KeyboardInterrupt:\n        print("Shutting down PyBullet...")\n        p.disconnect()\n        raise\n    # ===================================\n'
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    with open(file_path, "w") as f:
        f.write(content)
    print("✅ Fixed husky_ur5.py with correct keep-alive")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
