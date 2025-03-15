from pyvis.network import Network
import networkx as nx
import os
from typing import List, Set, Optional, Dict, Any
from data_model import NodeType, NodeMetadata

def generate_graph_visualization(
    graph: nx.MultiDiGraph,
    show_levels: List[int] = None,
    selected_nodes: Set[str] = None,
    selected_edges: Set[tuple] = None,
    show_edge_types: List[str] = None,
    output_filename: str = "graph.html"
) -> bool:
    """
    Generate an interactive visualization of the knowledge graph.
    
    Args:
        graph: The NetworkX graph to visualize
        show_levels: List of levels to show
        selected_nodes: Set of nodes to highlight
        selected_edges: Set of edges (source, target) to highlight
        show_edge_types: List of edge types (relationships) to show
        output_filename: Path to save the HTML file
    
    Returns:
        bool: True if visualization was generated successfully
    """
    try:
        print(f"Starting visualization generation with {len(graph.nodes())} nodes and {len(graph.edges())} edges")
        print(f"Show levels: {show_levels}")
        print(f"Selected nodes: {selected_nodes}")
        print(f"Selected edges: {selected_edges}")
        print(f"Show edge types: {show_edge_types}")
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_filename) or '.'
        os.makedirs(output_dir, exist_ok=True)
        print(f"Output directory created: {output_dir}")
        
        # Create a new network
        net = Network(
            height="750px",
            width="100%",
            bgcolor="#ffffff",
            font_color="black",
            directed=True,
            select_menu=False,  # Disable selection menu in visualization
            filter_menu=False   # Disable filter menu in visualization
        )
        
        # First pass: Add all nodes that should be visible
        visible_nodes = set()
        
        # Add nodes from selected levels
        if show_levels is not None:
            for node, data in graph.nodes(data=True):
                node_level = data.get('level')
                print(f"Checking node {node} with level {node_level}")
                if node_level in show_levels:
                    visible_nodes.add(node)
        else:
            # If no levels specified, show all nodes
            visible_nodes.update(graph.nodes())
        
        print(f"Nodes after level filtering: {visible_nodes}")
        
        # Add selected nodes regardless of their level
        if selected_nodes:
            visible_nodes.update(selected_nodes)
            print(f"Added selected nodes: {selected_nodes}")
        
        # Second pass: Add nodes that are connected to visible nodes
        connected_nodes = set()
        for node in visible_nodes:
            # Add neighbors (both predecessors and successors)
            predecessors = list(graph.predecessors(node))
            successors = list(graph.successors(node))
            print(f"Node {node} has predecessors: {predecessors} and successors: {successors}")
            connected_nodes.update(predecessors)
            connected_nodes.update(successors)
        
        print(f"Connected nodes found: {connected_nodes}")
        
        # Add connected nodes if their levels are selected
        if show_levels is not None:
            for node in connected_nodes:
                node_level = graph.nodes[node].get('level')
                print(f"Checking connected node {node} with level {node_level}")
                if node_level in show_levels:
                    visible_nodes.add(node)
        else:
            visible_nodes.update(connected_nodes)
        
        print(f"Final visible nodes: {visible_nodes}")
        
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
            
            print(f"Adding node {node} of type {node_type}")
            
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
        print("Adding edges...")
        for edge_data in graph.edges(data=True, keys=True):
            # Unpack edge data correctly
            if len(edge_data) == 4:
                source, target, key, data = edge_data
            else:
                source, target, data = edge_data
                key = 0
                
            # Get the relationship type
            relationship = data.get('relationship', 'related_to')
            print(f"Processing edge: {source} -> {target} ({relationship})")
            
            # Skip if edge type is not visible
            if show_edge_types is not None and relationship not in show_edge_types:
                print(f"Skipping edge {source} -> {target} (edge type not visible)")
                continue
            
            # Only add edges if both nodes are visible
            if source not in visible_nodes or target not in visible_nodes:
                print(f"Skipping edge {source} -> {target} (nodes not visible)")
                continue
            
            # Determine edge color based on relationship
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
            
            # Highlight selected edges (independent of node selection)
            if selected_edges and (source, target) in selected_edges:
                color = "#FFA500"  # Orange for selected edges
                width = 3
                dashes = False
            else:
                width = 1
                dashes = False
            
            print(f"Adding edge {source} -> {target} with relationship {relationship}")
            
            try:
                # Add edge with relationship label
                net.add_edge(str(source),  # Convert to string to ensure compatibility
                            str(target),
                            title=str(relationship),
                            color=color,
                            arrows=arrows,
                            width=width,
                            dashes=dashes,
                            label=str(relationship))
            except Exception as e:
                print(f"Error adding edge {source} -> {target}: {str(e)}")
                continue
        
        print("Configuring physics layout...")
        # Configure physics layout
        net.set_options("""
        {
            "physics": {
                "enabled": false,
                "stabilization": {
                    "enabled": true,
                    "iterations": 1000,
                    "updateInterval": 50,
                    "onlyDynamicEdges": false,
                    "fit": true
                }
            },
            "interaction": {
                "dragNodes": true,
                "dragView": true,
                "hideEdgesOnDrag": false,
                "hideNodesOnDrag": false,
                "hover": true,
                "navigationButtons": true,
                "selectable": false,
                "selectConnectedEdges": false,
                "multiselect": false,
                "zoomView": true
            },
            "layout": {
                "hierarchical": {
                    "enabled": false
                }
            },
            "manipulation": {
                "enabled": false
            }
        }
        """)
        
        print(f"Saving visualization to {output_filename}")
        # Save the visualization
        net.write_html(output_filename)
        print("Visualization generated successfully")
        return True
        
    except Exception as e:
        print(f"Error generating visualization: {str(e)}")
        import traceback
        traceback.print_exc()
        return False 