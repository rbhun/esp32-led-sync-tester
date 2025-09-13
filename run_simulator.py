#!/usr/bin/env python3
"""
ESP32 LED Tester Simulator Launcher
Automatically chooses the best available simulator version
"""

import sys
import subprocess

def check_tkinter():
    """Check if tkinter is available"""
    try:
        import tkinter
        return True
    except ImportError:
        return False

def main():
    """Main launcher function"""
    print("ESP32 LED Tester Simulator Launcher")
    print("=" * 40)
    
    if check_tkinter():
        print("✓ Tkinter available - starting full simulator with GUI")
        print("This will open both a web interface and a visual LED display window")
        print()
        try:
            import simulator
            simulator.main()
        except Exception as e:
            print(f"Error starting full simulator: {e}")
            print("Falling back to web-only version...")
            import simulator_web
            simulator_web.main()
    else:
        print("⚠ Tkinter not available - starting web-only simulator")
        print("This will open only the web interface (no separate LED display window)")
        print()
        import simulator_web
        simulator_web.main()

if __name__ == "__main__":
    main()


