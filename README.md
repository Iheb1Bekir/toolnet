````markdown
# ToolNet – Robot Simulation Platform

[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-BSD--2--Clause-green.svg)](LICENSE)
[![Flask](https://img.shields.io/badge/flask-3.1.0-lightgrey.svg)](https://flask.palletsprojects.com)
[![PyBullet](https://img.shields.io/badge/pybullet-3.2.7-orange.svg)](https://pybullet.org)

**ToolNet** is a modern web-based robot simulation platform that combines Flask, PyBullet, and a sleek glass-morphism dashboard. It allows users to command a simulated Husky robot equipped with a UR5 robotic arm and Robotiq gripper, record action sequences, and replay them as reusable goals.

---

## ✨ Key Features

- 🎮 **Interactive Robot Control** – Control a simulated robot directly from a web interface.
- 📷 **Live Camera Feed** – Low-latency MJPEG stream (640×480 @ 8 FPS) with a third-person follow camera.
- 🖥️ **External 3D View** – Optional PyBullet GUI window for full 3D visualization.
- 🎯 **Action Composer** – Build custom actions (`moveTo`, `pick`, `place`, etc.) using dynamic argument dropdowns.
- 🧠 **Goal Recording & Playback** – Record action sequences and save them as reusable goals.
- ↩️ **Undo / Rollback System** – Automatic state snapshots with rollback on failure.
- 🎨 **Modern Dashboard** – Responsive dark glass-morphism interface with real-time logs and status updates.
- ⚡ **Performance Optimized** – 120 Hz physics stepping, bounded camera FPS, and GPU acceleration support.
- 📝 **Persistent User Goals** – Saved goals remain available after restarting the application.

---

## 🎬 Demo Videos

- 📹 **Recording a Goal** – Demonstrates recording and saving custom goals.
- 📹 **Dashboard Walkthrough** – Overview of the dashboard, controls, and workflow.

---

## 📦 System Requirements

### Software

- Python **3.11+**
- Pip (latest version)
- Virtual Environment (recommended)

### Supported Operating Systems

- Windows 10 / 11
- Linux
- macOS

### Recommended Hardware

| Component | Minimum | Recommended |
|------------|----------|-------------|
| CPU | 2 Cores | 4+ Cores |
| RAM | 4 GB | 8+ GB |
| GPU | Integrated Graphics | NVIDIA RTX or equivalent |

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Iheb1Bekir/toolnet.git
cd toolnet
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv-launch
```

### 3. Activate the Virtual Environment

#### Windows

```powershell
.\.venv-launch\Scripts\Activate.ps1
```

#### Linux / macOS

```bash
source .venv-launch/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Start ToolNet

```bash
python app.py
```

### 6. Open the Dashboard

Navigate to:

```text
http://127.0.0.1:5000
```

---

## 🎮 Usage Guide

### Selecting a World and Goal

1. Select a world from the **World** dropdown.
2. Select a saved goal from the **Goal** dropdown.
3. Built-in goals remain hidden from the user interface.
4. To create a new goal, follow the recording procedure below.

---

### Recording and Saving a Goal

1. Press the **Record** button (🔴).
2. Create actions using the **Action Composer**.
3. Execute actions one by one.
4. Press **Record** again to stop recording.
5. Click **+ New Goal**.
6. Enter a goal name.
7. Click **Save Goal**.

Your goal is immediately stored and remains available after application restarts.

---

### Playing Back a Goal

1. Select a goal.
2. Press **Start**.
3. Use:
   - **Next** to execute actions step-by-step.
   - **Run All** to execute the entire goal automatically.

---

### Keyboard Shortcuts

| Key | Function |
|------|----------|
| N | Next Action |
| R | Reset Simulation |
| U | Undo Last Action |
| Space | Start / Run All |

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|-----------|-------------|----------|
| `PYBULLET_USE_SOFTWARE` | Force software rendering | `0` |
| `PYBULLET_USE_OPENGL` | OpenGL rendering mode | unset |
| `TOOLNET_RENDERER` | Camera renderer (`hardware` or `tiny`) | `hardware` |

---

### Command-Line Arguments

| Argument | Description |
|-----------|-------------|
| `--world` | Load a specific world JSON |
| `--goal` | Load a built-in goal JSON |
| `--randomize` | Randomize world and goal |
| `--headless` | Run without PyBullet GUI |
| `--display` | Display mode (`none`, `camera`, `both`) |

---

## 📂 Project Structure

```text
toolnet/
├── app.py
├── camera_service.py
├── rollback_manager.py
├── goal_manager.py
├── action_validator.py
├── command_bus.py
├── husky_ur5.py
├── src/
├── jsons/
│   ├── goals/
│   └── user_goals/
├── templates/
│   └── index.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
├── logs/
├── demo/
│   ├── demo1.mp4
│   └── demo3.mp4
├── requirements.txt
├── LICENSE
└── README.md
```

---

## 🧪 Troubleshooting

### PyBullet GUI Appears Blank

- Zoom out using the mouse wheel.
- Rotate the view using right-click + drag.
- Enable software rendering:

```powershell
$env:PYBULLET_USE_SOFTWARE="1"
```

- Set Python to **High Performance GPU** mode in Windows Graphics Settings.

---

### Camera Feed Is Slow

Reduce camera load by:

- Increasing sleep time in `camera_service.py`
- Lowering resolution to `320×240`
- Disabling shadows:

```python
p.configureDebugVisualizer(
    p.COV_ENABLE_SHADOWS,
    0
)
```

---

### Goals Are Not Saving

Verify:

- The folder `jsons/user_goals/` exists.
- The application has write permissions.
- No antivirus is blocking file creation.

---

## 🏗️ Architecture Overview

ToolNet combines several independent services:

### Backend

- Flask Web Server
- Command Bus
- Goal Manager
- Rollback Manager
- Action Validator
- Camera Service

### Simulation Layer

- PyBullet Physics Engine
- Husky Mobile Robot
- UR5 Manipulator
- Robotiq Gripper

### Frontend

- HTML5 Dashboard
- Vanilla JavaScript
- Real-Time Status Updates
- Glass-Morphism UI

---

## 📄 License

This project is licensed under the **BSD-2-Clause License**.

See the LICENSE file for full details.

Copyright © 2026 **Iheb Bekir**

---

## 🙏 Acknowledgments

ToolNet is derived from the original ToolNet research project:

- Rajas Bansal
- Shreshth Tuli
- Rohan Paul
- Mausam

Original Repository:

https://github.com/reail-iitd/commonsense-task-planning

This version has been extensively redesigned and enhanced with:

- Goal Recording System
- Persistent User Goals
- Live Camera Streaming
- Modern Dashboard Interface
- Rollback and Recovery System
- Performance Optimizations
- Improved User Experience

---

## 🤝 Contributing

Contributions are welcome.

1. Fork the repository.
2. Create a feature branch:

```bash
git checkout -b feature/amazing-feature
```

3. Commit your changes:

```bash
git commit -m "Add amazing feature"
```

4. Push your branch:

```bash
git push origin feature/amazing-feature
```

5. Open a Pull Request.

---

## 📞 Contact

**Maintainer:** Iheb Bekir

GitHub:

https://github.com/Iheb1Bekir

---

## ⭐ Support the Project

If you find ToolNet useful:

- ⭐ Star the repository
- 🐛 Report bugs
- 💡 Suggest features
- 🤝 Contribute improvements

---

**Enjoy controlling your robot! 🤖**
````
