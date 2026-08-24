import re
import sys

file_path = "husky_ur5.py"
try:
    with open(file_path, "r") as f:
        content = f.read()

    # Check if the keep-alive loop already exists
    if "while True:" in content and "time.sleep(1)" in content and "keep alive" in content.lower():
        print("✅ Keep-alive loop already present; skipping.")
        sys.exit(0)

    # Find the end of the start() function – look for the final 'except KeyboardInterrupt' or the end of the function.
    # We'll add the loop right after the datapoint initialization and before the function ends.
    # Look for the line: datapoint.goal = g
    # and insert the keep-alive after that.
    pattern = r'(datapoint\.goal = g\s*)'
    replacement = r'\1\n\n    # ===== KEEP THE PROCESS ALIVE =====\n    # This prevents the main thread from exiting, which would close PyBullet.\n    try:\n        while True:\n            time.sleep(1)   # idle forever\n    except KeyboardInterrupt:\n        print("Shutting down PyBullet...")\n        p.disconnect()\n        raise\n    # ===================================\n'
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    if new_content != content:
        with open(file_path, "w") as f:
            f.write(new_content)
        print("✅ Added keep-alive loop to husky_ur5.py")
    else:
        print("⚠️ Could not insert keep-alive loop; skipping.")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
