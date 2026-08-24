import re
import sys

file_path = "husky_ur5.py"
try:
    with open(file_path, "r") as f:
        content = f.read()

    # 1. Force rendering ON (if it was disabled)
    if "COV_ENABLE_RENDERING" in content:
        # Replace any occurrence that sets it to 0 with 1
        content = re.sub(r'p\.configureDebugVisualizer\(p\.COV_ENABLE_RENDERING,\s*0\)', 
                         'p.configureDebugVisualizer(p.COV_ENABLE_RENDERING, 1)', content)
        # Also ensure we have a line that sets it to 1 after world load
        pattern = r'(print\s*\(\s*["\']The world file is["\'],\s*args\.world\s*\))'
        replacement = r'\1\n\n    # Force rendering ON\n    p.configureDebugVisualizer(p.COV_ENABLE_RENDERING, 1)\n    time.sleep(0.5)  # let scene initialize'
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    else:
        print("Rendering lines not found; skipping.")
        sys.exit(0)

    # 2. Add a camera reset after the world is fully loaded (after print(id_lookup))
    # We'll insert after the line that prints id_lookup
    pattern = r'(print\s*\(\s*id_lookup\s*\))'
    replacement = r'\1\n\n    # ===== RESET CAMERA (full scene) =====\n    p.resetDebugVisualizerCamera(\n        cameraDistance=6.0,\n        cameraYaw=45,\n        cameraPitch=-30,\n        cameraTargetPosition=[0, 0, 0]\n    )\n    # ==================================='
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    with open(file_path, "w") as f:
        f.write(content)
    print("✅ Patched husky_ur5.py: rendering ON, camera reset after world load.")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
