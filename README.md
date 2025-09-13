# ESP32 LED Tester with VSYNC Detection

This project implements an LED tester for a custom PCB with 12 LEDs arranged in a circle, plus VSYNC and field signal detection capabilities.

## Features

### LED Control
- **12 LEDs** mapped to GPIO pins in clock positions (12 o'clock = LED1, clockwise)
- **Fast Circle Animation**: LEDs light up sequentially (1ms per LED, user adjustable)
- **Frame Circle Animation**: LED1&7 and LED4&10 alternate based on frame rate
- **D4 Output (OUT1)**: Frame sync signal (HIGH during LED1&7, LOW during LED4&10)
- **VSYNC Lock**: Synchronize both LED circles to VSYNC falling edge

### VSYNC & Field Detection
- **D34 (VSYNC Input)**: Detects falling edge of VSYNC signal from blackburst
- **D35 (Field Input)**: Detects ODD/EVEN field signal
- **Automatic Frame Rate Detection**: Calculates framerate from VSYNC timing
- **Field Duration Measurement**: Measures and displays odd/even field lengths
- **Frame Rate Validation**: Shows red error if measured vs set framerate don't match

### Web Interface
- WiFi AP: "Fillscrn-Syctester" (password: "Fillscrnlovesyou1")
- Real-time LED control and status monitoring
- VSYNC and field detection status
- Visual LED layout diagram
- Auto-refreshing status updates

## Hardware Connections

### LED Mappings (Clock Positions)
- LED1 (12 o'clock): GPIO 13
- LED2 (1 o'clock): GPIO 14
- LED3 (2 o'clock): GPIO 27
- LED4 (3 o'clock): GPIO 26
- LED5 (4 o'clock): GPIO 25
- LED6 (5 o'clock): GPIO 33
- LED7 (6 o'clock): GPIO 32
- LED8 (7 o'clock): GPIO 16 (RX2)
- LED9 (8 o'clock): GPIO 17 (TX2)
- LED10 (9 o'clock): GPIO 18
- LED11 (10 o'clock): GPIO 19
- LED12 (11 o'clock): GPIO 23

### Signal Inputs
- **D34**: VSYNC signal input (with pullup)
- **D35**: Field signal input (with pullup)

### Outputs
- **D4 (OUT1)**: Frame sync output (optional, user controllable)

## Usage

1. Upload the code to your ESP32-Wroom-32D
2. Connect to WiFi "Fillscrn-Syctester" with password "Fillscrnlovesyou1"
3. Open web browser to the IP address shown in Serial Monitor
4. Control LED animations and monitor VSYNC/field signals through the web interface

## Web Interface Controls

- **Fast Circle**: Enable/disable and set LED duration (1-1000ms)
- **Frame Circle**: Enable/disable, set framerate (1-120fps), enable D4 output, enable VSYNC lock
- **VSYNC Detection**: Shows VSYNC status and measured framerate
- **Field Detection**: Shows current field (ODD/EVEN) and field durations
- **Frame Rate Validation**: Red error text if measured vs set framerate mismatch
- **VSYNC Lock**: Synchronize LED circles to VSYNC falling edge

## Technical Details

- Uses interrupt-driven VSYNC and field detection for accurate timing
- Microsecond precision timing measurements
- Non-blocking LED animations
- JSON API for web communication
- Responsive web design for mobile devices
