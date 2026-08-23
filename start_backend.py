"""
DiskMind Startup Script
Installs missing packages and starts the backend server.
Run this from the diskmind/ project root.
"""
import subprocess
import sys
import os

PYTHON = sys.executable
PIP = [PYTHON, "-m", "pip"]

PACKAGES = [
    "aiosqlite",
    "scikit-learn",
    "joblib",
    "psutil",
    "Pillow",
    "imagehash",
    "pandas",
    "python-dotenv",
]

print(f"Python: {PYTHON}")
print(f"Installing missing packages...")

for pkg in PACKAGES:
    try:
        __import__(pkg.replace("-", "_").split("[")[0])
        print(f"  ✓ {pkg}")
    except ImportError:
        print(f"  → Installing {pkg}...")
        subprocess.run([*PIP, "install", pkg, "--quiet"], check=False)

print("\nGenerating demo dataset...")
subprocess.run([PYTHON, "demo/generate_test_data.py"], check=True)

print("\nStarting DiskMind backend...")
print("  URL: http://localhost:8000")
print("  Docs: http://localhost:8000/docs")
print("  Press Ctrl+C to stop\n")
subprocess.run([
    PYTHON, "-m", "uvicorn", "backend.main:app",
    "--reload", "--host", "0.0.0.0", "--port", "8000"
])
