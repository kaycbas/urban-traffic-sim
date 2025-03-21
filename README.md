# Urban Traffic Simulator

A simplified travel model web application that demonstrates traffic redistribution when roads are closed. This project is built with Python, Flask, and interactive mapping tools.

![Screenshot of the application](screenshot.png)

## Features

- Generate synthetic transportation networks with a grid layout
- Assign synthetic traffic volumes to road segments
- Simulate road closures and visualize traffic redistribution
- Interactive web interface with a dynamic map

## Technical Stack

- **Backend**: Python, Flask
- **Network Analysis**: NetworkX
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
   pip3 install -r requirements.txt
   ```

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

1. **Network Loading**: The application downloads a street network from OpenStreetMap for the selected area.

2. **Traffic Assignment**: Synthetic traffic volumes are randomly assigned to each road segment.

3. **Road Closure Simulation**: When a road is closed, the application finds alternative routes and redistributes traffic along these paths.

4. **Visualization**: Traffic volumes are displayed using color coding (green for low, yellow for medium, red for high traffic) and line thickness.

## Project Structure

- `app.py`: Main Flask application with all backend functionality
- `templates/index.html`: Frontend HTML template with embedded JavaScript
- `static/`: Directory for CSS, JavaScript, and images (if needed)
- `requirements.txt`: Python dependencies

## Limitations and Future Improvements

This is a simplified model intended for demonstration purposes. Some limitations and potential improvements include:

- Currently uses random traffic data; could be enhanced with real data or more sophisticated generation
- The traffic redistribution algorithm is basic; could be improved with more advanced traffic assignment models
- Performance may be an issue for very large networks
- Add support for different transportation modes (public transit, cycling, etc.)
- Implement more sophisticated traffic simulation algorithms

## License

[MIT License](LICENSE)

## Acknowledgments

- [OpenStreetMap](https://www.openstreetmap.org/) for providing the geographical data
- [OSMnx](https://github.com/gboeing/osmnx) for the Python package to work with OpenStreetMap
- [Leaflet.js](https://leafletjs.com/) for the interactive mapping library