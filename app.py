import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
import os
from typing import Set, List, Optional
import networkx as nx
import tempfile

from data_model import KnowledgeGraph, NodeType, NodeMetadata
from visualization import generate_graph_visualization
from persistence import GraphPersistence

# Initialize session state
if 'graph' not in st.session_state:
    st.session_state.graph = KnowledgeGraph()
if 'selected_nodes' not in st.session_state:
    st.session_state.selected_nodes = set()
if 'show_levels' not in st.session_state:
    st.session_state.show_levels = [0, 1, 2]  # Show all levels by default
if 'selected_node_info' not in st.session_state:
    st.session_state.selected_node_info = None

# Initialize persistence
persistence = GraphPersistence()

# Create output directory for visualizations
try:
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
except Exception as e:
    st.error(f"Failed to create output directory: {str(e)}")
    # Fallback to temporary directory
    output_dir = Path(tempfile.gettempdir()) / 'knowledge_atlas'
    output_dir.mkdir(exist_ok=True)

# Load existing graph if available
if os.path.exists('knowledge_graph.pkl'):
    st.session_state.graph = persistence.load_graph()

def toggle_level(level: int):
    """Toggle visibility of a specific level in the graph."""
    if level in st.session_state.show_levels:
        st.session_state.show_levels.remove(level)
    else:
        st.session_state.show_levels.append(level)

def toggle_node_selection(node: str):
    """Toggle selection of a specific node."""
    if node in st.session_state.selected_nodes:
        st.session_state.selected_nodes.remove(node)
    else:
        st.session_state.selected_nodes.add(node)

def main():
    st.set_page_config(
        page_title="Knowledge Atlas",
        page_icon="📚",
        layout="wide"
    )
    
    st.title("📚 Knowledge Atlas")
    st.markdown("""
    Organize your reading materials and visualize knowledge connections.
    Add nodes and connect them to create your knowledge graph.
    """)
    
    # Sidebar
    with st.sidebar:
        st.header("Add New Content")
        
        # Add Node Section
        st.header("Add Node")
        with st.form("add_node_form"):
            node_name = st.text_input("Node Name")
            node_type = st.selectbox("Node Type", [t.value for t in NodeType])
            node_level = st.number_input("Level", min_value=0, max_value=10, value=0)
            node_url = st.text_input("URL (optional)")
            node_description = st.text_area("Description (optional)")
            
            if st.form_submit_button("Add Node"):
                if node_name:
                    metadata = NodeMetadata(url=node_url if node_url else None,
                                          description=node_description if node_description else None)
                    if st.session_state.graph.add_node(node_name, NodeType(node_type), node_level, metadata):
                        st.success(f"Added {node_name}")
                    else:
                        st.error(f"Node {node_name} already exists")
        
        # Add Edge Section
        st.header("Add Connection")
        with st.form("add_edge_form"):
            nodes = list(st.session_state.graph.graph.nodes())
            if len(nodes) >= 2:
                source = st.selectbox("Source Node", nodes)
                target = st.selectbox("Target Node", [n for n in nodes if n != source])
                relationship = st.text_input("Relationship Type", "related_to")
                
                if st.form_submit_button("Add Connection"):
                    if source and target and relationship:
                        if st.session_state.graph.add_edge(source, target, relationship):
                            st.success(f"Connected {source} to {target}")
                        else:
                            st.error("Failed to add connection")
            else:
                st.warning("Please add at least two nodes first!")
                st.form_submit_button("Add Connection", disabled=True)
        
        # Visualization Controls
        st.header("Visualization Controls")
        
        # Level visibility toggles
        st.subheader("Show/Hide Levels")
        for level in range(11):  # Support up to 10 levels
            if st.checkbox(f"Level {level}", value=level in st.session_state.show_levels):
                toggle_level(level)
        
        # Node selection
        st.subheader("Select Nodes")
        for node in st.session_state.graph.graph.nodes():
            if st.checkbox(node, value=node in st.session_state.selected_nodes):
                toggle_node_selection(node)
        
        # Node information
        if st.session_state.selected_node_info:
            st.subheader("Node Information")
            info = st.session_state.selected_node_info
            st.write(f"**Name:** {info['name']}")
            st.write(f"**Type:** {info['type'].value}")
            st.write(f"**Level:** {info['level']}")
            if info['metadata'].url:
                st.write(f"**URL:** [{info['metadata'].url}]({info['metadata'].url})")
            if info['metadata'].description:
                st.write(f"**Description:** {info['metadata'].description}")
            st.write("**Connected Nodes:**")
            for connected in info['connected_nodes']:
                st.write(f"- {connected}")
        
        # Save/Load Section
        if st.button("Save Graph"):
            if persistence.save_graph(st.session_state.graph.graph):
                st.success("Graph saved successfully!")
            else:
                st.error("Failed to save graph!")
    
    # Main content area - Graph Visualization
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Knowledge Graph Visualization")
        # Generate and display the graph
        graph = st.session_state.graph.graph
        if len(graph.nodes) > 0:
            try:
                output_file = output_dir / 'graph.html'
                if generate_graph_visualization(
                    graph,
                    show_levels=st.session_state.show_levels,
                    selected_nodes=st.session_state.selected_nodes if st.session_state.selected_nodes else None,
                    output_filename=str(output_file)
                ):
                    with open(output_file, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    components.html(html_content, height=600)
                else:
                    st.error("Failed to generate graph visualization. Please try again.")
            except Exception as e:
                st.error(f"Error displaying graph: {str(e)}")
        else:
            st.info("Add nodes to see the knowledge graph visualization!")
    
    with col2:
        st.subheader("Statistics")
        nodes_by_type = {}
        for node, data in graph.nodes(data=True):
            node_type = data.get('type')
            if node_type:
                nodes_by_type[node_type] = nodes_by_type.get(node_type, 0) + 1
        
        for node_type, count in nodes_by_type.items():
            st.metric(node_type.value.title(), count)
        
        st.metric("Total Nodes", len(graph.nodes))
        st.metric("Total Connections", len(graph.edges))

if __name__ == "__main__":
    main() 