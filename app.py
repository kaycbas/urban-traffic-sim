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

# Default center coordinates (Jakarta, Indonesia)
DEFAULT_CENTER = (-6.2088, 106.8456)
DEFAULT_DIST = 500  # meters - smaller area for OSM data to load quickly

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

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
        
        # Store original lat/lng before projection
        for node_id, data in G.nodes(data=True):
            G.nodes[node_id]['lon'] = data['x']
            G.nodes[node_id]['lat'] = data['y']
            
        # Ensure the graph is projected to a useful CRS for accurate geometry
        G = ox.project_graph(G)
        
        # Convert MultiDiGraph to DiGraph to simplify
        G = nx.DiGraph(G)
        
        # Make a copy for modifications
        G_modified = G.copy()
        
        # Generate synthetic traffic based on road types and centrality
        edge_traffic = generate_traffic(G)
        
        # Create a GeoJSON representation of the network with traffic
        network_geojson = create_network_geojson(G, edge_traffic)
        
        # Note: Leaflet expects [lat, lng] for setView
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
    # If it fails or takes too long, we'll use a simpler approach
    try:
        # Calculate betweenness centrality with a limit on number of sample nodes to keep it fast
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
            # Regular roads
            elif highway_type in ['residential', 'unclassified', 'road']:
                road_factor = 1.0
            # Service roads
            else:
                road_factor = 0.5
        
        # Length factor - shorter segments might be in denser areas
        length_factor = 1.0
        if 'length' in data:
            # Normalize length - shorter segments get more traffic (usually in busier areas)
            if data['length'] > 0:
                length_factor = 200 / max(data['length'], 50)  # Cap the effect for very short segments
                length_factor = min(2.0, max(0.5, length_factor))  # Keep between 0.5 and 2.0
        
        # Centrality factor - based on betweenness
        centrality_factor = 1.0
        if (u, v) in bc_edges:
            # Scale centrality to a reasonable range
            centrality = bc_edges[(u, v)]
            if centrality > 0:
                centrality_factor = 1.0 + 2.0 * centrality / max(bc_edges.values())
        
        # Add some randomness
        random_factor = random.uniform(0.8, 1.2)
        
        # Calculate final traffic
        # Convert to int and ensure it's between 10 and 1000
        edge_traffic = int(base_traffic * road_factor * length_factor * centrality_factor * random_factor)
        traffic[(u, v, 0)] = max(10, min(1000, edge_traffic))
    
    return traffic

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
        width = 1.5 + (traffic / 150)  # Scale width by traffic
        
        # Get edge geometry if it exists
        if 'geometry' in data:
            # Use the existing LineString geometry
            coords = []
            if hasattr(data['geometry'], 'coords'):
                # Convert projected coordinates back to lat/lng for GeoJSON
                if 'crs' in data and data['crs'] == 'EPSG:4326':
                    # These are already lat/lng coordinates
                    coords = list(data['geometry'].coords)
                else:
                    # Get nodes' lat/lng from the original graph - this is needed because
                    # we've projected the graph and the x,y are no longer lat/lng
                    coords = [(graph.nodes[u].get('lon', graph.nodes[u]['x']), 
                              graph.nodes[u].get('lat', graph.nodes[u]['y'])), 
                             (graph.nodes[v].get('lon', graph.nodes[v]['x']), 
                              graph.nodes[v].get('lat', graph.nodes[v]['y']))]
            else:
                # Fallback to node lat/lng coords 
                coords = [(graph.nodes[u].get('lon', graph.nodes[u]['x']), 
                          graph.nodes[u].get('lat', graph.nodes[u]['y'])), 
                         (graph.nodes[v].get('lon', graph.nodes[v]['x']), 
                          graph.nodes[v].get('lat', graph.nodes[v]['y']))]
        else:
            # Create a straight line from node to node using lat/lng coords
            coords = [(graph.nodes[u].get('lon', graph.nodes[u]['x']), 
                      graph.nodes[u].get('lat', graph.nodes[u]['y'])), 
                     (graph.nodes[v].get('lon', graph.nodes[v]['x']), 
                      graph.nodes[v].get('lat', graph.nodes[v]['y']))]
        
        # Get road name if available
        name = "Unnamed Road"
        if 'name' in data:
            name = data['name']
        elif 'highway' in data:
            name = f"{data['highway'].replace('_', ' ').title()}"
        
        # Get highway type
        highway = "road"
        if 'highway' in data:
            highway = data['highway']
        
        # Create GeoJSON Feature
        # Note: GeoJSON format expects [lon, lat] order for coordinates
        feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'LineString',
                'coordinates': [[c[0], c[1]] for c in coords]  # already in [lon, lat] format
            },
            'properties': {
                'u': u,
                'v': v,
                'key': k,
                'name': name,
                'highway': highway,
                'traffic': traffic,
                'width': width
            }
        }
        features.append(feature)
    
    # Add nodes as Point features (but only a limited number to keep the visualization clean)
    # Use a threshold to only include important nodes
    node_count = len(graph.nodes())
    if node_count <= 1000:  # Only add nodes if there aren't too many
        for node_id, data in graph.nodes(data=True):
            # Get longitude and latitude from the node data
            # OSMnx stores original coordinates as 'lon', 'lat' and projected as 'x', 'y'
            lon = data.get('lon', data.get('x'))
            lat = data.get('lat', data.get('y'))
            
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [lon, lat]
                },
                'properties': {
                    'id': node_id,
                    'type': 'node'
                }
            }
            features.append(feature)
    
    return {
        'type': 'FeatureCollection',
        'features': features
    }

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)