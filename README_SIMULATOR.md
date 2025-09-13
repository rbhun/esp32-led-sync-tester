# ESP32 LED Tester Simulator

This simulator allows you to test your ESP32 LED tester code without having the physical hardware connected. It provides a complete simulation of the LED control logic, web interface, and VSYNC synchronization features.

## Features

- **Complete LED Control Simulation**: Simulates all 12 LEDs in circular pattern
- **Web Interface**: Identical web interface to the ESP32 version
- **Visual LED Display**: Real-time LED state visualization (multiple options)
- **VSYNC Simulation**: Simulates video sync signals at 24fps
- **Frame Synchronization**: Tests frame circle and VSYNC lock features
- **API Compatibility**: Same REST API endpoints as the ESP32 code

## Simulator Versions

### 1. Web-Only Simulator (`simulator_web.py`)
- **Best for**: Most users, especially on systems without GUI support
- **Features**: Enhanced web interface with real-time LED visualization
- **Requirements**: Python 3.6+ (no additional dependencies)
- **LED Display**: Integrated into web interface with smooth animations

### 2. Full Simulator (`simulator.py`)
- **Best for**: Users who want a separate LED display window
- **Features**: Web interface + separate tkinter LED visualization window
- **Requirements**: Python 3.6+ with tkinter support
- **LED Display**: Dedicated window with LED circle and status information

### 3. Auto Launcher (`run_simulator.py`)
- **Best for**: Easy setup and automatic version selection
- **Features**: Automatically chooses the best available version
- **Requirements**: Python 3.6+ (tries full version first, falls back to web-only)

## Requirements

- Python 3.6 or higher
- No external dependencies (uses only Python standard library)

## Quick Start

### Option 1: Automatic Launcher (Recommended)
```bash
python3 run_simulator.py
```
This will automatically choose the best available simulator version.

### Option 2: Web-Only Simulator
```bash
python3 simulator_web.py
```
This version works on all systems and provides enhanced LED visualization in the web interface.

### Option 3: Full Simulator (if tkinter is available)
```bash
python3 simulator.py
```
This version includes both web interface and a separate LED visualization window.

## Access the Simulator

1. **Web Interface**:
   - Open your browser and go to: http://localhost:8080
   - The interface is identical to the ESP32 version
   - Enhanced LED visualization shows real-time LED states

2. **LED Visualization** (Full version only):
   - A separate window will open showing the LED circle
   - LEDs will light up in red when active
   - Status information is displayed below the circle

## How It Works

### LED Control Logic
- **Fast Circle**: LEDs light up sequentially around the circle at configurable intervals
- **Frame Circle**: Alternates between LED1&7 and LED4&10 patterns at frame rate timing
- **VSYNC Lock**: Resets both circles when VSYNC signal is detected

### VSYNC Simulation
- Simulates VSYNC signals at 24fps (configurable)
- Provides measured frame rate feedback
- Triggers circle resets when VSYNC lock is enabled

### Web Interface
- Same HTML/CSS/JavaScript as the ESP32 version
- REST API endpoints for controlling the simulator
- Real-time status updates every 2 seconds

## API Endpoints

### GET /api/status
Returns current status including:
- LED states and timing
- VSYNC detection status
- Frame rate measurements
- Control settings

### POST /api/fastCircle
Updates fast circle settings:
- `enabled`: Enable/disable fast circle
- `interval`: LED duration in milliseconds

### POST /api/frameCircle
Updates frame circle settings:
- `enabled`: Enable/disable frame circle
- `frameRate`: Frame rate in fps (1-120)
- `d4Output`: Enable/disable D4 output
- `vsyncLock`: Enable/disable VSYNC lock

## Testing Your Code

This simulator is perfect for:

1. **Algorithm Testing**: Verify your LED control logic works correctly
2. **Timing Validation**: Test different frame rates and intervals
3. **VSYNC Integration**: Test frame synchronization features
4. **Web Interface Development**: Develop and test the web UI
5. **Debugging**: Identify issues before deploying to hardware

## Differences from ESP32 Version

- **Timing**: Uses Python's `time.time()` instead of `millis()`
- **GPIO Simulation**: LED states are stored in memory instead of physical pins
- **VSYNC Source**: Simulated VSYNC signals instead of external input
- **Performance**: May not match exact timing of ESP32 hardware

## Troubleshooting

### Web Interface Not Loading
- Check that port 8080 is not in use by another application
- Try accessing http://127.0.0.1:8080 instead

### LED Visualization Not Updating
- Ensure tkinter is properly installed
- Check that the simulator is running without errors

### VSYNC Not Detected
- VSYNC simulation starts automatically
- Check the console output for any error messages

## Customization

You can modify the simulator to:
- Change VSYNC frame rate
- Add different LED patterns
- Modify timing precision
- Add additional test features

## Stopping the Simulator

- Close the LED visualization window, or
- Press Ctrl+C in the terminal

The simulator will cleanly shut down all threads and processes.
