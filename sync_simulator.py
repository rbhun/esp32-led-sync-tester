#!/usr/bin/env python3
"""
ESP32 LED Tester Simulator Sync Tool
Helps sync changes from ESP32 code to simulator
"""

import re
import os

def extract_constants_from_cpp(file_path):
    """Extract constants and variables from ESP32 C++ code"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Extract LED pins
        led_pins_match = re.search(r'const int LED_PINS\[12\] = \{(.*?)\};', content, re.DOTALL)
        led_pins = []
        if led_pins_match:
            pins_text = led_pins_match.group(1)
            # Extract only the first number from each line (the GPIO pin number)
            lines = pins_text.strip().split('\n')
            for line in lines:
                if line.strip():
                    # Extract the first number from each line
                    pin_match = re.search(r'(\d+)', line.strip())
                    if pin_match:
                        led_pins.append(int(pin_match.group(1)))
        
        # Extract other constants
        output_pin_match = re.search(r'const int OUTPUT_PIN = (\d+);', content)
        output_pin = int(output_pin_match.group(1)) if output_pin_match else 4
        
        vsync_pin_match = re.search(r'const int VSYNC_PIN = (\d+);', content)
        vsync_pin = int(vsync_pin_match.group(1)) if vsync_pin_match else 34
        
        field_pin_match = re.search(r'const int FIELD_PIN = (\d+);', content)
        field_pin = int(field_pin_match.group(1)) if field_pin_match else 35
        
        # Extract WiFi settings
        ssid_match = re.search(r'const char\* ssid = "([^"]+)";', content)
        ssid = ssid_match.group(1) if ssid_match else "Fillscrn-Synctester"
        
        password_match = re.search(r'const char\* password = "([^"]+)";', content)
        password = password_match.group(1) if password_match else "Fillscrnlovesyou1"
        
        # Extract default values
        fast_interval_match = re.search(r'unsigned long fastCircleInterval = (\d+);', content)
        fast_interval = int(fast_interval_match.group(1)) if fast_interval_match else 1
        
        frame_rate_match = re.search(r'unsigned long frameRate = (\d+);', content)
        frame_rate = int(frame_rate_match.group(1)) if frame_rate_match else 24
        
        # Extract boolean flags
        fast_circle_enabled_match = re.search(r'bool fastCircleEnabled = (true|false);', content)
        fast_circle_enabled = fast_circle_enabled_match.group(1) == 'true' if fast_circle_enabled_match else True
        
        frame_circle_enabled_match = re.search(r'bool frameCircleEnabled = (true|false);', content)
        frame_circle_enabled = frame_circle_enabled_match.group(1) == 'true' if frame_circle_enabled_match else True
        
        d4_output_enabled_match = re.search(r'bool d4OutputEnabled = (true|false);', content)
        d4_output_enabled = d4_output_enabled_match.group(1) == 'true' if d4_output_enabled_match else False
        
        vsync_lock_enabled_match = re.search(r'bool vsyncLockEnabled = (true|false);', content)
        vsync_lock_enabled = vsync_lock_enabled_match.group(1) == 'true' if vsync_lock_enabled_match else False
        
        vsync_detection_enabled_match = re.search(r'bool vsyncDetectionEnabled = (true|false);', content)
        vsync_detection_enabled = vsync_detection_enabled_match.group(1) == 'true' if vsync_detection_enabled_match else True
        
        return {
            'led_pins': led_pins,
            'output_pin': output_pin,
            'vsync_pin': vsync_pin,
            'field_pin': field_pin,
            'ssid': ssid,
            'password': password,
            'fast_interval': fast_interval,
            'frame_rate': frame_rate,
            'fast_circle_enabled': fast_circle_enabled,
            'frame_circle_enabled': frame_circle_enabled,
            'd4_output_enabled': d4_output_enabled,
            'vsync_lock_enabled': vsync_lock_enabled,
            'vsync_detection_enabled': vsync_detection_enabled
        }
    except Exception as e:
        print(f"Error reading ESP32 code: {e}")
        return None

def update_simulator_file(simulator_file, constants):
    """Update simulator file with new constants"""
    try:
        with open(simulator_file, 'r') as f:
            content = f.read()
        
        # Update LED pins
        if constants['led_pins']:
            pins_str = ', '.join(map(str, constants['led_pins']))
            content = re.sub(
                r'self\.LED_PINS = \[.*?\]',
                f'self.LED_PINS = {constants["led_pins"]}',
                content
            )
        
        # Update default values
        content = re.sub(
            r'self\.fast_circle_interval = \d+',
            f'self.fast_circle_interval = {constants["fast_interval"]}',
            content
        )
        
        content = re.sub(
            r'self\.frame_rate = \d+',
            f'self.frame_rate = {constants["frame_rate"]}',
            content
        )
        
        # Update boolean flags
        content = re.sub(
            r'self\.fast_circle_enabled = (True|False)',
            f'self.fast_circle_enabled = {constants["fast_circle_enabled"]}',
            content
        )
        
        content = re.sub(
            r'self\.frame_circle_enabled = (True|False)',
            f'self.frame_circle_enabled = {constants["frame_circle_enabled"]}',
            content
        )
        
        content = re.sub(
            r'self\.d4_output_enabled = (True|False)',
            f'self.d4_output_enabled = {constants["d4_output_enabled"]}',
            content
        )
        
        content = re.sub(
            r'self\.vsync_lock_enabled = (True|False)',
            f'self.vsync_lock_enabled = {constants["vsync_lock_enabled"]}',
            content
        )
        
        with open(simulator_file, 'w') as f:
            f.write(content)
        
        return True
    except Exception as e:
        print(f"Error updating simulator: {e}")
        return False

def main():
    """Main sync function"""
    print("ESP32 LED Tester Simulator Sync Tool")
    print("=" * 40)
    
    esp32_file = "src/main.cpp"
    simulator_file = "simulator_web.py"
    
    if not os.path.exists(esp32_file):
        print(f"❌ ESP32 code file not found: {esp32_file}")
        return
    
    if not os.path.exists(simulator_file):
        print(f"❌ Simulator file not found: {simulator_file}")
        return
    
    print(f"📖 Reading ESP32 code from: {esp32_file}")
    constants = extract_constants_from_cpp(esp32_file)
    
    if not constants:
        print("❌ Failed to extract constants from ESP32 code")
        return
    
    print("✅ Extracted constants:")
    print(f"   LED Pins: {constants['led_pins']}")
    print(f"   Output Pin: {constants['output_pin']}")
    print(f"   VSYNC Pin: {constants['vsync_pin']}")
    print(f"   Field Pin: {constants['field_pin']}")
    print(f"   WiFi SSID: {constants['ssid']}")
    print(f"   Fast Interval: {constants['fast_interval']}ms")
    print(f"   Frame Rate: {constants['frame_rate']}fps")
    print(f"   Fast Circle Enabled: {constants['fast_circle_enabled']}")
    print(f"   Frame Circle Enabled: {constants['frame_circle_enabled']}")
    print(f"   D4 Output Enabled: {constants['d4_output_enabled']}")
    print(f"   VSYNC Lock Enabled: {constants['vsync_lock_enabled']}")
    print(f"   VSYNC Detection Enabled: {constants['vsync_detection_enabled']}")
    
    print(f"\n🔄 Updating simulator: {simulator_file}")
    if update_simulator_file(simulator_file, constants):
        print("✅ Simulator updated successfully!")
        print("\n📋 Next steps:")
        print("1. Restart the simulator: python3 run_simulator.py")
        print("2. Refresh your browser at http://localhost:8080")
    else:
        print("❌ Failed to update simulator")

if __name__ == "__main__":
    main()
