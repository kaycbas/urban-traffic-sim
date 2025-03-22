# Urban Traffic Simulator

A web application that simulates traffic flow and road closures using real street networks from OpenStreetMap. This project allows users to explore how traffic redistributes when roads are closed in any location worldwide.

![Screenshot of the application](screenshot.png)

## Features

- Load real-world street networks from any location using OpenStreetMap data
- Generate realistic traffic volumes based on road types and centrality
- Simulate road closures and visualize traffic redistribution
- Interactive web interface with a dynamic map using Leaflet.js
- Color-coded visualization of traffic volumes
- Support for different cities and custom locations

## Technical Stack

- **Backend**: Python, Flask
- **Network Analysis**: NetworkX, OSMnx
- **Geospatial**: Shapely, GeoPandas
- **Frontend**: HTML, CSS, JavaScript, Leaflet.js for mapping

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/travel-model-mvp.git
   cd travel-model-mvp
   ```

2. Create a virtual environment and activate it:
   ```
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

   **Note for Apple Silicon (M1/M2/M3) Mac users**: When creating the virtual environment, ensure you're using a Python version compiled for ARM64 architecture to avoid compatibility issues with NumPy and other dependencies.

## Usage

1. Start the Flask development server:
   ```
   python3 app.py
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:5001
   ```

3. Use the application:
   - Select a location or enter custom coordinates
   - Click "Load Network" to fetch the transportation network
   - Click on a road segment to simulate closing it
   - Observe how traffic is redistributed throughout the network
   - Use "Reset Network" to restore the original state

## How It Works

1. **Network Loading**: The application downloads a street network from OpenStreetMap for the selected area using OSMnx.

2. **Traffic Assignment**: Traffic volumes are generated based on multiple factors:
   - Road classification (highways get more traffic than residential streets)
   - Road length (shorter segments might indicate denser areas)
   - Betweenness centrality (roads that connect many parts get more traffic)
   - Random variation to simulate real-world conditions

3. **Road Closure Simulation**: When a road is closed, the application:
   - Removes the selected edge from the network
   - Finds shortest alternative paths between the endpoints
   - Redistributes traffic along these alternative paths

4. **Visualization**: Traffic volumes are displayed using:
   - Color coding (green for low, orange for medium, red for high traffic)
   - Line thickness proportional to traffic volume
   - Interactive tooltips showing road names and traffic values

## Project Structure

- `app.py`: Main Flask application with all backend functionality
- `templates/index.html`: Frontend HTML template with embedded JavaScript
- `static/`: Directory for CSS, JavaScript, and images (if needed)
- `requirements.txt`: Python dependencies

## Limitations and Future Improvements

While this model uses real street networks, it's still a simplified simulation. Some limitations and potential improvements include:

- **Traffic Generation**: Though based on road characteristics, the traffic is still synthetic; could be enhanced with real traffic data
- **Redistribution Algorithm**: The current algorithm finds single shortest paths; more realistic models would distribute traffic across multiple alternative routes
- **Performance Considerations**: For better performance, limit network size to 500-1000 meters in high-density areas
- **Additional Features**:
  - Support for different transportation modes (public transit, cycling, etc.)
  - Time-based traffic patterns (rush hour vs. off-peak)
  - Multiple simultaneous closures
  - Directional traffic visualization with arrows
  - Analytics dashboard showing network metrics 
  - Ability to save and compare different scenarios

## License

[MIT License](LICENSE)

## Acknowledgments

- [OpenStreetMap](https://www.openstreetmap.org/) for providing the geographical data
- [OSMnx](https://github.com/gboeing/osmnx) for the Python package to work with OpenStreetMap street networks
- [NetworkX](https://networkx.org/) for graph analysis and algorithms
- [Leaflet.js](https://leafletjs.com/) for the interactive mapping library
- [Flask](https://flask.palletsprojects.com/) for the web framework

## Troubleshooting

If you encounter issues running the application:

1. **NumPy Architecture Errors**: If you see errors related to NumPy architecture mismatch on Apple Silicon Macs, try:
   ```
   # Remove the existing environment
   rm -rf venv
   
   # Create a new environment with ARM64 Python
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install "numpy<2.0"  # Install NumPy 1.x version first
   pip install -r requirements.txt
   ```

2. **Loading Large Networks**: If the application is slow or crashes when loading, try reducing the network size using the slider (200-500m recommended).

3. **Map Alignment Issues**: If the network doesn't align with the map, try reloading the page and selecting a smaller network size.