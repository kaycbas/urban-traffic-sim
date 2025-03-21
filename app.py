import os
import json
import random
import networkx as nx
from flask import Flask, render_template, request, jsonify

# Set up Flask app
app = Flask(__name__)

# Global variables to store network data
G = None  # The original network
G_modified = None  # The network with a road closure
edge_traffic = {}  # Traffic volumes on edges

# Default center coordinates (Jakarta, Indonesia)
DEFAULT_CENTER = (-6.2088, 106.8456)

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/load_network', methods=['POST'])
def load_network():
    """Create a synthetic network without using numpy"""
    data = request.json
    
    # Get location from request, or use default
    lat = float(data.get('latitude', DEFAULT_CENTER[0]))
    lng = float(data.get('longitude', DEFAULT_CENTER[1]))
    
    # Create a synthetic network
    global G, G_modified, edge_traffic
    try:
        # Create a grid graph as a demo
        G = nx.grid_2d_graph(10, 10)
        
        # Convert node IDs to integers and add coordinates
        mapping = {}
        for i, node in enumerate(G.nodes()):
            mapping[node] = i
            # Add coordinates that will be centered around the specified lat/lng
            G.nodes[node]['x'] = lng + (node[0] - 5) * 0.001
            G.nodes[node]['y'] = lat + (node[1] - 5) * 0.001
        
        # Relabel nodes to use integers
        G = nx.relabel_nodes(G, mapping)
        
        # Make a copy for modifications
        G_modified = G.copy()
        
        # Generate synthetic traffic data using random instead of numpy
        edge_traffic = {}
        for u, v in G.edges():
            edge_traffic[(u, v, 0)] = random.randint(10, 1000)
        
        # Create a GeoJSON representation of the network with traffic
        network_geojson = create_network_geojson(G, edge_traffic)
        
        return jsonify({
            'success': True,
            'center': [lat, lng],
            'network': network_geojson
        })
    except Exception as e:
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
    u = int(data.get('node_from'))
    v = int(data.get('node_to'))
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
    edge_traffic = {}
    for u, v in G.edges():
        edge_traffic[(u, v, 0)] = random.randint(10, 1000)
    
    # Create GeoJSON with the original network
    network_geojson = create_network_geojson(G, edge_traffic)
    
    return jsonify({
        'success': True,
        'network': network_geojson
    })

def create_network_geojson(graph, traffic_data):
    """Convert network to GeoJSON format with traffic data"""
    features = []
    
    # Add edges as LineString features
    for u, v in graph.edges():
        # Create key 0 for all edges (simplified model)
        k = 0
        
        # Get node coordinates to create lines
        x1, y1 = graph.nodes[u]['x'], graph.nodes[u]['y']
        x2, y2 = graph.nodes[v]['x'], graph.nodes[v]['y']
        coords = [(x1, y1), (x2, y2)]
        
        # Get traffic for this edge
        traffic = traffic_data.get((u, v, k), 0)
        
        # Calculate line width based on traffic
        width = 1 + (traffic / 200)  # Scale width by traffic
        
        # Create GeoJSON Feature
        feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'LineString',
                'coordinates': [[c[0], c[1]] for c in coords]
            },
            'properties': {
                'u': u,
                'v': v,
                'key': k,
                'name': f'Road {u}-{v}',
                'highway': 'road',
                'traffic': traffic,
                'width': width
            }
        }
        features.append(feature)
    
    # Add nodes as Point features
    for node_id, data in graph.nodes(data=True):
        feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [data['x'], data['y']]
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
            path = nx.shortest_path(modified_graph, u, v)
            
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
            pass
    
    return new_traffic

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)