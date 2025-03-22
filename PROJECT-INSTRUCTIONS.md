# Urban Traffic Simulator

## Project Overview

You'll build an interactive web application that:
- Loads real street networks from OpenStreetMap
- Generates synthetic traffic based on road characteristics
- Allows users to simulate road closures
- Visualizes traffic redistribution on an interactive map

## Step 1: Setting Up Your Environment

### Create a Project Directory

```bash
mkdir urban-traffic-simulator
cd urban-traffic-simulator
```

### Set Up a Python Virtual Environment

For Mac with M1/M2/M3 (Apple Silicon):
```bash
# Make sure you're using a Python version compiled for ARM64
python3 -m venv venv
source venv/bin/activate

# Install NumPy first to avoid architecture compatibility issues
pip install --upgrade pip
pip install "numpy<2.0"  # Important: Use NumPy 1.x for compatibility
```

For other systems:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install --upgrade pip
```

### Create a requirements.txt File

Create a `requirements.txt` file with these dependencies:

```
Flask==2.0.1
Werkzeug==2.0.1
networkx==2.8.8
osmnx==1.3.0
geopandas==0.12.2
Shapely==2.0.1
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Project Structure

Create the following directory structure:

```
urban-traffic-simulator/
├── app.py               # Flask application
├── requirements.txt     # Dependencies
├── README.md            # Project documentation
├── static/
│   ├── css/
│   │   └── main.css     # Optional: Custom CSS
│   ├── js/              # Optional: Custom JavaScript
│   └── images/          # Optional: Images
└── templates/
    └── index.html       # Frontend template
```

## Step 3: Creating the Flask Application

Create `app.py` to set up the basic Flask framework:

1. **Import required libraries**:
   - Flask for the web framework
   - OSMnx for downloading street networks
   - NetworkX for graph operations
   - Additional utilities (json, random)

2. **Initialize Flask app and configure settings**:
   - Create a Flask app instance
   - Configure OSMnx settings
   - Set up global variables to store network data

3. **Define the root route**:
   - Create a route for the homepage (`/`) that renders your template

4. **Setup the server to run the application**:
   - Add the standard `if __name__ == '__main__':` block to run the app
   - Configure it to run on port 5001

Here's a starting point:

```python
import os
import networkx as nx
import osmnx as ox
from flask import Flask, render_template, request, jsonify

# Set up Flask app
app = Flask(__name__)

# Global variables to store network data
G = None  # The original network
G_modified = None  # The network with road closures
edge_traffic = {}  # Traffic volumes on edges

# Default settings
DEFAULT_CENTER = (-6.2088, 106.8456)  # Jakarta, Indonesia
DEFAULT_DIST = 500  # meters

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
```

## Step 4: Core Backend Functionality

You'll need to implement these key components in the Flask application:

### 1. Load Network Route

Create a route `/load_network` that:
- Accepts POST requests with location coordinates and network size
- Uses OSMnx to download a street network for the specified location
- Stores the original lat/lng coordinates before projection (critical for map alignment!)
- Projects the graph for accurate geometry calculations
- Generates synthetic traffic for the network
- Converts the network to GeoJSON format for display on the map
- Returns a JSON response with the network data

Key considerations:
- Make sure to store the original lat/lng coordinates before projection
- Handle exceptions gracefully
- Return appropriate success/error responses

### 2. Traffic Generation Function

Create a `generate_traffic()` function that:
- Takes a graph as input
- Calculates betweenness centrality (with a limit on sample nodes for performance)
- Assigns traffic values to each edge based on:
  - Road classification (highways get more traffic)
  - Road length (shorter segments might indicate denser areas)
  - Centrality (roads that connect many parts of the network)
  - Random variation to simulate real-world conditions
- Returns a dictionary mapping edge tuples to traffic values

Sample code snippet for calculating road factors:
```python
# Sample of how you might determine traffic based on road type
road_factor = 1.0
if 'highway' in data:
    highway_type = data['highway']
    if highway_type in ['motorway', 'trunk', 'primary']:
        road_factor = 3.0  # Primary roads get more traffic
    elif highway_type in ['secondary', 'tertiary']:
        road_factor = 2.0  # Secondary roads get medium traffic
```

### 3. GeoJSON Conversion Function

Create a `create_network_geojson()` function that:
- Takes a graph and traffic data as input
- Creates a GeoJSON FeatureCollection containing:
  - Roads as LineString features
  - (Optionally) Intersections as Point features
- For each road segment, include properties like:
  - Traffic volume
  - Road name
  - Road type
  - Visual properties (width, color)
- Ensure coordinates are in the correct format for GeoJSON (longitude, latitude)

Remember: The most critical part of this function is ensuring coordinates are correctly handled. OSMnx projects the graph for calculations, but Leaflet needs original lat/lng coordinates.

### 4. Road Closure and Traffic Redistribution

For the road closure functionality, implement:

1. **A route for handling road closures**:
   - Accept POST requests with the edge to close
   - Create a modified copy of the original graph
   - Remove the selected edge
   - Redistribute traffic
   - Return GeoJSON of the modified network

2. **A traffic redistribution function**:
   - Find alternate routes between the endpoints of the closed road
   - Distribute the traffic from the closed road to the alternate routes
   - Handle cases where no alternate route exists

3. **A reset function**:
   - Restore the original network state
   - Reset traffic to initial values

## Step 5: Frontend Implementation

Create an HTML template (`templates/index.html`) with these components:

### 1. Basic HTML Structure

- Set up the document structure
- Include Leaflet.js library and CSS
- Create a layout with a header, sidebar and map container

### 2. CSS Styling

- Style the layout (flex container for sidebar and map)
- Style form controls and buttons
- Add responsive design elements

### 3. Map Setup

Initialize a Leaflet map with basic settings:

```javascript
// Initialize map centered on default location
let map = L.map('map').setView([-6.2088, 106.8456], 15);

// Add OpenStreetMap tiles
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19
}).addTo(map);
```

### 4. User Interface Controls

Create controls for:
- Location selection (preset cities or custom coordinates)
- Network size adjustment (slider for distance)
- Action buttons (load network, reset network)

### 5. JavaScript Functions

Implement these core JavaScript functions:

1. **loadNetwork()**:
   - Gather user inputs (location, size)
   - Send a fetch request to your backend
   - Process the response and display the network

2. **displayNetwork()**:
   - Take GeoJSON data and display it on the map
   - Style roads based on traffic (color, width)
   - Add click handlers for road selection
   - Add tooltips with road information

3. **closeRoad()**:
   - Send selected road data to your backend
   - Update the display with the modified network

4. **resetNetwork()**:
   - Request the original network from your backend
   - Restore the display to its initial state

For styling, consider a color scheme for traffic levels:
```javascript
// Example traffic color coding
function getTrafficColor(traffic) {
    if (traffic < 200) return '#4daf4a';      // Green for low traffic
    else if (traffic < 500) return '#ff7f00';  // Orange for medium traffic
    else return '#e41a1c';                     // Red for high traffic
}
```

## Step 6: Running and Testing

1. **Start your application**:
   ```bash
   python app.py
   ```

2. **Open in browser**:
   ```
   http://localhost:5001
   ```

3. **Test the key workflows**:
   - Load networks for different locations
   - Try different network sizes
   - Close roads and observe traffic redistribution
   - Reset the network to original state

## Common Issues and Solutions

### 1. NumPy Errors on Apple Silicon

If you encounter errors related to NumPy or GDAL:

```bash
# Remove the existing environment
rm -rf venv

# Create a new environment with ARM64 Python
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install "numpy<2.0"  # Install NumPy 1.x version first
pip install -r requirements.txt
```

### 2. Map Alignment Issues

If the network doesn't align with the map:
- Make sure you're storing the original longitude/latitude in the nodes before projection
- Use smaller network sizes (200-500m is optimal)
- Double-check the coordinate order in GeoJSON (it should be [longitude, latitude])

### 3. Performance Issues

If the application is slow:
- Reduce the network size (use the distance slider)
- Limit the number of nodes used for betweenness centrality calculation
- Consider adding a loading indicator during network operations

## Next Steps and Enhancements

Once you have the basic application working, consider these enhancements:

1. **Visual Improvements**:
   - Add directional arrows to show traffic flow
   - Improve the highlighting of closed roads
   - Add a legend explaining the traffic color coding

2. **Usability Features**:
   - Add a search bar for finding specific locations
   - Implement the ability to save and compare different scenarios
   - Add a status indicator for long operations

3. **Simulation Enhancements**:
   - Implement time-of-day effects on traffic
   - Allow multiple simultaneous road closures
   - Consider more sophisticated traffic redistribution algorithms

4. **Analytics**:
   - Add statistics about the network (total traffic, average speeds)
   - Provide before/after comparison metrics for road closures
   - Implement a "congestion score" for the network

## Resources

- [OSMnx Documentation](https://osmnx.readthedocs.io/)
- [NetworkX Documentation](https://networkx.org/documentation/stable/)
- [Leaflet.js Documentation](https://leafletjs.com/reference.html)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [OpenStreetMap Wiki](https://wiki.openstreetmap.org/)

Good luck with your project! Feel free to customize and extend it based on your interests and skills.