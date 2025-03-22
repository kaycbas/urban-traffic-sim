# Building Your Own Urban Traffic Simulator

This guide will walk you through creating a web application that visualizes traffic on real street networks and simulates the effects of road closures. Follow these step-by-step instructions to build your own version of this project.

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

Create `app.py` with the basic Flask setup:

```python
import os
import json
import random
import networkx as nx
import osmnx as ox
from flask import Flask, render_template, request, jsonify

# Set up Flask app
app = Flask(__name__)

# Configure osmnx
ox.config(use_cache=True, log_console=True)

# Global variables to store network data
G = None  # The original network
G_modified = None  # The network with a road closure
edge_traffic = {}  # Traffic volumes on edges

# Default center coordinates (choose any city you like)
DEFAULT_CENTER = (-6.2088, 106.8456)  # Jakarta, Indonesia
DEFAULT_DIST = 500  # meters - smaller area for OSM data to load quickly

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

# Start the Flask server when running the script directly
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
```

## Step 4: Core Backend Functionality

Now, you need to implement these key functions in your `app.py`:

1. **Load Network Route**: Fetches street network from OpenStreetMap
2. **Traffic Generation**: Creates synthetic traffic data
3. **Road Closure**: Simulates closing roads and traffic redistribution
4. **GeoJSON Conversion**: Formats network data for map display

Here are the key functions you should implement:

### 1. Load Network Route

```python
@app.route('/load_network', methods=['POST'])
def load_network():
    """Load a network from OpenStreetMap"""
    data = request.json
    
    # Get location from request, or use default
    lat = float(data.get('latitude', DEFAULT_CENTER[0]))
    lng = float(data.get('longitude', DEFAULT_CENTER[1]))
    dist = float(data.get('distance', DEFAULT_DIST))
    
    global G, G_modified, edge_traffic
    try:
        # Download street network from OSM for the specified location
        print(f"Downloading OSM network for location: ({lat}, {lng}), dist={dist}m")
        G = ox.graph_from_point((lat, lng), dist=dist, network_type='drive')
        
        # Store original lat/lng before projection - critical for map alignment!
        for node_id, data in G.nodes(data=True):
            G.nodes[node_id]['lon'] = data['x']  
            G.nodes[node_id]['lat'] = data['y']
            
        # Project graph to a useful CRS for accurate geometry
        G = ox.project_graph(G)
        
        # Create a copy for modifications
        G_modified = G.copy()
        
        # Generate synthetic traffic
        edge_traffic = generate_traffic(G)
        
        # Convert to GeoJSON
        network_geojson = create_network_geojson(G, edge_traffic)
        
        return jsonify({
            'success': True,
            'center': [lat, lng],
            'network': network_geojson
        })
    except Exception as e:
        print(f"Error loading network: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })
```

### 2. Traffic Generation Function

Implement a function to generate synthetic traffic:

```python
def generate_traffic(graph):
    """
    Generate realistic traffic volumes based on:
    1. Road classification (highways get more traffic)
    2. Road length (shorter segments might have more traffic)
    3. Betweenness centrality (roads that connect many parts of the city have more traffic)
    """
    # Initialize traffic dictionary
    traffic = {}
    
    # Try to compute betweenness centrality (may be expensive)
    try:
        # Limit sample nodes to keep it fast
        bc_edges = nx.edge_betweenness_centrality(graph, k=min(100, len(graph.nodes)), weight='length')
    except:
        # Fallback to a simpler model
        bc_edges = {edge: 0.5 for edge in graph.edges()}
    
    # For each edge, assign traffic based on multiple factors
    for u, v, data in graph.edges(data=True):
        # Base traffic level - random between 50-200
        base_traffic = random.randint(50, 200)
        
        # Road classification factor - highways get more traffic
        road_factor = 1.0
        if 'highway' in data:
            highway_type = data['highway']
            # Primary roads
            if highway_type in ['motorway', 'trunk', 'primary', 'motorway_link', 'trunk_link', 'primary_link']:
                road_factor = 3.0
            # Secondary roads
            elif highway_type in ['secondary', 'secondary_link', 'tertiary', 'tertiary_link']:
                road_factor = 2.0
                
        # Calculate final traffic
        edge_traffic = int(base_traffic * road_factor * random.uniform(0.8, 1.2))
        traffic[(u, v, 0)] = max(10, min(1000, edge_traffic))
    
    return traffic
```

### 3. GeoJSON Conversion Function

```python
def create_network_geojson(graph, traffic_data):
    """Convert network to GeoJSON format with traffic data"""
    features = []
    
    # Add edges as LineString features
    for u, v, data in graph.edges(data=True):
        # Create key 0 for all edges (simplified model)
        k = 0
        
        # Get traffic for this edge
        traffic = traffic_data.get((u, v, k), 0)
        
        # Calculate line width based on traffic
        width = 1.5 + (traffic / 150)
        
        # Get coordinates for the edge
        coords = [(graph.nodes[u].get('lon', graph.nodes[u]['x']), 
                  graph.nodes[u].get('lat', graph.nodes[u]['y'])), 
                 (graph.nodes[v].get('lon', graph.nodes[v]['x']), 
                  graph.nodes[v].get('lat', graph.nodes[v]['y']))]
        
        # Create GeoJSON Feature
        feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'LineString',
                'coordinates': [[c[0], c[1]] for c in coords]  # [lon, lat] format
            },
            'properties': {
                'u': u,
                'v': v,
                'key': k,
                'name': data.get('name', 'Unnamed Road'),
                'highway': data.get('highway', 'road'),
                'traffic': traffic,
                'width': width
            }
        }
        features.append(feature)
    
    return {
        'type': 'FeatureCollection',
        'features': features
    }
```

## Step 5: Frontend Implementation

Create `templates/index.html` for the user interface:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Urban Traffic Simulator</title>
    
    <!-- Leaflet CSS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.3/dist/leaflet.css" />
    
    <style>
        html, body {
            height: 100%;
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
        }
        
        .container {
            display: flex;
            flex-direction: column;
            height: 100%;
        }
        
        .header {
            background-color: #2c3e50;
            color: white;
            padding: 10px 20px;
        }
        
        .content {
            display: flex;
            flex: 1;
            overflow: hidden;
        }
        
        .sidebar {
            width: 300px;
            background-color: #f5f5f5;
            padding: 20px;
            overflow-y: auto;
        }
        
        #map {
            flex: 1;
            height: 100%;
        }
        
        .form-group {
            margin-bottom: 15px;
        }
        
        button {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 8px 15px;
            cursor: pointer;
            width: 100%;
            margin-top: 10px;
        }
        
        /* Add more styling as needed */
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Urban Traffic Simulator</h1>
        </div>
        
        <div class="content">
            <div class="sidebar">
                <h2>Network Settings</h2>
                
                <div class="form-group">
                    <label for="location">Location</label>
                    <select id="location-preset">
                        <option value="custom">Custom Location</option>
                        <option value="jakarta">Jakarta, Indonesia</option>
                        <option value="newyork">New York, USA</option>
                        <option value="london">London, UK</option>
                    </select>
                </div>
                
                <div id="custom-location">
                    <div class="form-group">
                        <label for="latitude">Latitude</label>
                        <input type="number" id="latitude" step="0.0001" value="-6.2088">
                    </div>
                    
                    <div class="form-group">
                        <label for="longitude">Longitude</label>
                        <input type="number" id="longitude" step="0.0001" value="106.8456">
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="distance">Network Size (meters)</label>
                    <input type="range" id="distance" min="200" max="1000" step="100" value="500">
                    <span id="distance-value">500 meters</span>
                </div>
                
                <button id="load-network-btn">Load Network</button>
                <button id="reset-network-btn" disabled>Reset Network</button>
            </div>
            
            <div id="map"></div>
        </div>
    </div>
    
    <!-- Leaflet JS -->
    <script src="https://unpkg.com/leaflet@1.9.3/dist/leaflet.js"></script>
    
    <script>
        // Basic JavaScript to initialize the map
        let map = L.map('map').setView([-6.2088, 106.8456], 15);
        
        // Add the base map tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 19
        }).addTo(map);
        
        // Initialize variables
        let networkLayer = null;
        const loadNetworkBtn = document.getElementById('load-network-btn');
        const resetNetworkBtn = document.getElementById('reset-network-btn');
        
        // Add event listeners for your buttons
        loadNetworkBtn.addEventListener('click', loadNetwork);
        resetNetworkBtn.addEventListener('click', resetNetwork);
        
        // Implement loadNetwork function
        function loadNetwork() {
            // Get user inputs
            const lat = parseFloat(document.getElementById('latitude').value);
            const lng = parseFloat(document.getElementById('longitude').value);
            const dist = parseInt(document.getElementById('distance').value);
            
            // Make API request to your Flask backend
            fetch('/load_network', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    latitude: lat,
                    longitude: lng,
                    distance: dist
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Display the network on the map
                    displayNetwork(data.network);
                    resetNetworkBtn.disabled = false;
                } else {
                    alert('Error: ' + data.error);
                }
            });
        }
        
        // Add more JavaScript functions for handling the network display and interaction
        
        // Example: Display network function
        function displayNetwork(networkData) {
            // Remove existing network
            if (networkLayer) {
                map.removeLayer(networkLayer);
            }
            
            // Create a new layer with the network data
            networkLayer = L.geoJSON(networkData, {
                style: function(feature) {
                    if (feature.geometry.type === 'LineString') {
                        // Color based on traffic
                        const traffic = feature.properties.traffic;
                        let color = '#4daf4a';  // Green for low traffic
                        
                        if (traffic > 500) {
                            color = '#e41a1c';  // Red for high traffic
                        } else if (traffic > 200) {
                            color = '#ff7f00';  // Orange for medium traffic
                        }
                        
                        return {
                            color: color,
                            weight: feature.properties.width || 3,
                            opacity: 0.8
                        };
                    }
                },
                onEachFeature: function(feature, layer) {
                    // Add click handler for road segments
                    if (feature.geometry.type === 'LineString') {
                        layer.on('click', function() {
                            // Implement road closure functionality
                            if (confirm('Close this road segment?')) {
                                closeRoad(feature.properties);
                            }
                        });
                        
                        // Add tooltip with road info
                        layer.bindTooltip(`${feature.properties.name}<br>Traffic: ${feature.properties.traffic}`);
                    }
                }
            }).addTo(map);
            
            // Fit map to network bounds
            if (networkLayer.getBounds().isValid()) {
                map.fitBounds(networkLayer.getBounds());
            }
        }
        
        // Implement the resetNetwork and closeRoad functions
    </script>
</body>
</html>
```

## Step 6: Implementing Road Closure and Traffic Redistribution

Add these routes and functions to `app.py`:

```python
@app.route('/close_road', methods=['POST'])
def close_road():
    """Simulate closing a road segment and recalculate traffic"""
    global G, G_modified, edge_traffic
    
    if G is None:
        return jsonify({'success': False, 'error': 'No network loaded'})
    
    data = request.json
    u = data.get('node_from')
    v = data.get('node_to')
    k = int(data.get('key', 0))
    
    try:
        # Create a new modified graph
        G_modified = G.copy()
        
        # Remove the selected edge
        if G_modified.has_edge(u, v):
            G_modified.remove_edge(u, v)
        
        # Recalculate traffic
        edge_traffic = redistribute_traffic(G, G_modified, edge_traffic, (u, v, k))
        
        # Create GeoJSON representation of modified network
        network_geojson = create_network_geojson(G_modified, edge_traffic)
        
        return jsonify({
            'success': True,
            'network': network_geojson
        })
    except Exception as e:
        print(f"Error closing road: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/reset_network', methods=['POST'])
def reset_network():
    """Reset to the original network without closures"""
    global G, G_modified, edge_traffic
    
    if G is None:
        return jsonify({'success': False, 'error': 'No network loaded'})
    
    # Reset modified graph to original
    G_modified = G.copy()
    
    # Reset traffic to original values
    edge_traffic = generate_traffic(G)
    
    # Create GeoJSON with the original network
    network_geojson = create_network_geojson(G, edge_traffic)
    
    return jsonify({
        'success': True,
        'network': network_geojson
    })

def redistribute_traffic(original_graph, modified_graph, original_traffic, closed_edge):
    """
    Redistribute traffic after a road closure using a simple algorithm:
    - For the closed edge, find alternative paths between its endpoints
    - Distribute the traffic from the closed edge along these paths
    """
    u, v, k = closed_edge
    closed_traffic = original_traffic.get((u, v, k), 0)
    
    # Copy the original traffic
    new_traffic = original_traffic.copy()
    
    # Remove the closed edge's traffic
    new_traffic.pop((u, v, k), None)
    
    # Only redistribute if there was traffic on the closed edge
    if closed_traffic > 0:
        try:
            # Find shortest path between the endpoints in the modified graph
            path = nx.shortest_path(modified_graph, u, v, weight='length')
            
            # Distribute traffic along this path
            for i in range(len(path)-1):
                from_node = path[i]
                to_node = path[i+1]
                
                # Use key 0 for all edges in our simplified model
                edge = (from_node, to_node, 0)
                
                # Add traffic to this edge
                new_traffic[edge] = new_traffic.get(edge, 0) + closed_traffic
        except nx.NetworkXNoPath:
            # If no path exists, we cannot redistribute the traffic
            print(f"No alternative path found between {u} and {v}")
            pass
    
    return new_traffic
```

## Step 7: Completing the Frontend JavaScript

Add these JavaScript functions to your HTML file:

```javascript
// Function to close a road
function closeRoad(edge) {
    fetch('/close_road', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            node_from: edge.u,
            node_to: edge.v,
            key: edge.key
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayNetwork(data.network);
        } else {
            alert('Error: ' + data.error);
        }
    });
}

// Function to reset the network
function resetNetwork() {
    fetch('/reset_network', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayNetwork(data.network);
        } else {
            alert('Error: ' + data.error);
        }
    });
}

// Add event listener for location presets
document.getElementById('location-preset').addEventListener('change', function() {
    const locations = {
        jakarta: { lat: -6.2088, lng: 106.8456 },
        newyork: { lat: 40.7128, lng: -74.0060 },
        london: { lat: 51.5074, lng: -0.1278 }
    };
    
    if (this.value !== 'custom' && locations[this.value]) {
        document.getElementById('latitude').value = locations[this.value].lat;
        document.getElementById('longitude').value = locations[this.value].lng;
    }
});

// Update distance display when slider changes
document.getElementById('distance').addEventListener('input', function() {
    document.getElementById('distance-value').textContent = `${this.value} meters`;
});
```

## Step 8: Run Your Application

```bash
python app.py
```

Open your browser and navigate to `http://localhost:5001`

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