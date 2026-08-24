import re, sys
file_path = "src/initialise.py"
with open(file_path, "r") as f:
    content = f.read()

# Find the line that loads the gripper and replace it with the flagged version
pattern = r'(gripper_id\s*=\s*p\.loadURDF\s*\(\s*["\']models/urdf/robotiq_85\.urdf["\'],?\s*[^)]*\))'
replacement = '''gripper_id = p.loadURDF(
    "models/urdf/robotiq_85.urdf",
    basePosition=[0,0,0],
    baseOrientation=[0,0,0,1],
    useFixedBase=True,
    flags=p.URDF_USE_SELF_COLLISION | p.URDF_USE_SELF_COLLISION_EXCLUDE_ALL_PARENT
)'''
new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
if new_content != content:
    with open(file_path, "w") as f:
        f.write(new_content)
    print("✅ Patched gripper loading in src/initialise.py")
else:
    print("⚠️ Could not find gripper line; skipping.")
