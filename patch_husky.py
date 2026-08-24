import re, sys
file_path = "husky_ur5.py"
with open(file_path, "r") as f:
    content = f.read()

# Insert the camera code after the destroy() function
pattern = r'(def destroy\(\):.*?p\.disconnect\(\))'
camera_code = r'''\1

# ========== CAMERA FEED ==========
import threading
import queue
import time
import numpy as np
from PIL import Image
import io

camera_output_queue = queue.Queue(maxsize=1)
camera_thread_started = False

def capture_third_person():
    global husky, camera_output_queue, camera_thread_started
    while husky is None:
        time.sleep(0.05)
    print("Camera thread started")
    width, height = 640, 480
    while True:
        try:
            pos, orn = p.getBasePositionAndOrientation(husky)
            import math
            def quat_to_euler(q):
                x, y, z, w = q
                t0 = +2.0 * (w * x + y * z)
                t1 = +1.0 - 2.0 * (x*x + y*y)
                roll = math.atan2(t0, t1)
                t2 = +2.0 * (w*y - z*x)
                t2 = max(-1.0, min(1.0, t2))
                pitch = math.asin(t2)
                t3 = +2.0 * (w*z + x*y)
                t4 = +1.0 - 2.0 * (y*y + z*z)
                yaw = math.atan2(t3, t4)
                return roll, pitch, yaw
            _, _, yaw = quat_to_euler(orn)
            camera_distance = 2.5
            height_offset = 1.2
            behind_yaw = yaw + math.pi
            dx = camera_distance * math.cos(behind_yaw)
            dy = camera_distance * math.sin(behind_yaw)
            camera_pos = [pos[0] + dx, pos[1] + dy, pos[2] + height_offset]
            target_pos = [pos[0], pos[1], pos[2] + 0.3]
            view_matrix = p.computeViewMatrix(
                cameraEyePosition=camera_pos,
                cameraTargetPosition=target_pos,
                cameraUpVector=[0,0,1]
            )
            proj_matrix = p.computeProjectionMatrixFOV(
                fov=60, aspect=width/height,
                nearVal=0.1, farVal=10.0
            )
            w_img, h_img, rgb_img, depth, seg = p.getCameraImage(
                width=width, height=height,
                viewMatrix=view_matrix,
                projectionMatrix=proj_matrix,
                renderer=p.ER_BULLET_HARDWARE_OPENGL
            )
            rgb_img = np.reshape(rgb_img, (h_img, w_img, 4))
            rgb_img = rgb_img[:, :, :3]
            img = Image.fromarray(rgb_img.astype(np.uint8))
            jpeg_data = io.BytesIO()
            img.save(jpeg_data, format='JPEG', quality=70)
            frame = jpeg_data.getvalue()
            try:
                camera_output_queue.put_nowait(frame)
            except queue.Full:
                try:
                    camera_output_queue.get_nowait()
                    camera_output_queue.put_nowait(frame)
                except:
                    pass
        except Exception as e:
            print("Camera capture error:", e)
            time.sleep(0.2)
        time.sleep(0.2)  # 5 FPS

def start_camera_thread():
    global camera_thread_started
    if not camera_thread_started:
        thread = threading.Thread(target=capture_third_person, daemon=True)
        thread.start()
        camera_thread_started = True
        print("Camera thread started")
'''
content = re.sub(pattern, camera_code, content, flags=re.DOTALL)

# Add rendering enable and camera reset after print("The world file is", args.world)
pattern = r'(print\s*\(\s*["\']The world file is["\'],\s*args\.world\s*\))'
replacement = r'''\1

    # Force rendering ON
    p.configureDebugVisualizer(p.COV_ENABLE_RENDERING, 1)

    # Reset camera to show full scene
    p.resetDebugVisualizerCamera(
        cameraDistance=6.0,
        cameraYaw=45,
        cameraPitch=-30,
        cameraTargetPosition=[0, 0, 0]
    )
'''
content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Call start_camera_thread() at the end of start()
pattern = r'(datapoint\.goal = g\s*)'
replacement = r'\1\n\n    # Start camera thread\n    start_camera_thread()\n'
content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write back
with open(file_path, "w") as f:
    f.write(content)
print("✅ Patched husky_ur5.py with camera feed and fixes.")
