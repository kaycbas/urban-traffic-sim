# Simplified Travel Model Web App

## Setup Instructions (Mac)
1. Ensure Python 3.9+ is installed: `python3 --version`.
2. Create and activate a virtual environment:
   - `python3 -m venv venv`
   - `source venv/bin/activate`
3. Install dependencies: `pip install flask osmnx networkx folium pandas`.
4. If osmnx fails, install geospatial tools: `brew install geos gdal`, then retry.
5. Run the app: `python app.py` and visit `http://localhost:5000`. 