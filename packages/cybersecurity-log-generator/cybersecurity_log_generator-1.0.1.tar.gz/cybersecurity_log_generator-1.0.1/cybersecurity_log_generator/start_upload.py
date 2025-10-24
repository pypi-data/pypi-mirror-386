#!/usr/bin/env python3
"""
Start Upload Script
Simple interface to start different upload methods
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import json

def load_upload_history():
    """Load upload history"""
    history_file = Path("logs/upload_history.json")
    if history_file.exists():
        with open(history_file, 'r') as f:
            return json.load(f)
    return {"last_upload": None, "scripts_used": []}

def get_yesterday_script():
    """Get the script used yesterday"""
    history = load_upload_history()
    if history.get("scripts_used"):
        yesterday = datetime.now() - timedelta(days=1)
        for entry in reversed(history["scripts_used"]):
            entry_date = datetime.fromisoformat(entry["timestamp"])
            if entry_date.date() == yesterday.date():
                return entry["script"]
    return "No script found"

def show_menu():
    """Show the main menu"""
    print("=" * 60)
    print("KAGGLE DATASET UPLOAD TO VICTORIALOGS")
    print("=" * 60)
    print(f"Yesterday's script: {get_yesterday_script()}")
    print()
    print("Available Upload Methods:")
    print("1. Master Upload (Comprehensive - All methods)")
    print("2. Continuous Upload (Simple - Pillar logs only)")
    print("3. Kaggle Log Generator (File-based analysis)")
    print("4. Kaggle Line Logger (Line-by-line processing)")
    print("5. Show Upload History")
    print("6. Exit")
    print("=" * 60)

def run_script(script_name, args=None):
    """Run a script with optional arguments"""
    try:
        cmd = [sys.executable, script_name]
        if args:
            cmd.extend(args)
        
        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_name}: {e}")
    except KeyboardInterrupt:
        print(f"\n{script_name} stopped by user")

def show_upload_history():
    """Show upload history"""
    history = load_upload_history()
    
    print("\nUpload History:")
    print("-" * 40)
    print(f"Last upload: {history.get('last_upload', 'Never')}")
    print(f"Total uploads: {len(history.get('scripts_used', []))}")
    
    if history.get("scripts_used"):
        print("\nRecent uploads:")
        for entry in history["scripts_used"][-5:]:  # Show last 5
            print(f"  {entry['timestamp']}: {entry['script']}")

def main():
    """Main function"""
    while True:
        show_menu()
        
        try:
            choice = input("Enter your choice (1-6): ").strip()
            
            if choice == "1":
                print("\nMaster Upload Options:")
                print("a) Single upload")
                print("b) Continuous upload (1 hour interval)")
                print("c) Continuous upload (custom interval)")
                
                sub_choice = input("Enter sub-choice (a-c): ").strip().lower()
                
                if sub_choice == "a":
                    run_script("master_upload.py")
                elif sub_choice == "b":
                    run_script("master_upload.py", ["--continuous", "--interval", "3600"])
                elif sub_choice == "c":
                    interval = input("Enter interval in seconds: ").strip()
                    run_script("master_upload.py", ["--continuous", "--interval", interval])
                else:
                    print("Invalid sub-choice")
                    
            elif choice == "2":
                print("\nContinuous Upload Options:")
                print("a) Start immediately (1 hour interval)")
                print("b) Custom interval")
                
                sub_choice = input("Enter sub-choice (a-b): ").strip().lower()
                
                if sub_choice == "a":
                    run_script("continuous_upload.py", ["--start", "--interval", "3600"])
                elif sub_choice == "b":
                    interval = input("Enter interval in seconds: ").strip()
                    run_script("continuous_upload.py", ["--start", "--interval", interval])
                else:
                    print("Invalid sub-choice")
                    
            elif choice == "3":
                print("\nKaggle Log Generator Options:")
                print("a) Single upload")
                print("b) Continuous upload")
                
                sub_choice = input("Enter sub-choice (a-b): ").strip().lower()
                
                if sub_choice == "a":
                    run_script("kaggle_log_generator.py")
                elif sub_choice == "b":
                    interval = input("Enter interval in seconds: ").strip()
                    run_script("kaggle_log_generator.py", ["--continuous", "--interval", interval])
                else:
                    print("Invalid sub-choice")
                    
            elif choice == "4":
                print("\nKaggle Line Logger Options:")
                print("a) Single upload")
                print("b) Continuous upload")
                
                sub_choice = input("Enter sub-choice (a-b): ").strip().lower()
                
                if sub_choice == "a":
                    run_script("kaggle_line_logger.py")
                elif sub_choice == "b":
                    interval = input("Enter interval in seconds: ").strip()
                    run_script("kaggle_line_logger.py", ["--continuous", "--interval", interval])
                else:
                    print("Invalid sub-choice")
                    
            elif choice == "5":
                show_upload_history()
                input("\nPress Enter to continue...")
                
            elif choice == "6":
                print("Goodbye!")
                break
                
            else:
                print("Invalid choice. Please enter 1-6.")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()



