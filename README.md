# ToolNet “ Robot Simulation Platform

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/Flask-3.x-000000.svg" alt="Flask" />
  <img src="https://img.shields.io/badge/PyBullet-Enabled-3B82F6.svg" alt="PyBullet" />
  <img src="https://img.shields.io/badge/License-BSD--2--Clause-orange.svg" alt="BSD-2-Clause" />
</p>

ToolNet is a modern web-based robot simulation platform for task planning, action execution, and goal-driven automation in a PyBullet environment. The dashboard is the primary interface for interacting with a simulated Husky mobile robot equipped with a UR5 arm and gripper, enabling users to orchestrate robot actions, stream live camera data, record task sequences, and replay goal-driven behaviors.

The project has been refactored around a streamlined, glass-morphism control dashboard with real-time monitoring, action composition, and reusable mission playback workflows. It supports both headless and graphical rendering modes, making it easier to run in local development environments, remote labs, or GPU-accelerated workstations.


## ?? Demo Videos

Watch the videos below to see ToolNet in action – click the play button on each.

### 1. Recording a Goal
<video width="100%" controls>
  <source src="demo/demo1.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>

### 2. Playing Back a Goal
<video width="100%" controls>
  <source src="demo/demo2.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>

### 3. Dashboard Walkthrough
<video width="100%" controls>
  <source src="demo/demo3.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>

## ?? Demo Videos

Watch these short videos to see ToolNet in action – click the play button on each.

### 1. Recording a Goal
<video width="100%" controls>
  <source src="demo/demo1.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>

### 2. Playing Back a Goal
<video width="100%" controls>
  <source src="demo/demo2.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>

### 3. Dashboard Walkthrough
<video width="100%" controls>
  <source src="demo/demo3.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Quick Start

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

The dashboard is now the primary user experience, and the legacy tutorial pages have been removed in favor of a cleaner mission-control workflow.

## Key Features

- Headless or GUI PyBullet simulation support
- Embedded live MJPEG camera feed for robot monitoring
- Action Composer with dynamic argument selection and execution
- Goal recording and playback for saved action chains
- Undo and rollback support for failed or partial actions
- Modern dark dashboard with glass-morphism styling
- RTX GPU acceleration support for improved rendering performance
- Reusable, editable goal definitions for task automation workflows

## System Requirements

- Python 3.11 or newer
- PyBullet
- Flask
- NumPy
- OpenCV / image streaming support
- A compatible graphics driver for GUI rendering (optional if running headless)
- Optional: NVIDIA RTX-enabled environment for accelerated simulation performance

## Installation

1. Clone the repository:

```bash
git clone https://github.com/your-org/toolnet.git
cd toolnet
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Launch the platform:

```bash
python app.py
```

Then visit:

```text
http://127.0.0.1:5000
```

### Typical workflow

- Select a goal or mission configuration from the available options.
- Use the action composer to define and execute robot commands.
- Monitor the current scene and camera feed from the control dashboard.
- Record a sequence of actions as a reusable goal.
- Replay saved actions step-by-step or run the full goal automatically.
- If an action fails, use the rollback/undo flow to recover or adjust the sequence.

## Configuration

The application is designed to run in both desktop and headless environments.

Common setup considerations:

- Use GUI mode when a local display is available.
- Use headless mode when running in a server or remote environment without an attached monitor.
- Ensure the PYTHONPATH and virtual environment are correctly activated before launching the app.
- If using GPU-accelerated rendering, verify that PyBullet and the installed graphics stack are compatible with your hardware.

Example environment hints:

```bash
export DISPLAY=:0
python app.py
```

For headless/CI environments, prefer the no-GUI configuration and verify that camera streaming and simulation threads initialize correctly.

## Project Structure

```text
.
â”œâ”€â”€ app.py                  # Main Flask application entry point
â”œâ”€â”€ README.md               # Project overview and usage docs
â”œâ”€â”€ LICENSE                 # BSD-2-Clause license
â”œâ”€â”€ requirements.txt        # Python dependencies
â”œâ”€â”€ dataset/                # Training and evaluation data folders
â”œâ”€â”€ jsons/                  # Scene, action, predicate, and goal definitions
â”œâ”€â”€ models/                 # Meshes, URDFs, and simulation assets
â”œâ”€â”€ src/                    # Core simulation, parser, utilities, and model logic
â”œâ”€â”€ static/                 # Front-end assets and dashboard resources
â”œâ”€â”€ templates/              # Web templates and UI views
â”œâ”€â”€ logs/                   # Runtime logs and outputs
â”œâ”€â”€ train.py                # Training pipeline entry point
â”œâ”€â”€ validate_toolnet.py     # Validation and sanity-check tooling
â”œâ”€â”€ generate_synthetic_dataset.py
â”œâ”€â”€ fix_*.py                # Utility patches and compatibility fixes
â””â”€â”€ ...
```

## License

This project is licensed under the BSD-2-Clause License.

Copyright (c) 2026, iHEB BEKIR
All rights reserved.

See the [LICENSE](LICENSE) file for the full terms.

## Acknowledgments

This project builds on earlier work and original research from the following contributors and teams:

- Rajas Bansal
- Shreshth Tuli
- Rohan Paul
- Mausam

Their foundational work on robot planning, tool use prediction, and simulator-based task execution established the basis for the current platform. The modern dashboard and workflow tooling extend that original research into a more accessible interactive simulation environment.

## Contact

For questions, contributions, or deployment support, please open an issue or contact the project maintainer.


## ?? Demo Videos

Watch these short videos to see ToolNet in action:

- [Recording a Goal](demo/demo1.mp4) – Record a sequence of actions and save it as a reusable goal.
- [Playing Back a Goal](demo/demo2.mp4) – Execute a saved goal automatically.
- [Dashboard Walkthrough](demo/demo3.mp4) – Explore the modern dark dashboard and its features.
