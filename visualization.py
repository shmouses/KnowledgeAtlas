from pyvis.network import Network
import networkx as nx
import os
from typing import List, Set, Optional, Dict, Any
from data_model import NodeType, NodeMetadata

def generate_graph_visualization(graph: nx.MultiDiGraph,
                              show_levels: Optional[List[int]] = None,
                              selected_nodes: Optional[Set[str]] = None,
                              output_filename: str = "graph.html") -> bool:
    """Generate an interactive visualization of the knowledge graph."""
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_filename) or '.'
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a new network
        net = Network(height="750px", width="100%", bgcolor="#ffffff", font_color="black")
        
        # First pass: Add all nodes that should be visible
        visible_nodes = set()
        for node, data in graph.nodes(data=True):
            # Include node if it's in selected levels or if it's connected to a visible node
            if show_levels is None or data.get('level') in show_levels:
                visible_nodes.add(node)
        
        # Second pass: Add nodes that are connected to visible nodes
        for node, data in graph.nodes(data=True):
            if node not in visible_nodes:
                # Check if this node is connected to any visible node
                for visible_node in visible_nodes:
                    if graph.has_edge(node, visible_node) or graph.has_edge(visible_node, node):
                        visible_nodes.add(node)
                        break
        
        # Add nodes to visualization
        for node, data in graph.nodes(data=True):
            if node not in visible_nodes:
                continue
                
            # Determine node color and shape based on type
            node_type = data.get('type')
            if node_type == NodeType.MAIN_TOPIC:
                color = "#ff7f7f"  # Light red
                shape = "dot"
            elif node_type == NodeType.SUB_TOPIC:
                color = "#7f7fff"  # Light blue
                shape = "dot"
            elif node_type == NodeType.PAPER:
                color = "#7fff7f"  # Light green
                shape = "diamond"
            elif node_type == NodeType.CONCEPT:
                color = "#ff7fff"  # Light purple
                shape = "triangle"
            elif node_type == NodeType.METHOD:
                color = "#ffff7f"  # Light yellow
                shape = "star"
            elif node_type == NodeType.TOOL:
                color = "#7fffff"  # Light cyan
                shape = "square"
            elif node_type == NodeType.DATASET:
                color = "#ffa07a"  # Light salmon
                shape = "hexagon"
            else:
                color = "#d3d3d3"  # Light gray
                shape = "dot"
            
            # Add node with metadata
            metadata = data.get('metadata', NodeMetadata())
            title = f"{node}<br>"
            if metadata.url:
                title += f"<a href='{metadata.url}' target='_blank'>URL</a><br>"
            if metadata.description:
                title += f"Description: {metadata.description}<br>"
            title += f"Type: {node_type.value}<br>"
            title += f"Level: {data.get('level')}"
            
            # Highlight selected nodes
            if selected_nodes and node in selected_nodes:
                color = "#ffd700"  # Gold
                size = 30
            else:
                size = 20
            
            net.add_node(node, 
                        label=node,
                        title=title,
                        color=color,
                        shape=shape,
                        size=size,
                        level=data.get('level', 0))
        
        # Add edges with relationship labels
        for edge in graph.edges(data=True, keys=True):
            source, target, key = edge
            data = edge[3]  # Edge data
            
            # Only add edges between visible nodes
            if source not in visible_nodes or target not in visible_nodes:
                continue
            
            # Skip edges where either node is not selected
            if selected_nodes and (source not in selected_nodes and target not in selected_nodes):
                continue
            
            # Determine edge color based on relationship
            relationship = data.get('relationship', 'related_to')
            if relationship == 'belongs_to':
                color = "#808080"  # Gray
                arrows = "to"
            elif relationship == 'related_to':
                color = "#0000ff"  # Blue
                arrows = "to"
            elif relationship == 'depends_on':
                color = "#ff0000"  # Red
                arrows = "to"
            else:
                color = "#000000"  # Black
                arrows = "to"
            
            # Add edge with relationship label
            net.add_edge(source, 
                        target,
                        title=relationship,
                        color=color,
                        arrows=arrows,
                        label=relationship)
        
        # Configure physics layout
        net.set_options("""
        {
            "physics": {
                "forceAtlas2Based": {
                    "gravitationalConstant": -100,
                    "centralGravity": 0.01,
                    "springLength": 200,
                    "springConstant": 0.08
                },
                "maxVelocity": 50,
                "solver": "forceAtlas2Based",
                "timestep": 0.35,
                "stabilization": {
                    "enabled": true,
                    "iterations": 1000,
                    "updateInterval": 50
                }
            },
            "layout": {
                "hierarchical": {
                    "enabled": true,
                    "direction": "LR",
                    "sortMethod": "directed",
                    "levelSeparation": 150
                }
            }
        }
        """)
        
        # Save the visualization
        net.write_html(output_filename)
        return True
        
    except Exception as e:
        print(f"Error generating visualization: {str(e)}")
        return False 