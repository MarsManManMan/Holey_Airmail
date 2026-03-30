Cornhole Pro 2.5
Automated Computer‑Vision Scoring System for Cornhole
Cornhole Pro 2.5 is an advanced automated scoring system for cornhole that uses computer vision, motion tracking, color detection, and stability logic to reliably recognize scoring events. It supports both Raspberry Pi Camera Module 3 (Picamera2) and USB webcams, and runs on Raspberry Pi OS (Bookworm) as well as Linux, Windows, and macOS.
The system provides automatic scoring, ROI drawing tools, a live scoreboard, comprehensive logging, optional color calibration, a replay buffer, and an optional Flask web interface for remote scoreboard viewing and control.

Features
Automatic Scoring
The system detects and classifies:

Bag on board: 1 point
Bag in hole: 3 points

Points are only awarded once the bag has fully stopped moving.
Motion and Stability Tracking
To prevent false detections:

The bag must stop moving
The bag must remain inside the detection region for several consecutive frames

Color Selection and Calibration

Manual color selection
Optional automatic HSV calibration based on current lighting conditions

Realtime Visual Interface

Live camera feed
Always-visible scoreboard window
Controls for starting, pausing, resetting, and adjusting scores

Optional Web Interface
A built-in Flask UI allows any device on the same network to view and control the scoreboard.
Logging System
All events are logged to CSV and JSON:

Bag detections
Events
Round summaries
Error logs


Installation (Raspberry Pi OS Bookworm)
1. Required System Packages (APT)
Install system dependencies:
Shellsudo apt updatesudo apt install -y \    python3 python3-pip python3-opencv \    python3-numpy python3-flask python3-picamera2 \    python3-pil python3-matplotlib \    libatlas-base-dev libopenblas-dev liblapack-devMeer regels weergeven

2. Required Python Packages (PIP)
Install the additional Python dependencies:
Shellpip3 install qrcode[pil]Meer regels weergeven
If your logging module is external:
Shellpip3 install cornhole-loggingMeer regels weergeven

3. Raspberry Pi Camera Setup (Picamera2)
Enable the camera:
Shellsudo raspi-configMeer regels weergeven
Navigate to:
Interface Options → Camera → Enable

Reboot:
Shellsudo rebootMeer regels weergeven
Test Picamera2:
Shellpython3 - << 'EOF'from picamera2 import Picamera2Picamera2()print("Picamera2 is working.")EOFMeer regels weergeven

Required Files
secretstuff.py
Create this file inside the project directory:
PythonverstuurEmailAdress = "your_email@gmail.com"Logincode = "your_gmail_app_password"Meer regels weergeven
Google requires an App Password for SMTP.
cornhole_logging/
This folder must contain the logging classes:

EventLogger
JSONLogger
DetectionLogger
RoundLogger
ErrorLogger


Recommended Project Structure
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


Running Cornhole Pro
In the project directory:
Shellpython3 cornhole_pro.pyMeer regels weergeven
The program guides you through:

Selecting player bag colors
Optional HSV calibration
Drawing the board rectangle and hole circle
Starting the match

A separate scoreboard window will remain visible.

Web Interface (Optional)
If enabled in the script:
Pythonflask_enabled = TrueMeer regels weergeven
You can access the scoreboard from any device on the same network:
http://<raspberry_pi_ip>:5000

Example:
http://192.168.0.52:5000


Logging
The system automatically generates:

cornhole_events.csv
cornhole_events.json
cornhole_detections.csv
cornhole_rounds.csv
cornhole_errors.csv

These logs are useful for debugging, analytics, tournaments, and post‑game review.

Email Match Reports
After a match, Cornhole Pro can send a detailed email including:

Final score
Accuracy graphs
Points per round
Color hitmaps
AI-generated match summary

SMTP settings are retrieved from secretstuff.py
