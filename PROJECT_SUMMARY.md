# BlueOS Web Interface - Technical Project Summary

## 1. Project Overview

**blueos_webinterface** is a real-time GPS tracking web application designed for maritime environments, specifically integrating with BlueOS (Blue Robotics' Raspberry Pi operating system) to visualize boat GPS telemetry. The system leverages MAVLink2REST protocol to fetch GPS data from autonomous vehicles and displays it through an interactive web interface with live map visualization and telemetry readout.

**Key Purpose:** Provide a real-time, low-latency dashboard for vessel position tracking and telemetry monitoring within the BlueOS ecosystem.

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     BlueOS Container                         │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐              ┌──────────────────┐    │
│  │  MAVLink2REST    │  (port 6040) │  Python HTTP     │    │
│  │  API Server      │◄─────────────┤  Server (main.py)│    │
│  │  (GLOBAL_       │              │  (port 8080)     │    │
│  │   POSITION_INT) │              └──────────────────┘    │
│  └──────────────────┘                      │               │
│                                             │               │
│                          ┌──────────────────┴─────────────┐ │
│                          │  Static Files                  │ │
│                          │  (index.html)                  │ │
│                          └──────────────────┬─────────────┘ │
└──────────────────────────────────────────────┼──────────────┘
                                               │
                ┌──────────────────────────────┘
                │ http://localhost:8080
                │
         ┌──────▼────────┐
         │  Web Browser  │
         │ (index.html)  │
         └───────────────┘
```

---

## 3. Technical Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | Python 3.11 | HTTP server implementation |
| **HTTP Server** | `http.server` + `socketserver` | Lightweight threaded HTTP handling |
| **Protocol** | MAVLink2REST (via HTTP) | Vehicle telemetry access |
| **Frontend** | HTML5 + JavaScript (ES6) | Real-time map interface |
| **Mapping Library** | Leaflet.js 1.9.4 | Interactive map visualization |
| **Base Maps** | CartoDB Dark Maps | Tile layer for map rendering |
| **Containerization** | Docker | Application deployment |
| **Base Image** | python:3.11-slim | Minimal Python runtime |

---

## 4. System Components

### 4.1 Backend Server (`main.py`)

**Responsibilities:**
- HTTP request routing
- MAVLink2REST API proxying
- Static file serving
- CORS headers management
- Error handling and timeouts

**Key Features:**
- **Single-threaded Event Loop:** Built on Python's `socketserver.TCPServer` with `BaseHTTPRequestHandler`
- **Request Routing:** Two primary endpoints (root/API)
- **Proxy Pattern:** Acts as HTTP proxy to avoid CORS issues
- **Timeout Handling:** 2-second timeout for MAVLink API requests
- **Graceful Degradation:** JSON error responses for connection failures

**Listening Port:** `8080`

### 4.2 Frontend (`index.html`)

**Responsibilities:**
- Real-time GPS data fetching
- Map visualization and marker positioning
- Telemetry display and formatting
- User interface styling (terminal-style theme)

**Key Features:**
- **Leaflet.js Integration:** OpenStreetMap-style map with Leaflet cartography
- **Polling Mechanism:** 1-second interval API polling (`setInterval(fetchGPS, 1000)`)
- **Coordinate Conversion:** Converts MAVLink integer coordinates to decimal degrees (division by 1e7)
- **Altitude Tracking:** Displays both absolute and relative altitude
- **Track History:** Polyline rendering of vessel path over time
- **Status Indicator:** Visual feedback for GPS lock state
- **Responsive Styling:** Full-viewport map with CSS overlay panel

**Map Features:**
- Auto-zoom on first GPS fix (zoom level 16)
- Green marker (circle) for current position
- Green polyline trail for position history
- Dark theme for maritime/nighttime operation

### 4.3 Docker Container

**Configuration:**
- Base Image: `python:3.11-slim`
- Working Directory: `/app`
- Exposed Port: `8080`
- Network Mode: Host (required for localhost MAVLink API access)
- Device Mappings:
  - `/dev/video0` - Camera/video input
  - `/dev/ttyUSB0` - Serial GPS/sensor devices

**BlueOS Extension Metadata:**
- Version: 1.0.0
- Permissions: Host networking enabled
- Allows direct access to host GPIO, USB, and network devices

---

## 5. API Specification

### 5.1 HTTP Endpoints

#### GET `/` or `/index.html`
- **Response:** HTML5 web interface
- **Content-Type:** `text/html`
- **Status:** 200 OK (if file exists) | 404 Not Found

#### GET `/api/gps`
- **Description:** Proxy endpoint to MAVLink2REST GPS data
- **Upstream URL:** `http://localhost:6040/v1/mavlink/vehicles/1/components/1/messages/GLOBAL_POSITION_INT`
- **Response (Success):** JSON telemetry object
  ```json
  {
    "message": {
      "lat": 40123456,     // Integer latitude (1e-7 decimal degrees)
      "lon": -122123456,   // Integer longitude (1e-7 decimal degrees)
      "alt": 45000,        // Absolute altitude (millimeters)
      "relative_alt": 2000 // Relative altitude (millimeters)
    }
  }
  ```
- **Response (Error):**
  ```json
  {
    "error": "Connection refused" or other error message
  }
  ```
- **Headers (Response):**
  - `Content-Type: application/json`
  - `Access-Control-Allow-Origin: *` (CORS enabled)
  - `Content-Length: <size>`
- **Status Codes:**
  - `200` - Successful MAVLink data retrieval
  - `502` - Bad Gateway (MAVLink API unreachable or timeout)
  - `404` - Invalid endpoint

#### GET `/*` (Other paths)
- **Status:** 404 Not Found

---

## 6. Data Flow

```
1. Browser (JavaScript)
   ↓ (1-second polling via fetch('/api/gps'))
   
2. Python HTTP Server (main.py)
   ├─ Parse request path
   ├─ Route to /api/gps handler
   └─ Initiate upstream HTTP request
   
3. HTTP Request to MAVLink2REST
   └─ http://localhost:6040/v1/mavlink/vehicles/1/components/1/messages/GLOBAL_POSITION_INT
   
4. MAVLink2REST Server (BlueOS)
   └─ Query autopilot/GPS component
   └─ Return current GLOBAL_POSITION_INT message
   
5. Response Chain (reverse)
   ├─ MAVLink JSON data returned to proxy
   ├─ Headers added (CORS, Content-Type)
   ├─ Response sent to browser
   
6. Frontend Processing
   ├─ Parse JSON
   ├─ Convert coordinates (lat/lon ÷ 1e7, alt ÷ 1000)
   ├─ Update Leaflet marker position
   ├─ Append to polyline trail
   ├─ Update telemetry display
   └─ Error handling: show "WAITING FOR FIX" on connection failure
```

---

## 7. Backend Implementation Details

### Request Routing
```python
def do_GET(self):
    if self.path == "/api/gps":
        self._proxy_mavlink()
    elif self.path in ("/", "/index.html"):
        self._serve_file("index.html", "text/html")
    else:
        self.send_response(404)
```

### Error Handling
- **URLError/Timeout:** Caught as generic exception
- **File Not Found:** Graceful 404 response
- **Malformed Requests:** Handled by `BaseHTTPRequestHandler`
- **Network Failures:** Returns `502` with error JSON

### Performance Considerations
- Suppressed logging (`log_message` override) to reduce I/O
- 2-second timeout prevents hanging requests
- No request queuing or rate limiting
- Single-threaded event loop (suitable for low-traffic applications)

---

## 8. Frontend Implementation Details

### Polling Architecture
```javascript
setInterval(fetchGPS, 1000); // 1 Hz update rate
fetchGPS(); // Initial call on page load
```

### Coordinate Transformation
- **MAVLink Format:** Latitude/longitude as integers (1e-7 scale)
- **Decimal Format:** Divide by 1e7 for degrees
- **Altitude Format:** Divide by 1000 for meters (stored in millimeters by MAVLink)

### State Management
- `firstFix` boolean: Auto-zoom on initial GPS lock
- Map viewport updates only on first fix (subsequent updates pan/center as needed)

### UI States
- **WAITING FOR FIX:** Red status (GPS unavailable)
- **GPS ACTIVE:** Green status (GPS locked and updating)

---

## 9. Deployment

### Build Command
```bash
sudo docker build -t local/my-gps-tracker .
```

### Run Command
```bash
sudo docker run --network host \
  --device /dev/video0 \
  --device /dev/ttyUSB0 \
  local/my-gps-tracker
```

### Access URL
```
http://192.168.2.2:8080
```

### Prerequisites
- BlueOS 1.x installed on Raspberry Pi
- MAVLink2REST service running (default port 6040)
- Network host mode required for localhost access
- USB devices connected (`/dev/ttyUSB0` for GPS, `/dev/video0` for camera)

---

## 10. File Structure

```
blueos_webinterface/
├── Dockerfile              # Container configuration and BlueOS metadata
├── main.py                 # Python HTTP server (backend)
├── index.html              # Web interface (frontend)
├── LICENSE                 # Project license
├── README.md               # User setup documentation
└── PROJECT_SUMMARY.md      # This technical summary
```

---

## 11. Security Considerations

| Concern | Status | Notes |
|---------|--------|-------|
| CORS Headers | ✅ Enabled | `Access-Control-Allow-Origin: *` (all origins permitted) |
| Input Validation | ⚠️ Minimal | No request body validation; path-based routing only |
| Network Isolation | ✅ Host Mode | Restricted to host network (not exposed externally unless port forwarded) |
| Error Messages | ✅ Safe | Generic error messages in JSON responses |
| Static File Access | ✅ Protected | File serving limited to `index.html` via path restriction |

---

## 12. Performance Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| Update Frequency | 1 Hz | Browser polls every 1000ms |
| Response Timeout | 2 seconds | MAVLink API request timeout |
| Map Tile Load | CDN via CartoDB | External basemap tiles (requires internet) |
| Memory Footprint | ~50-100 MB | Python 3.11-slim base image |
| Maximum Connections | Unlimited | Single-threaded server (no connection pooling) |

---

## 13. Known Limitations

1. **Single-threaded Server:** Can process only one request at a time
2. **No Caching:** Each API poll fetches fresh data from MAVLink
3. **No Persistence:** GPS history lost on page reload
4. **Hardcoded MAVLink URL:** Cannot configure different vehicle/component IDs
5. **External Tile Dependency:** CartoDB maps require internet connectivity
6. **No Authentication:** Public access to all endpoints
7. **No SSL/TLS:** HTTP only (suitable for LAN-only deployment)

---

## 14. Future Enhancement Opportunities

- [ ] WebSocket support for bidirectional real-time updates
- [ ] Configurable polling interval via query parameters
- [ ] GPS data persistence (SQLite/PostgreSQL)
- [ ] Multiple vehicle tracking
- [ ] Telemetry filtering and smoothing (Kalman filter)
- [ ] Historical replay functionality
- [ ] Geofencing and alert thresholds
- [ ] Multi-user session support
- [ ] REST API for programmatic access
- [ ] SSL/TLS certificate support

---

**Document Generated:** 2026-06-04  
**Project Status:** Production-Ready (Single Vehicle Tracking)  
**Target Environment:** BlueOS on Raspberry Pi 4/5
