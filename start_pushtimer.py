#!/usr/bin/env python3
"""
Standalone Pushup Timer Starter
"""
import os
import sys
import subprocess

def main():
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Activate virtual environment
    venv_python = os.path.join(script_dir, "venv", "bin", "python")
    
    if not os.path.exists(venv_python):
        print("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], cwd=script_dir)
        
        # Install PySide6
        venv_pip = os.path.join(script_dir, "venv", "bin", "pip")
        subprocess.run([venv_pip, "install", "PySide6"], cwd=script_dir)
    
    # Run the main application
    main_script = os.path.join(script_dir, "main.py")
    subprocess.run([venv_python, main_script])

if __name__ == "__main__":
    main()
