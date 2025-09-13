#!/usr/bin/env python3
"""
ESP32 LED Tester Simulator Refresh Tool
Quickly sync changes and restart the simulator
"""

import subprocess
import sys
import time
import os

def run_command(cmd, description):
    """Run a command and show the result"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
        else:
            print(f"❌ {description} failed")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description} failed: {e}")
        return False
    return True

def main():
    """Main refresh function"""
    print("ESP32 LED Tester Simulator Refresh Tool")
    print("=" * 45)
    
    # Check if ESP32 code exists
    if not os.path.exists("src/main.cpp"):
        print("❌ ESP32 code file not found: src/main.cpp")
        print("   Make sure you're in the correct directory")
        return
    
    # Sync changes from ESP32 code
    if not run_command("python3 sync_simulator.py", "Syncing changes from ESP32 code"):
        return
    
    print("\n🚀 Starting updated simulator...")
    print("   Web interface will be available at: http://localhost:8080")
    print("   Press Ctrl+C to stop the simulator")
    print()
    
    # Start the simulator
    try:
        subprocess.run(["python3", "run_simulator.py"])
    except KeyboardInterrupt:
        print("\n✅ Simulator stopped")

if __name__ == "__main__":
    main()
