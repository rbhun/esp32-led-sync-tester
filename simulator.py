#!/usr/bin/env python3
"""
ESP32 LED Tester Simulator
Simulates the ESP32 LED tester without hardware
"""

import time
import threading
import json
import random
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import tkinter as tk
from tkinter import ttk
import math

class LEDTesterSimulator:
    def __init__(self):
        # LED GPIO Mappings (12 o'clock position = LED1, clockwise)
        self.LED_PINS = [13, 14, 27, 26, 25, 33, 32, 16, 17, 18, 19, 23]
        
        # Control Variables
        self.fast_circle_interval = 1  # ms per LED
        self.frame_rate = 24  # fps
        self.fast_circle_enabled = True
        self.frame_circle_enabled = True
        self.d4_output_enabled = False
        self.vsync_lock_enabled = False
        
        # VSYNC and Field Detection Variables
        self.vsync_active = False
        self.last_vsync_time = 0
        self.vsync_interval = 0
        self.measured_frame_rate = 0.0
        self.field_odd = False
        self.last_field_change_time = 0
        self.odd_field_duration = 0
        self.even_field_duration = 0
        self.vsync_detected = False
        self.vsync_lock_trigger = False
        
        # Timing Variables
        self.last_fast_circle_update = 0
        self.last_frame_circle_update = 0
        self.current_fast_led = 0
        self.frame_circle_phase = False  # false = LED1&6, true = LED4&10
        
        # LED States (True = ON, False = OFF)
        self.led_states = [False] * 12
        self.d4_output_state = False
        
        # Frame timing
        self.frame_interval = 1000 / (self.frame_rate * 2)  # Half frame duration
        
        # VSYNC simulation
        self.vsync_simulation_running = False
        self.vsync_thread = None
        
        # Start the main loop in a separate thread
        self.running = True
        self.main_thread = threading.Thread(target=self.main_loop, daemon=True)
        self.main_thread.start()
        
        # Start VSYNC simulation
        self.start_vsync_simulation()
    
    def start_vsync_simulation(self):
        """Start VSYNC signal simulation"""
        if not self.vsync_simulation_running:
            self.vsync_simulation_running = True
            self.vsync_thread = threading.Thread(target=self.vsync_simulation_loop, daemon=True)
            self.vsync_thread.start()
    
    def vsync_simulation_loop(self):
        """Simulate VSYNC signals at 24fps"""
        while self.vsync_simulation_running:
            # Simulate VSYNC falling edge
            current_time = time.time() * 1000000  # Convert to microseconds
            if self.last_vsync_time > 0:
                self.vsync_interval = current_time - self.last_vsync_time
                self.measured_frame_rate = 1000000.0 / self.vsync_interval
            self.last_vsync_time = current_time
            self.vsync_active = True
            self.vsync_detected = True
            
            # Trigger circle reset if VSYNC lock is enabled
            if self.vsync_lock_enabled:
                self.vsync_lock_trigger = True
            
            # Simulate VSYNC rising edge after a short time
            time.sleep(0.001)  # 1ms
            self.vsync_active = False
            
            # Wait for next frame (24fps = ~41.67ms)
            time.sleep(1.0 / 24.0)
    
    def update_frame_interval(self):
        """Update frame interval based on frame rate"""
        self.frame_interval = 1000 / (self.frame_rate * 2)
    
    def main_loop(self):
        """Main simulation loop"""
        while self.running:
            current_time = time.time() * 1000  # Convert to milliseconds
            
            # Handle VSYNC lock trigger
            if self.vsync_lock_trigger:
                self.vsync_lock_trigger = False
                
                # Reset both circles to start position
                if self.fast_circle_enabled:
                    self.current_fast_led = 0
                    self.last_fast_circle_update = current_time
                
                if self.frame_circle_enabled:
                    self.frame_circle_phase = False
                    self.last_frame_circle_update = current_time
            
            # Handle fast circle animation
            if self.fast_circle_enabled and (current_time - self.last_fast_circle_update >= self.fast_circle_interval):
                self.handle_fast_circle()
                self.last_fast_circle_update = current_time
            
            # Handle frame circle animation
            if self.frame_circle_enabled and (current_time - self.last_frame_circle_update >= self.frame_interval):
                self.handle_frame_circle()
                self.last_frame_circle_update = current_time
            
            time.sleep(0.001)  # 1ms delay to prevent excessive CPU usage
    
    def handle_fast_circle(self):
        """Handle fast circle LED animation"""
        # Turn off all LEDs first
        for i in range(12):
            self.led_states[i] = False
        
        # Turn on current LED
        self.led_states[self.current_fast_led] = True
        
        # Move to next LED
        self.current_fast_led = (self.current_fast_led + 1) % 12
    
    def handle_frame_circle(self):
        """Handle frame circle LED animation"""
        # Turn off frame circle LEDs
        self.led_states[0] = False   # LED1
        self.led_states[6] = False   # LED7
        self.led_states[3] = False   # LED4
        self.led_states[9] = False   # LED10
        
        if self.frame_circle_phase:
            # Phase 2: LED4 and LED10
            self.led_states[3] = True   # LED4
            self.led_states[9] = True   # LED10
            # D4 output: LOW during LED4&10 phase
            if self.d4_output_enabled:
                self.d4_output_state = False
        else:
            # Phase 1: LED1 and LED7
            self.led_states[0] = True   # LED1
            self.led_states[6] = True   # LED7
            # D4 output: HIGH during LED1&7 phase
            if self.d4_output_enabled:
                self.d4_output_state = True
        
        self.frame_circle_phase = not self.frame_circle_phase
    
    def get_status(self):
        """Get current status as dictionary"""
        return {
            "fastCircleEnabled": self.fast_circle_enabled,
            "frameCircleEnabled": self.frame_circle_enabled,
            "d4OutputEnabled": self.d4_output_enabled,
            "vsyncLockEnabled": self.vsync_lock_enabled,
            "fastCircleInterval": self.fast_circle_interval,
            "frameRate": self.frame_rate,
            "currentFastLED": self.current_fast_led,
            "frameCirclePhase": self.frame_circle_phase,
            "vsyncActive": self.vsync_active,
            "vsyncDetected": self.vsync_detected,
            "measuredFrameRate": self.measured_frame_rate,
            "fieldOdd": self.field_odd,
            "oddFieldDuration": self.odd_field_duration,
            "evenFieldDuration": self.even_field_duration,
            "ledStates": self.led_states,
            "d4OutputState": self.d4_output_state
        }
    
    def update_fast_circle(self, enabled=None, interval=None):
        """Update fast circle settings"""
        if enabled is not None:
            self.fast_circle_enabled = enabled
        if interval is not None:
            self.fast_circle_interval = max(1, interval)
    
    def update_frame_circle(self, enabled=None, frame_rate=None, d4_output=None, vsync_lock=None):
        """Update frame circle settings"""
        if enabled is not None:
            self.frame_circle_enabled = enabled
        if frame_rate is not None:
            self.frame_rate = max(1, min(120, frame_rate))
            self.update_frame_interval()
        if d4_output is not None:
            self.d4_output_enabled = d4_output
        if vsync_lock is not None:
            self.vsync_lock_enabled = vsync_lock
    
    def stop(self):
        """Stop the simulator"""
        self.running = False
        self.vsync_simulation_running = False


class LEDTesterHTTPHandler(BaseHTTPRequestHandler):
    def __init__(self, simulator, *args, **kwargs):
        self.simulator = simulator
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self.serve_main_page()
        elif parsed_path.path == '/api/status':
            self.serve_status()
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/fastCircle':
            self.handle_fast_circle_update()
        elif parsed_path.path == '/api/frameCircle':
            self.handle_frame_circle_update()
        else:
            self.send_error(404)
    
    def serve_main_page(self):
        """Serve the main HTML page"""
        html = self.get_main_page_html()
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_status(self):
        """Serve status API"""
        status = self.simulator.get_status()
        response = json.dumps(status)
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(response.encode())
    
    def handle_fast_circle_update(self):
        """Handle fast circle update request"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        params = parse_qs(post_data)
        
        enabled = None
        interval = None
        
        if 'enabled' in params:
            enabled = params['enabled'][0] == 'true'
        if 'interval' in params:
            interval = int(params['interval'][0])
        
        self.simulator.update_fast_circle(enabled, interval)
        
        response = '{"status":"ok"}'
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(response.encode())
    
    def handle_frame_circle_update(self):
        """Handle frame circle update request"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        params = parse_qs(post_data)
        
        enabled = None
        frame_rate = None
        d4_output = None
        vsync_lock = None
        
        if 'enabled' in params:
            enabled = params['enabled'][0] == 'true'
        if 'frameRate' in params:
            frame_rate = int(params['frameRate'][0])
        if 'd4Output' in params:
            d4_output = params['d4Output'][0] == 'true'
        if 'vsyncLock' in params:
            vsync_lock = params['vsyncLock'][0] == 'true'
        
        self.simulator.update_frame_circle(enabled, frame_rate, d4_output, vsync_lock)
        
        response = '{"status":"ok"}'
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(response.encode())
    
    def get_main_page_html(self):
        """Get the main page HTML (same as ESP32 version)"""
        return '''<!DOCTYPE html>
<html>
<head>
    <title>LED Tester Control</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f0f0f0; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .section h3 { margin-top: 0; color: #555; }
        .control-group { margin: 10px 0; }
        label { display: inline-block; width: 200px; font-weight: bold; }
        input, select { padding: 5px; margin: 5px; border: 1px solid #ccc; border-radius: 3px; }
        button { padding: 10px 20px; margin: 5px; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { background-color: #0056b3; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .status.success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .led-diagram { text-align: center; margin: 20px 0; }
        .led-circle { display: inline-block; width: 300px; height: 300px; border: 2px solid #333; border-radius: 50%; position: relative; }
        .led-position { position: absolute; width: 20px; height: 20px; background-color: #ccc; border-radius: 50%; border: 2px solid #333; }
        .led-12 { top: 10px; left: 50%; transform: translateX(-50%); }
        .led-1 { top: 30px; right: 20px; }
        .led-2 { top: 70px; right: 10px; }
        .led-3 { top: 120px; right: 10px; }
        .led-4 { top: 170px; right: 20px; }
        .led-5 { bottom: 20px; right: 30px; }
        .led-6 { bottom: 10px; left: 50%; transform: translateX(-50%); }
        .led-7 { bottom: 20px; left: 30px; }
        .led-8 { top: 170px; left: 20px; }
        .led-9 { top: 120px; left: 10px; }
        .led-10 { top: 70px; left: 10px; }
        .led-11 { top: 30px; left: 20px; }
        .error-text { color: red; font-weight: bold; }
        .status-indicator { padding: 2px 8px; border-radius: 3px; font-weight: bold; }
        .status-active { background-color: #d4edda; color: #155724; }
        .status-inactive { background-color: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <h1>LED Tester Control Panel (SIMULATOR)</h1>
        
        <div class="led-diagram">
            <h3>LED Layout (Clock Positions)</h3>
            <div class="led-circle">
                <div class="led-position led-12">1</div>
                <div class="led-position led-1">2</div>
                <div class="led-position led-2">3</div>
                <div class="led-position led-3">4</div>
                <div class="led-position led-4">5</div>
                <div class="led-position led-5">6</div>
                <div class="led-position led-6">7</div>
                <div class="led-position led-7">8</div>
                <div class="led-position led-8">9</div>
                <div class="led-position led-9">10</div>
                <div class="led-position led-10">11</div>
                <div class="led-position led-11">12</div>
            </div>
        </div>
        
        <div class="section">
            <h3>Fast Circle Control</h3>
            <div class="control-group">
                <label>Enable Fast Circle:</label>
                <input type="checkbox" id="fastCircleEnabled" checked>
            </div>
            <div class="control-group">
                <label>LED Duration (ms):</label>
                <input type="number" id="fastCircleInterval" value="1" min="1" max="1000">
            </div>
            <button onclick="updateFastCircle()">Update Fast Circle</button>
        </div>
        
        <div class="section">
            <h3>Frame Circle Control</h3>
            <div class="control-group">
                <label>Enable Frame Circle:</label>
                <input type="checkbox" id="frameCircleEnabled" checked>
            </div>
            <div class="control-group">
                <label>Frame Rate (fps):</label>
                <input type="number" id="frameRate" value="24" min="1" max="120">
                <span id="frameRateError" class="error-text"></span>
            </div>
            <div class="control-group">
                <label>Enable D4 Output (OUT1):</label>
                <input type="checkbox" id="d4OutputEnabled">
            </div>
            <div class="control-group">
                <label>Lock to VSYNC:</label>
                <input type="checkbox" id="vsyncLockEnabled">
            </div>
            <button onclick="updateFrameCircle()">Update Frame Circle</button>
        </div>
        
        <div class="section">
            <h3>VSYNC & Field Detection</h3>
            <div class="control-group">
                <label>VSYNC Status:</label>
                <span id="vsyncStatus">Not Detected</span>
            </div>
            <div class="control-group">
                <label>Measured Frame Rate:</label>
                <span id="measuredFrameRate">0.0 fps</span>
            </div>
            <div class="control-group">
                <label>Field Status:</label>
                <span id="fieldStatus">Unknown</span>
            </div>
            <div class="control-group">
                <label>Odd Field Duration:</label>
                <span id="oddFieldDuration">0 μs</span>
            </div>
            <div class="control-group">
                <label>Even Field Duration:</label>
                <span id="evenFieldDuration">0 μs</span>
            </div>
        </div>
        
        <div class="section">
            <h3>Status</h3>
            <div id="status"></div>
            <button onclick="updateStatus()">Refresh Status</button>
        </div>
    </div>
    
    <script>
        function updateFastCircle() {
            const enabled = document.getElementById('fastCircleEnabled').checked;
            const interval = document.getElementById('fastCircleInterval').value;
            
            fetch('/api/fastCircle', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `enabled=${enabled}&interval=${interval}`
            })
            .then(response => response.json())
            .then(data => {
                showStatus('Fast Circle updated successfully', 'success');
            })
            .catch(error => {
                showStatus('Error updating Fast Circle: ' + error, 'error');
            });
        }
        
        function updateFrameCircle() {
            const enabled = document.getElementById('frameCircleEnabled').checked;
            const frameRate = document.getElementById('frameRate').value;
            const d4Output = document.getElementById('d4OutputEnabled').checked;
            const vsyncLock = document.getElementById('vsyncLockEnabled').checked;
            
            fetch('/api/frameCircle', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `enabled=${enabled}&frameRate=${frameRate}&d4Output=${d4Output}&vsyncLock=${vsyncLock}`
            })
            .then(response => response.json())
            .then(data => {
                showStatus('Frame Circle updated successfully', 'success');
            })
            .catch(error => {
                showStatus('Error updating Frame Circle: ' + error, 'error');
            });
        }
        
        function updateStatus() {
            fetch('/api/status')
            .then(response => response.json())
            .then(data => {
                document.getElementById('fastCircleEnabled').checked = data.fastCircleEnabled;
                document.getElementById('frameCircleEnabled').checked = data.frameCircleEnabled;
                document.getElementById('d4OutputEnabled').checked = data.d4OutputEnabled;
                document.getElementById('vsyncLockEnabled').checked = data.vsyncLockEnabled;
                document.getElementById('fastCircleInterval').value = data.fastCircleInterval;
                document.getElementById('frameRate').value = data.frameRate;
                
                // Update VSYNC status
                const vsyncStatus = data.vsyncDetected ? 
                    (data.vsyncActive ? 'Active' : 'Detected') : 'Not Detected';
                document.getElementById('vsyncStatus').textContent = vsyncStatus;
                document.getElementById('vsyncStatus').className = 
                    data.vsyncDetected ? 'status-indicator status-active' : 'status-indicator status-inactive';
                
                // Update measured frame rate
                document.getElementById('measuredFrameRate').textContent = 
                    data.measuredFrameRate.toFixed(2) + ' fps';
                
                // Check for frame rate mismatch
                const frameRateError = document.getElementById('frameRateError');
                if (data.vsyncDetected && data.measuredFrameRate > 0) {
                    const difference = Math.abs(data.measuredFrameRate - data.frameRate);
                    if (difference > 0.5) { // Allow 0.5 fps tolerance
                        frameRateError.textContent = `MISMATCH! (Measured: ${data.measuredFrameRate.toFixed(2)} fps)`;
                    } else {
                        frameRateError.textContent = '';
                    }
                } else {
                    frameRateError.textContent = '';
                }
                
                // Update field status
                const fieldStatus = data.fieldOdd ? 'ODD' : 'EVEN';
                document.getElementById('fieldStatus').textContent = fieldStatus;
                document.getElementById('fieldStatus').className = 
                    data.fieldOdd ? 'status-indicator status-active' : 'status-indicator status-inactive';
                
                // Update field durations
                document.getElementById('oddFieldDuration').textContent = 
                    (data.oddFieldDuration / 1000).toFixed(2) + ' ms';
                document.getElementById('evenFieldDuration').textContent = 
                    (data.evenFieldDuration / 1000).toFixed(2) + ' ms';
                
                let statusHtml = `
                    <p><strong>Fast Circle:</strong> ${data.fastCircleEnabled ? 'Enabled' : 'Disabled'} (${data.fastCircleInterval}ms per LED)</p>
                    <p><strong>Frame Circle:</strong> ${data.frameCircleEnabled ? 'Enabled' : 'Disabled'} (${data.frameRate}fps)</p>
                    <p><strong>D4 Output (OUT1):</strong> ${data.d4OutputEnabled ? 'Enabled' : 'Disabled'}</p>
                    <p><strong>VSYNC Lock:</strong> ${data.vsyncLockEnabled ? 'Enabled' : 'Disabled'}</p>
                    <p><strong>Current Fast LED:</strong> ${data.currentFastLED + 1}</p>
                    <p><strong>Frame Phase:</strong> ${data.frameCirclePhase ? 'LED4&10' : 'LED1&7'}</p>
                `;
                document.getElementById('status').innerHTML = statusHtml;
            })
            .catch(error => {
                showStatus('Error fetching status: ' + error, 'error');
            });
        }
        
        function showStatus(message, type) {
            const statusDiv = document.getElementById('status');
            statusDiv.innerHTML = `<div class="status ${type}">${message}</div>`;
        }
        
        // Update status on page load
        updateStatus();
        
        // Auto-refresh status every 2 seconds
        setInterval(updateStatus, 2000);
    </script>
</body>
</html>'''


class LEDVisualizer:
    def __init__(self, simulator):
        self.simulator = simulator
        self.root = tk.Tk()
        self.root.title("LED Tester Visualizer")
        self.root.geometry("600x600")
        
        # Create canvas for LED circle
        self.canvas = tk.Canvas(self.root, width=400, height=400, bg='white')
        self.canvas.pack(pady=20)
        
        # LED positions (12 o'clock = 0, clockwise)
        self.led_positions = []
        center_x, center_y = 200, 200
        radius = 150
        
        for i in range(12):
            angle = (i * 30 - 90) * math.pi / 180  # -90 to start at 12 o'clock
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            self.led_positions.append((x, y))
        
        # Create LED circles
        self.led_circles = []
        for i, (x, y) in enumerate(self.led_positions):
            circle = self.canvas.create_oval(x-15, y-15, x+15, y+15, 
                                          fill='gray', outline='black', width=2)
            self.led_circles.append(circle)
            
            # Add LED number labels
            self.canvas.create_text(x, y, text=str(i+1), font=('Arial', 10, 'bold'))
        
        # Status labels
        self.status_frame = tk.Frame(self.root)
        self.status_frame.pack(pady=10)
        
        self.fast_led_label = tk.Label(self.status_frame, text="Fast LED: 1", font=('Arial', 12))
        self.fast_led_label.pack()
        
        self.frame_phase_label = tk.Label(self.status_frame, text="Frame Phase: LED1&7", font=('Arial', 12))
        self.frame_phase_label.pack()
        
        self.d4_output_label = tk.Label(self.status_frame, text="D4 Output: OFF", font=('Arial', 12))
        self.d4_output_label.pack()
        
        # Start update loop
        self.update_display()
    
    def update_display(self):
        """Update the LED display"""
        status = self.simulator.get_status()
        
        # Update LED states
        for i, led_state in enumerate(status['ledStates']):
            color = 'red' if led_state else 'gray'
            self.canvas.itemconfig(self.led_circles[i], fill=color)
        
        # Update status labels
        self.fast_led_label.config(text=f"Fast LED: {status['currentFastLED'] + 1}")
        
        phase_text = "LED4&10" if status['frameCirclePhase'] else "LED1&7"
        self.frame_phase_label.config(text=f"Frame Phase: {phase_text}")
        
        d4_text = "ON" if status['d4OutputState'] else "OFF"
        self.d4_output_label.config(text=f"D4 Output: {d4_text}")
        
        # Schedule next update
        self.root.after(50, self.update_display)  # Update every 50ms
    
    def run(self):
        """Run the visualizer"""
        self.root.mainloop()


def create_handler(simulator):
    """Create HTTP handler with simulator reference"""
    def handler(*args, **kwargs):
        return LEDTesterHTTPHandler(simulator, *args, **kwargs)
    return handler


def main():
    """Main function"""
    print("Starting ESP32 LED Tester Simulator...")
    
    # Create simulator
    simulator = LEDTesterSimulator()
    
    # Start web server
    port = 8080
    handler = create_handler(simulator)
    httpd = HTTPServer(('localhost', port), handler)
    
    print(f"Web server starting on http://localhost:{port}")
    print("Press Ctrl+C to stop")
    
    # Start web server in a separate thread
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    
    # Start visualizer
    try:
        visualizer = LEDVisualizer(simulator)
        visualizer.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
        simulator.stop()
        httpd.shutdown()


if __name__ == "__main__":
    main()


