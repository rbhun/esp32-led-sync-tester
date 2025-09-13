#!/usr/bin/env python3
"""
ESP32 LED Tester Simulator Demo
Demonstrates the simulator functionality without web interface
"""

import time
import simulator_web

def demo_led_patterns():
    """Demonstrate different LED patterns"""
    print("ESP32 LED Tester Simulator Demo")
    print("=" * 40)
    
    # Create simulator
    sim = simulator_web.LEDTesterSimulator()
    
    print("✓ Simulator started")
    print("✓ VSYNC simulation running at 24fps")
    print()
    
    # Demo 1: Fast Circle
    print("Demo 1: Fast Circle Animation")
    print("-" * 30)
    sim.update_fast_circle(enabled=True, interval=100)  # 100ms per LED
    sim.update_frame_circle(enabled=False)
    
    for i in range(15):  # Show 15 steps
        time.sleep(0.1)
        status = sim.get_status()
        active_leds = [i+1 for i, state in enumerate(status['ledStates']) if state]
        print(f"Step {i+1:2d}: LED {active_leds[0] if active_leds else 'None'} active")
    
    print()
    
    # Demo 2: Frame Circle
    print("Demo 2: Frame Circle Animation")
    print("-" * 30)
    sim.update_fast_circle(enabled=False)
    sim.update_frame_circle(enabled=True, frame_rate=12)  # 12fps for demo
    
    for i in range(8):  # Show 8 steps
        time.sleep(0.2)
        status = sim.get_status()
        active_leds = [i+1 for i, state in enumerate(status['ledStates']) if state]
        phase = "LED4&10" if status['frameCirclePhase'] else "LED1&7"
        print(f"Step {i+1:2d}: {phase} - LEDs {active_leds} active")
    
    print()
    
    # Demo 3: VSYNC Lock
    print("Demo 3: VSYNC Lock Feature")
    print("-" * 30)
    sim.update_fast_circle(enabled=True, interval=50)
    sim.update_frame_circle(enabled=True, frame_rate=24, vsync_lock=True)
    
    print("VSYNC lock enabled - circles will reset on VSYNC signals")
    for i in range(10):
        time.sleep(0.1)
        status = sim.get_status()
        active_leds = [i+1 for i, state in enumerate(status['ledStates']) if state]
        vsync_status = "Active" if status['vsyncActive'] else "Inactive"
        print(f"Step {i+1:2d}: LEDs {active_leds} | VSYNC: {vsync_status}")
    
    print()
    
    # Demo 4: D4 Output
    print("Demo 4: D4 Output Control")
    print("-" * 30)
    sim.update_frame_circle(d4_output=True)
    
    for i in range(6):
        time.sleep(0.2)
        status = sim.get_status()
        d4_state = "HIGH" if status['d4OutputState'] else "LOW"
        phase = "LED4&10" if status['frameCirclePhase'] else "LED1&7"
        print(f"Step {i+1:2d}: {phase} | D4 Output: {d4_state}")
    
    print()
    
    # Final status
    print("Final Status:")
    print("-" * 30)
    final_status = sim.get_status()
    print(f"Fast Circle: {'Enabled' if final_status['fastCircleEnabled'] else 'Disabled'}")
    print(f"Frame Circle: {'Enabled' if final_status['frameCircleEnabled'] else 'Disabled'}")
    print(f"D4 Output: {'Enabled' if final_status['d4OutputEnabled'] else 'Disabled'}")
    print(f"VSYNC Lock: {'Enabled' if final_status['vsyncLockEnabled'] else 'Disabled'}")
    print(f"Measured Frame Rate: {final_status['measuredFrameRate']:.2f} fps")
    print(f"Current Fast LED: {final_status['currentFastLED'] + 1}")
    
    # Stop simulator
    sim.stop()
    print("\n✓ Demo completed - Simulator stopped")

if __name__ == "__main__":
    demo_led_patterns()


