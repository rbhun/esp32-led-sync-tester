#include <WiFi.h>
#include <ESPAsyncWebServer.h>
#include <ArduinoJson.h>

// LED GPIO Mappings (12 o'clock position = LED1, clockwise)
const int LED_PINS[12] = {
  13,  // LED1 - 12 o'clock
  14,  // LED2 - 1 o'clock  
  27,  // LED3 - 2 o'clock
  26,  // LED4 - 3 o'clock
  25,  // LED5 - 4 o'clock
  33,  // LED6 - 5 o'clock
  32,  // LED7 - 6 o'clock
  16,  // LED8 - RX2 (7 o'clock)
  17,  // LED9 - TX2 (8 o'clock)
  18,  // LED10 - 9 o'clock
  19,  // LED11 - 10 o'clock
  23   // LED12 - 11 o'clock
};

const int OUTPUT_PIN = 4; // D4 output
const int VSYNC_PIN = 34; // D34 - VSYNC signal input
const int FIELD_PIN = 35; // D35 - Field signal input (ODD/EVEN)

// WiFi AP Configuration
const char* ssid = "Fillscrn-Synctester";
const char* password = "Fillscrnlovesyou1";

// Web Server
AsyncWebServer server(80);

// LED Control Variables
unsigned long fastCircleInterval = 1; // ms per LED
unsigned long frameRate = 24; // fps
bool fastCircleEnabled = true;
bool frameCircleEnabled = true;
bool d4OutputEnabled = false; // Enable D4 output for frame signal
bool vsyncLockEnabled = false; // Lock LED circles to VSYNC
bool vsyncDetectionEnabled = true; // Enable VSYNC detection

// VSYNC and Field Detection Variables
volatile bool vsyncActive = false;
volatile unsigned long lastVsyncTime = 0;
volatile unsigned long vsyncInterval = 0;
volatile float measuredFrameRate = 0.0;
volatile bool fieldOdd = false;
volatile unsigned long lastFieldChangeTime = 0;
volatile unsigned long oddFieldDuration = 0;
volatile unsigned long evenFieldDuration = 0;
volatile bool vsyncDetected = false;
volatile bool vsyncLockTrigger = false; // Flag to trigger circle reset

// Timing Variables
unsigned long lastFastCircleUpdate = 0;
unsigned long lastFrameCircleUpdate = 0;
int currentFastLED = 0;
bool frameCirclePhase = false; // false = LED1&6, true = LED4&10

// Frame timing
unsigned long frameInterval; // Calculated from frameRate

void setup() {
  Serial.begin(115200);
  delay(1000); // Give serial time to initialize
  
  Serial.println("=== ESP32 LED Tester Starting ===");
  Serial.println("Initializing LED pins...");
  
  // Initialize LED pins
  for (int i = 0; i < 12; i++) {
    pinMode(LED_PINS[i], OUTPUT);
    digitalWrite(LED_PINS[i], LOW);
    Serial.print("LED");
    Serial.print(i+1);
    Serial.print(" (GPIO");
    Serial.print(LED_PINS[i]);
    Serial.println(") initialized");
  }
  
  // Initialize output pin
  Serial.println("Initializing output pin...");
  pinMode(OUTPUT_PIN, OUTPUT);
  digitalWrite(OUTPUT_PIN, LOW);
  Serial.println("D4 output initialized");
  
  // Initialize input pins for VSYNC and Field detection
  Serial.println("Initializing input pins...");
  pinMode(VSYNC_PIN, INPUT_PULLUP);
  pinMode(FIELD_PIN, INPUT_PULLUP);
  Serial.println("VSYNC and Field input pins initialized");
  
  // Attach interrupts for VSYNC and Field signals
  Serial.println("Attaching interrupts...");
  attachInterrupt(digitalPinToInterrupt(VSYNC_PIN), vsyncISR, CHANGE);
  attachInterrupt(digitalPinToInterrupt(FIELD_PIN), fieldISR, CHANGE);
  Serial.println("Interrupts attached");
  
  // Calculate frame interval
  Serial.println("Calculating frame interval...");
  updateFrameInterval();
  Serial.print("Frame interval: ");
  Serial.print(frameInterval);
  Serial.println(" ms");
  
  // Start WiFi AP
  Serial.println("Starting WiFi Access Point...");
  Serial.print("SSID: ");
  Serial.println(ssid);
  Serial.print("Password: ");
  Serial.println(password);
  
  bool wifiStarted = WiFi.softAP(ssid, password);
  if (wifiStarted) {
    Serial.println("WiFi AP Started Successfully!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.softAPIP());
  } else {
    Serial.println("ERROR: Failed to start WiFi AP!");
  }
  
  // Setup web server routes
  Serial.println("Setting up web server...");
  setupWebServer();
  Serial.println("Web server configured");
  
  Serial.println("=== LED Tester Ready! ===");
  Serial.println("Connect to WiFi: Fillscrn-Synctester");
  Serial.println("Password: Fillscrnlovesyou1");
  Serial.print("Web interface: http://");
  Serial.println(WiFi.softAPIP());
  
  // LED test sequence (clockwise)
  Serial.println("Running LED test sequence (clockwise)...");
  for (int i = 0; i < 12; i++) {
    digitalWrite(LED_PINS[i], HIGH);
    Serial.print("LED");
    Serial.print(i+1);
    Serial.println(" ON");
    delay(200);
    digitalWrite(LED_PINS[i], LOW);
  }
  Serial.println("LED test complete");
}

void loop() {
  unsigned long currentTime = millis();
  
  // Handle VSYNC lock trigger
  if (vsyncLockTrigger) {
    vsyncLockTrigger = false; // Clear the flag
    
    // Reset both circles to start position
    if (fastCircleEnabled) {
      currentFastLED = 0; // Start with LED1 (12 o'clock)
      lastFastCircleUpdate = currentTime; // Reset timing
    }
    
    if (frameCircleEnabled) {
      frameCirclePhase = false; // Start with LED1&7 phase
      lastFrameCircleUpdate = currentTime; // Reset timing
    }
  }
  
  // Handle fast circle animation
  if (fastCircleEnabled && (currentTime - lastFastCircleUpdate >= fastCircleInterval)) {
    handleFastCircle();
    lastFastCircleUpdate = currentTime;
  }
  
  // Handle frame circle animation
  if (frameCircleEnabled && (currentTime - lastFrameCircleUpdate >= frameInterval)) {
    handleFrameCircle();
    lastFrameCircleUpdate = currentTime;
  }
}

void handleFastCircle() {
  // Turn off all LEDs first
  for (int i = 0; i < 12; i++) {
    digitalWrite(LED_PINS[i], LOW);
  }
  
  // Turn on current LED
  digitalWrite(LED_PINS[currentFastLED], HIGH);
  
  // Move to next LED (clockwise = decrement for counter-clockwise array)
  currentFastLED = (currentFastLED - 1 + 12) % 12;
}

void handleFrameCircle() {
  // Turn off frame circle LEDs
  digitalWrite(LED_PINS[0], LOW);  // LED1
  digitalWrite(LED_PINS[6], LOW);  // LED7
  digitalWrite(LED_PINS[3], LOW);  // LED4
  digitalWrite(LED_PINS[9], LOW);  // LED10
  
  if (frameCirclePhase) {
    // Phase 2: LED4 and LED10
    digitalWrite(LED_PINS[3], HIGH);  // LED4
    digitalWrite(LED_PINS[9], HIGH);  // LED10
    // D4 output: LOW during LED4&10 phase
    if (d4OutputEnabled) {
      digitalWrite(OUTPUT_PIN, LOW);
    }
  } else {
    // Phase 1: LED1 and LED7
    digitalWrite(LED_PINS[0], HIGH);  // LED1
    digitalWrite(LED_PINS[6], HIGH);  // LED7
    // D4 output: HIGH during LED1&7 phase
    if (d4OutputEnabled) {
      digitalWrite(OUTPUT_PIN, HIGH);
    }
  }
  
  frameCirclePhase = !frameCirclePhase;
}

void updateFrameInterval() {
  frameInterval = 1000 / (frameRate * 2); // Half frame duration
}

// Interrupt Service Routines
void IRAM_ATTR vsyncISR() {
  if (!vsyncDetectionEnabled) return; // Skip if VSYNC detection disabled
  
  unsigned long currentTime = micros();
  if (digitalRead(VSYNC_PIN) == LOW) {
    // VSYNC falling edge detected
    if (lastVsyncTime > 0) {
      vsyncInterval = currentTime - lastVsyncTime;
      measuredFrameRate = 1000000.0 / vsyncInterval; // Convert microseconds to fps
    }
    lastVsyncTime = currentTime;
    vsyncActive = true;
    vsyncDetected = true;
    
    // Trigger circle reset if VSYNC lock is enabled
    if (vsyncLockEnabled) {
      vsyncLockTrigger = true;
    }
  } else {
    vsyncActive = false;
  }
}

void IRAM_ATTR fieldISR() {
  unsigned long currentTime = micros();
  bool currentFieldState = digitalRead(FIELD_PIN) == HIGH;
  
  if (lastFieldChangeTime > 0) {
    unsigned long fieldDuration = currentTime - lastFieldChangeTime;
    
    if (fieldOdd) {
      oddFieldDuration = fieldDuration;
    } else {
      evenFieldDuration = fieldDuration;
    }
  }
  
  fieldOdd = currentFieldState;
  lastFieldChangeTime = currentTime;
}

void setupWebServer() {
  // Serve main page
  server.on("/", HTTP_GET, [](AsyncWebServerRequest *request){
    String html = getMainPageHTML();
    request->send(200, "text/html", html);
  });
  
  // API endpoints
  server.on("/api/status", HTTP_GET, [](AsyncWebServerRequest *request){
    DynamicJsonDocument doc(2048);
    doc["fastCircleEnabled"] = fastCircleEnabled;
    doc["frameCircleEnabled"] = frameCircleEnabled;
    doc["d4OutputEnabled"] = d4OutputEnabled;
    doc["vsyncLockEnabled"] = vsyncLockEnabled;
    doc["fastCircleInterval"] = fastCircleInterval;
    doc["frameRate"] = frameRate;
    doc["currentFastLED"] = currentFastLED;
    doc["frameCirclePhase"] = frameCirclePhase;
    
    // VSYNC and Field information
    doc["vsyncDetectionEnabled"] = vsyncDetectionEnabled;
    doc["vsyncActive"] = vsyncActive;
    doc["vsyncDetected"] = vsyncDetected;
    doc["measuredFrameRate"] = measuredFrameRate;
    doc["fieldOdd"] = fieldOdd;
    doc["oddFieldDuration"] = oddFieldDuration;
    doc["evenFieldDuration"] = evenFieldDuration;
    
    String response;
    serializeJson(doc, response);
    request->send(200, "application/json", response);
  });
  
  server.on("/api/fastCircle", HTTP_POST, [](AsyncWebServerRequest *request){
    if (request->hasParam("enabled", true)) {
      fastCircleEnabled = request->getParam("enabled", true)->value() == "true";
    }
    if (request->hasParam("interval", true)) {
      fastCircleInterval = request->getParam("interval", true)->value().toInt();
      if (fastCircleInterval < 1) fastCircleInterval = 1;
    }
    request->send(200, "application/json", "{\"status\":\"ok\"}");
  });
  
  server.on("/api/frameCircle", HTTP_POST, [](AsyncWebServerRequest *request){
    if (request->hasParam("enabled", true)) {
      frameCircleEnabled = request->getParam("enabled", true)->value() == "true";
    }
    if (request->hasParam("frameRate", true)) {
      frameRate = request->getParam("frameRate", true)->value().toInt();
      if (frameRate < 1) frameRate = 1;
      if (frameRate > 120) frameRate = 120;
      updateFrameInterval();
    }
    if (request->hasParam("d4Output", true)) {
      d4OutputEnabled = request->getParam("d4Output", true)->value() == "true";
    }
    if (request->hasParam("vsyncLock", true)) {
      vsyncLockEnabled = request->getParam("vsyncLock", true)->value() == "true";
    }
    request->send(200, "application/json", "{\"status\":\"ok\"}");
  });
  
  server.on("/api/vsync", HTTP_POST, [](AsyncWebServerRequest *request){
    if (request->hasParam("enabled", true)) {
      vsyncDetectionEnabled = request->getParam("enabled", true)->value() == "true";
    }
    request->send(200, "application/json", "{\"status\":\"ok\"}");
  });
  
  server.begin();
}

String getMainPageHTML() {
  return R"rawliteral(
<!DOCTYPE html>
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
        <h1>LED Tester Control Panel</h1>
        
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
                <label>Enable VSYNC Detection:</label>
                <input type="checkbox" id="vsyncDetectionEnabled" checked>
            </div>
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
            <button onclick="updateVsyncSettings()">Update VSYNC Settings</button>
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
        
        function updateVsyncSettings() {
            const enabled = document.getElementById('vsyncDetectionEnabled').checked;
            
            fetch('/api/vsync', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `enabled=${enabled}`
            })
            .then(response => response.json())
            .then(data => {
                showStatus('VSYNC settings updated successfully', 'success');
            })
            .catch(error => {
                showStatus('Error updating VSYNC settings: ' + error, 'error');
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
                document.getElementById('vsyncDetectionEnabled').checked = data.vsyncDetectionEnabled;
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
                
                // Check for frame rate mismatch (only if VSYNC detection is enabled)
                const frameRateError = document.getElementById('frameRateError');
                if (data.vsyncDetectionEnabled && data.vsyncDetected && data.measuredFrameRate > 0) {
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
</html>
)rawliteral";
}
