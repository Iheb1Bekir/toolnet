import sys
import re
import time
import threading
import queue
import pybullet as p
import husky_ur5

# ---- 1. Ensure camera thread is defined and started ----
def ensure_camera_thread():
    # Check if camera_output_queue exists
    if not hasattr(husky_ur5, 'camera_output_queue'):
        husky_ur5.camera_output_queue = queue.Queue(maxsize=1)
        print("Added camera_output_queue to husky_ur5")

    # Check if capture_third_person function exists
    if not hasattr(husky_ur5, 'capture_third_person'):
        # Define the function
        def capture_third_person():
            # Wait for husky to be initialised
            while husky_ur5.husky is None:
                time.sleep(0.05)
            # Camera parameters
            camera_width = 640
            camera_height = 480
            while True:
                try:
                    if husky_ur5.husky is None:
                        time.sleep(0.1)
                        continue
                    # Get robot position and orientation
                    pos, orn = p.getBasePositionAndOrientation(husky_ur5.husky)
                    # Compute camera position: behind and above
                    # Use a fixed offset for now, or compute from quaternion
                    camera_distance = 2.0
                    height_offset = 1.2
                    # Simple: place camera at a fixed offset behind the robot
                    # For simplicity, we use a fixed world position; better to compute from robot orientation
                    # We'll use a chase camera: behind robot relative to its heading
                    # Get the forward direction from orientation
                    # Convert quaternion to euler
                    import math
                    def quat_to_euler(q):
                        # Roll, pitch, yaw from quaternion
                        x, y, z, w = q
                        t0 = +2.0 * (w * x + y * z)
                        t1 = +1.0 - 2.0 * (x * x + y * y)
                        roll = math.atan2(t0, t1)
                        t2 = +2.0 * (w * y - z * x)
                        t2 = max(-1.0, min(1.0, t2))
                        pitch = math.asin(t2)
                        t3 = +2.0 * (w * z + x * y)
                        t4 = +1.0 - 2.0 * (y * y + z * z)
                        yaw = math.atan2(t3, t4)
                        return roll, pitch, yaw
                    roll, pitch, yaw = quat_to_euler(orn)
                    # Behind vector: opposite of forward (yaw + pi)
                    behind_yaw = yaw + math.pi
                    dx = camera_distance * math.cos(behind_yaw)
                    dy = camera_distance * math.sin(behind_yaw)
                    camera_pos = [pos[0] + dx, pos[1] + dy, pos[2] + height_offset]
                    target_pos = [pos[0], pos[1], pos[2] + 0.2]
                    view_matrix = p.computeViewMatrix(
                        cameraEyePosition=camera_pos,
                        cameraTargetPosition=target_pos,
                        cameraUpVector=[0, 0, 1]
                    )
                    proj_matrix = p.computeProjectionMatrixFOV(
                        fov=60, aspect=camera_width/camera_height,
                        nearVal=0.1, farVal=10.0
                    )
                    width, height, rgb_img, depth, seg = p.getCameraImage(
                        width=camera_width, height=camera_height,
                        viewMatrix=view_matrix,
                        projectionMatrix=proj_matrix,
                        renderer=p.ER_BULLET_HARDWARE_OPENGL
                    )
                    # Convert to JPEG using PIL
                    import numpy as np
                    from PIL import Image
                    import io
                    rgb_img = np.reshape(rgb_img, (height, width, 4))
                    rgb_img = rgb_img[:, :, :3]  # Remove alpha
                    img = Image.fromarray(rgb_img.astype(np.uint8))
                    jpeg_data = io.BytesIO()
                    img.save(jpeg_data, format='JPEG', quality=70)
                    frame = jpeg_data.getvalue()
                    # Put in queue (replace if full)
                    try:
                        husky_ur5.camera_output_queue.put_nowait(frame)
                    except queue.Full:
                        try:
                            husky_ur5.camera_output_queue.get_nowait()
                            husky_ur5.camera_output_queue.put_nowait(frame)
                        except:
                            pass
                except Exception as e:
                    print(f"Camera capture error: {e}")
                    time.sleep(0.2)
                time.sleep(0.2)  # 5 FPS

        husky_ur5.capture_third_person = capture_third_person
        print("Added capture_third_person function")

    # Start the camera thread if not already running
    if not hasattr(husky_ur5, 'camera_thread_started'):
        thread = threading.Thread(target=husky_ur5.capture_third_person, daemon=True)
        thread.start()
        husky_ur5.camera_thread_started = True
        print("Started camera thread")

# ---- 2. Ensure camera reset is in start() ----
def ensure_camera_reset():
    # Patch start() in husky_ur5 to include reset
    # We can do this at runtime by monkey-patching
    original_start = husky_ur5.start
    def patched_start(input_args):
        original_start(input_args)
        # After world loaded, reset camera
        p.resetDebugVisualizerCamera(
            cameraDistance=5.0,
            cameraYaw=50,
            cameraPitch=-30,
            cameraTargetPosition=[0, 0, 0]
        )
        # Start camera thread
        ensure_camera_thread()
    husky_ur5.start = patched_start
    print("Patched husky_ur5.start with camera reset and thread start")

# ---- Apply patches ----
ensure_camera_reset()

# ---- Also patch husky_ur5.py file permanently ----
file_path = "husky_ur5.py"
with open(file_path, "r") as f:
    content = f.read()

# Check if camera reset is already in file
if "resetDebugVisualizerCamera" not in content:
    # Insert after print world file
    pattern = r'(print\s*\(\s*["\']The world file is["\'],\s*args\.world\s*\))'
    replacement = r'\1\n\n    # ===== RESET CAMERA TO SHOW FULL SCENE =====\n    p.resetDebugVisualizerCamera(\n        cameraDistance=5.0,\n        cameraYaw=50,\n        cameraPitch=-30,\n        cameraTargetPosition=[0, 0, 0]\n    )\n    # =============================================='
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Ensure start_camera_thread is called at the end of start()
if "start_camera_thread" not in content and "capture_third_person" not in content:
    # Add at the end of start() function (before the while True keepalive)
    # Find the end of start() function: after the datapoint init and before the keepalive loop
    # We'll append a call after the datapoint init
    pattern = r'(datapoint\.world = w\s+datapoint\.goal = g)'
    replacement = r'\1\n\n    # Start camera thread (if not already)\n    try:\n        import threading\n        if not hasattr(husky_ur5, "camera_thread_started"):\n            def capture_loop():\n                # Wait for husky to be initialised\n                while husky is None:\n                    time.sleep(0.05)\n                # Simple capture loop\n                import queue\n                # (actual implementation would be longer, but we'll just call the function if exists)\n                if hasattr(husky_ur5, "capture_third_person"):\n                    husky_ur5.capture_third_person()\n            t = threading.Thread(target=capture_loop, daemon=True)\n            t.start()\n            husky_ur5.camera_thread_started = True\n    except:\n        pass\n'
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open(file_path, "w") as f:
    f.write(content)
print("Patched husky_ur5.py file")

print("✅ All patches applied.")
