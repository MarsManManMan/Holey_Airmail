Cornhole Pro 2.5
Automated Computer‑Vision Scoring System for Cornhole
Cornhole Pro 2.5 is an advanced automated scoring system for cornhole that uses computer vision, motion tracking, color detection, and stability logic to reliably recognize points during gameplay. It supports both Raspberry Pi Camera Module 3 (Picamera2) and USB webcams, and runs on Raspberry Pi OS (Bookworm) or any Linux/Windows/Mac desktop.
Cornhole Pro 2.5 includes:

Automatic bag detection using HSV color segmentation
Motion and stability analysis to avoid false detections
Live scoreboard (separate window)
Interactive ROI drawing (board rectangle + hole circle)
Fully integrated logging system (events, rounds, detections, errors)
Replay buffer (last 4 seconds)
Optional Flask web interface for remote scoreboard display/control
Automatic color calibration for perfect detection
Email match reports with ASCII graphs + AI-generated summaries
Full support for Raspberry Pi Camera Module 3 via Picamera2


📦 Features
✔ Automatic Scoring
The system detects and classifies:

Bag on board → 1 point
Bag in hole → 3 points

Only stable, stationary bags are counted to ensure accuracy.
✔ Motion & Stability Tracking
A bag must:

Stop moving
Remain inside the region for several consecutive frames

Before any points are awarded.
✔ Color Selection & Calibration

Manual color selection
Optional auto-calibration to measure HSV values under current lighting

✔ Realtime Interface

Live camera feed
Persistent scoreboard window
Buttons for Start / Pause / Reset / Manual scoring

✔ Web Interface
A built-in Flask UI allows any device on the same network to:

View the scoreboard
Control the match

✔ Comprehensive Logging
Outputs CSV + JSON files for:

Events
Bag detections
Round summaries
Errors


🚀 Installation (Raspberry Pi OS Bookworm)
1. Install Required System Dependencies (APT)
Shellsudo apt updatesudo apt install -y \    python3 python3-pip python3-opencv \    python3-numpy python3-flask python3-picamera2 \    python3-pil python3-matplotlib \    libatlas-base-dev libopenblas-dev liblapack-devMeer regels weergeven

2. Install Required Python Packages (PIP)
Shellpip3 install qrcode[pil]Meer regels weergeven
If your logging module is not included locally:
Shellpip3 install cornhole-loggingMeer regels weergeven

3. Enable Raspberry Pi Camera Module 3 (Picamera2)
Run:
Shellsudo raspi-configMeer regels weergeven
Navigate to:
Interface Options → Camera → Enable

Then reboot:
Shellsudo rebootMeer regels weergeven
Test Picamera2:
Shellpython3 - << 'EOF'from picamera2 import Picamera2Picamera2()print("Picamera2 is working!")EOFMeer regels weergeven

4. Required Local Files
📁 secretstuff.py
Create this file with your email credentials:
PythonverstuurEmailAdress = "your_email@gmail.com"Logincode = "your_gmail_app_password"Meer regels weergeven
Google requires an App Password (not your login password).
📁 cornhole_logging/
Must contain at least:

EventLogger
JSONLogger
DetectionLogger
RoundLogger
ErrorLogger

If using your own implementation, keep this folder in the project directory.

📂 Recommended Project Structure
CornholePro/
│
├── cornhole_pro.py
├── secretstuff.py
├── profiles.json
├── replays/
├── cornhole_logging/
│   ├── __init__.py
│   ├── event_logger.py
│   ├── json_logger.py
│   ├── detection_logger.py
│   ├── round_logger.py
│   └── error_logger.py
└── README.md


▶️ Running Cornhole Pro
From the project folder:
Shellpython3 cornhole_pro.py``Meer regels weergeven
You will be guided through:

Player color selection
Optional automatic color calibration
Drawing the board & hole ROIs
Starting the match

The scoreboard appears in a separate window.

🌐 Optional Web Interface
If enabled in the script:
Pythonflask_enabled = TrueMeer regels weergeven
Visit from any device on the network:
http://<raspberry_pi_ip>:5000

Example:
http://192.168.0.52:5000

This shows the live scoreboard and controls.

📊 Logging System
Cornhole Pro automatically generates:

cornhole_events.csv
cornhole_events.json
cornhole_detections.csv
cornhole_rounds.csv
cornhole_errors.csv

Useful for debugging, data analysis, statistics, or tournaments.

✉️ Email Match Reports
After each match, the system can send a full report including:

Final score
Accuracy graphs
Points-per-round
Color hitmaps
AI‑generated match summary

SMTP details are taken from secretstuff.py.

❗ Troubleshooting
Camera not working
Try:
Shelllibcamera-helloMeer regels weergeven
Black screen for USB webcam
Ensure legacy camera mode is disabled in raspi-config.
Picamera2 import error
You are likely running Raspberry Pi OS Bullseye.
Upgrade to Bookworm.
Flask interface unreachable
Check your local IP:
Shellhostname -IMeer regels weergeven

🧩 Planned Future Improvements

Machine learning bag classifier
Multi-camera support
Tournament brackets
Livestream overlay mode


❤️ Credits
Cornhole Pro 2.5 is a complete rewrite focusing on:

Modern Picamera2 stack
Clean architecture
Improved ROI system
Stable scoring logic
Extended logging
Better web interface