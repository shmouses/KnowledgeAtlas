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
if 'selected_edges' not in st.session_state:
    st.session_state.selected_edges = set()
if 'show_levels' not in st.session_state:
    st.session_state.show_levels = set([0, 1, 2])  # Show all levels by default, using set
if 'show_edge_types' not in st.session_state:  # Add edge visibility state
    st.session_state.show_edge_types = set(['belongs_to', 'related_to', 'depends_on'])
if 'selected_node_info' not in st.session_state:
    st.session_state.selected_node_info = None
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False

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
        st.session_state.show_levels.add(level)

def toggle_node_selection(node: str):
    """Toggle selection of a specific node."""
    if node in st.session_state.selected_nodes:
        st.session_state.selected_nodes.remove(node)
    else:
        st.session_state.selected_nodes.add(node)

def toggle_edge_selection(source: str, target: str):
    """Toggle selection of a specific edge."""
    edge = (source, target)
    if edge in st.session_state.selected_edges:
        st.session_state.selected_edges.remove(edge)
    else:
        st.session_state.selected_edges.add(edge)

def toggle_edge_type(edge_type: str):
    """Toggle visibility of a specific edge type in the graph."""
    if edge_type in st.session_state.show_edge_types:
        st.session_state.show_edge_types.remove(edge_type)
    else:
        st.session_state.show_edge_types.add(edge_type)

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
        # Add tabs for different operations
        tab1, tab2, tab3, tab4 = st.tabs(["Add", "Edit", "Delete", "Controls"])
        
        with tab1:
            st.header("Add New Content")
            
            # Add Node Section
            st.subheader("Add Node")
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
            st.subheader("Add Connection")
            with st.form("add_edge_form"):
                nodes = list(st.session_state.graph.graph.nodes())
                if len(nodes) >= 2:
                    source = st.selectbox("Source Node", nodes, key="add_edge_source")
                    target = st.selectbox("Target Node", [n for n in nodes if n != source], key="add_edge_target")
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
        
        with tab2:
            st.header("Edit Content")
            
            # Edit Node Section
            st.subheader("Edit Node")
            nodes = list(st.session_state.graph.graph.nodes())
            if nodes:
                selected_node = st.selectbox("Select Node to Edit", nodes, key="edit_node_select")
                if selected_node:
                    node_data = st.session_state.graph.graph.nodes[selected_node]
                    with st.form("edit_node_form"):
                        new_name = st.text_input("Node Name", value=selected_node)
                        new_type = st.selectbox("Node Type", 
                                              [t.value for t in NodeType], 
                                              index=[t.value for t in NodeType].index(node_data['type'].value))
                        new_level = st.number_input("Level", 
                                                  min_value=0, 
                                                  max_value=10, 
                                                  value=node_data.get('level', 0))
                        new_url = st.text_input("URL", 
                                              value=node_data.get('metadata', NodeMetadata()).url or "")
                        new_description = st.text_area("Description", 
                                                     value=node_data.get('metadata', NodeMetadata()).description or "")
                        
                        if st.form_submit_button("Update Node"):
                            try:
                                # Store old edges
                                old_edges = list(st.session_state.graph.graph.edges(selected_node, data=True))
                                
                                # Remove old node
                                if new_name != selected_node:
                                    st.session_state.graph.graph.remove_node(selected_node)
                                
                                # Add updated node
                                metadata = NodeMetadata(url=new_url if new_url else None,
                                                      description=new_description if new_description else None)
                                
                                # Update node attributes if name hasn't changed
                                if new_name == selected_node:
                                    st.session_state.graph.graph.nodes[selected_node]['type'] = NodeType(new_type)
                                    st.session_state.graph.graph.nodes[selected_node]['level'] = new_level
                                    st.session_state.graph.graph.nodes[selected_node]['metadata'] = metadata
                                    st.success(f"Updated node {selected_node}")
                                else:
                                    # Add as new node if name changed
                                    if st.session_state.graph.add_node(new_name, NodeType(new_type), new_level, metadata):
                                        # Restore edges with the new node name
                                        for source, target, data in old_edges:
                                            new_source = new_name if source == selected_node else source
                                            new_target = new_name if target == selected_node else target
                                            st.session_state.graph.add_edge(new_source, new_target, data.get('relationship', 'related_to'))
                                        st.success(f"Updated node {selected_node} to {new_name}")
                                    else:
                                        # If failed to add new node, restore the old one
                                        st.session_state.graph.add_node(selected_node, node_data['type'], node_data.get('level', 0), node_data.get('metadata', NodeMetadata()))
                                        for source, target, data in old_edges:
                                            st.session_state.graph.add_edge(source, target, data.get('relationship', 'related_to'))
                                        st.error(f"Failed to update node: {new_name} already exists")
                            except Exception as e:
                                st.error(f"Error updating node: {str(e)}")
            else:
                st.warning("No nodes to edit!")
            
            # Edit Edge Section
            st.subheader("Edit Edge")
            edges = list(st.session_state.graph.graph.edges(data=True))
            if edges:
                edge_labels = [f"{s} → {t} ({d.get('relationship', 'related_to')})" for s, t, d in edges]
                selected_edge_idx = st.selectbox("Select Edge to Edit", 
                                               range(len(edges)), 
                                               format_func=lambda x: edge_labels[x],
                                               key="edit_edge_select")
                
                if selected_edge_idx is not None:
                    source, target, data = edges[selected_edge_idx]
                    with st.form("edit_edge_form"):
                        new_source = st.selectbox("Source Node", nodes, 
                                                index=nodes.index(source),
                                                key="edit_edge_source")
                        new_target = st.selectbox("Target Node", 
                                                [n for n in nodes if n != new_source],
                                                index=[n for n in nodes if n != new_source].index(target),
                                                key="edit_edge_target")
                        new_relationship = st.text_input("Relationship Type", 
                                                       value=data.get('relationship', 'related_to'))
                        
                        if st.form_submit_button("Update Edge"):
                            # Remove old edge
                            st.session_state.graph.graph.remove_edge(source, target)
                            
                            # Add updated edge
                            if st.session_state.graph.add_edge(new_source, new_target, new_relationship):
                                st.success(f"Updated edge {source} → {target}")
                            else:
                                st.error("Failed to update edge")
            else:
                st.warning("No edges to edit!")
        
        with tab3:
            st.header("Delete Content")
            
            # Delete Node Section
            st.subheader("Delete Node")
            nodes = list(st.session_state.graph.graph.nodes())
            if nodes:
                node_to_delete = st.selectbox("Select Node to Delete", nodes, key="delete_node_select")
                if st.button("Delete Node"):
                    st.session_state.graph.graph.remove_node(node_to_delete)
                    st.success(f"Deleted node {node_to_delete}")
            else:
                st.warning("No nodes to delete!")
            
            # Delete Edge Section
            st.subheader("Delete Edge")
            edges = list(st.session_state.graph.graph.edges(data=True))
            if edges:
                edge_labels = [f"{s} → {t} ({d.get('relationship', 'related_to')})" for s, t, d in edges]
                edge_to_delete = st.selectbox("Select Edge to Delete", 
                                            range(len(edges)), 
                                            format_func=lambda x: edge_labels[x],
                                            key="delete_edge_select")
                
                if st.button("Delete Edge"):
                    source, target, _ = edges[edge_to_delete]
                    st.session_state.graph.graph.remove_edge(source, target)
                    st.success(f"Deleted edge {source} → {target}")
            else:
                st.warning("No edges to delete!")
        
        with tab4:
            st.header("Visualization Controls")
            
            # Level visibility toggles with "Select All" option
            with st.expander("📊 Show/Hide Levels", expanded=True):
                # Add "Select All" checkbox
                all_levels = set(range(11))  # 0 to 10
                if st.checkbox("Select All Levels", value=st.session_state.show_levels == all_levels):
                    st.session_state.show_levels = all_levels.copy()
                else:
                    # Individual level toggles in columns
                    cols = st.columns(3)
                    for i, level in enumerate(range(11)):
                        with cols[i % 3]:
                            if st.checkbox(f"Level {level}", value=level in st.session_state.show_levels):
                                st.session_state.show_levels.add(level)
                            elif level in st.session_state.show_levels:
                                st.session_state.show_levels.remove(level)
            
            # Edge type visibility toggles
            with st.expander("🔗 Edge Visibility", expanded=True):
                st.markdown("""
                **Control which types of edges are visible in the graph.**
                This is independent of edge selection below.
                """)
                
                # Get all unique edge types from the graph
                edge_types = set()
                for _, _, data in st.session_state.graph.graph.edges(data=True):
                    edge_types.add(data.get('relationship', 'related_to'))
                
                # Add default edge types if not in graph
                edge_types.update(['belongs_to', 'related_to', 'depends_on'])
                edge_types = sorted(list(edge_types))
                
                # Add "Show All" checkbox
                if st.checkbox("Show All Edge Types", value=st.session_state.show_edge_types == set(edge_types)):
                    st.session_state.show_edge_types = set(edge_types)
                else:
                    # Individual edge type toggles in columns
                    edge_cols = st.columns(2)
                    for i, edge_type in enumerate(edge_types):
                        with edge_cols[i % 2]:
                            current_value = edge_type in st.session_state.show_edge_types
                            if st.checkbox(
                                f"{edge_type}",
                                value=current_value,
                                key=f"edge_type_{edge_type}",
                                help=f"Show/hide all edges of type '{edge_type}'"
                            ):
                                if not current_value:  # If it was off and now should be on
                                    st.session_state.show_edge_types.add(edge_type)
                            elif current_value:  # If it was on and now should be off
                                st.session_state.show_edge_types.remove(edge_type)
            
            # Node and Edge Selection
            with st.expander("🔍 Select Elements", expanded=True):
                st.markdown("""
                **Highlight specific nodes and edges.**
                Selected items will be highlighted in gold/orange. This does not affect visibility.
                """)
                
                # Add "Clear All" button
                if st.button("Clear All Selections"):
                    st.session_state.selected_nodes.clear()
                    st.session_state.selected_edges.clear()
                
                # Node selection with search
                st.subheader("Select Nodes")
                nodes = list(st.session_state.graph.graph.nodes())
                if nodes:
                    # Add search box for nodes
                    search_term = st.text_input("Search Nodes", key="node_search").lower()
                    filtered_nodes = [node for node in nodes if search_term in node.lower()]
                    
                    # Create columns for node checkboxes
                    node_cols = st.columns(2)
                    for i, node in enumerate(filtered_nodes):
                        with node_cols[i % 2]:
                            if st.checkbox(node, value=node in st.session_state.selected_nodes, key=f"node_{node}"):
                                toggle_node_selection(node)
                else:
                    st.info("No nodes available to select.")
                
                # Edge selection with search
                st.subheader("Select Edges")
                edges = list(st.session_state.graph.graph.edges(data=True))
                if edges:
                    # Add search box for edges
                    search_term = st.text_input("Search Edges", key="edge_search").lower()
                    filtered_edges = []
                    for source, target, data in edges:
                        edge_label = f"{source} → {target} ({data.get('relationship', 'related_to')})"
                        if search_term in edge_label.lower():
                            filtered_edges.append((source, target, data))
                    
                    # Create columns for edge checkboxes
                    edge_cols = st.columns(1)
                    for source, target, data in filtered_edges:
                        edge_label = f"{source} → {target} ({data.get('relationship', 'related_to')})"
                        if st.checkbox(
                            edge_label,
                            value=(source, target) in st.session_state.selected_edges,
                            key=f"edge_{source}_{target}",
                            help="Highlight this edge in the graph"
                        ):
                            toggle_edge_selection(source, target)
                else:
                    st.info("No edges available to select.")
            
            # Node Information
            if st.session_state.selected_node_info:
                with st.expander("ℹ️ Node Information", expanded=True):
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
            with st.expander("💾 Save/Load", expanded=False):
                st.markdown("""
                ### Export Graph
                Download your current graph as JSON or save it to disk.
                """)
                
                # Export current graph
                if st.button("Export as JSON"):
                    json_str = persistence.export_to_json(st.session_state.graph.graph)
                    if json_str:
                        st.download_button(
                            "Download JSON",
                            json_str,
                            "knowledge_graph.json",
                            "application/json",
                            key='download_json'
                        )
                    else:
                        st.error("Failed to export graph!")
                
                if st.button("Save to Disk"):
                    if persistence.save_graph(st.session_state.graph.graph):
                        st.success("Graph saved successfully!")
                    else:
                        st.error("Failed to save graph!")
                
                st.markdown("""
                ### Import Graph
                Import a graph from JSON. You can either:
                1. Upload a JSON file
                2. Paste JSON text directly
                
                The current graph will be replaced with the imported one.
                """)
                
                # File uploader for JSON
                uploaded_file = st.file_uploader("Upload JSON file", type=['json'])
                if uploaded_file is not None:
                    try:
                        json_str = uploaded_file.getvalue().decode()
                        new_graph = persistence.import_from_json(json_str)
                        if new_graph:
                            st.session_state.graph.graph = new_graph
                            st.success("Graph imported successfully!")
                            st.experimental_rerun()
                        else:
                            st.error("Failed to import graph from file!")
                    except Exception as e:
                        st.error(f"Error importing graph: {str(e)}")
                
                # Text area for JSON input
                st.markdown("**Or paste JSON directly:**")
                json_input = st.text_area("JSON Input", height=150)
                if st.button("Import from JSON"):
                    if json_input:
                        try:
                            new_graph = persistence.import_from_json(json_input)
                            if new_graph:
                                st.session_state.graph.graph = new_graph
                                st.success("Graph imported successfully!")
                                st.experimental_rerun()
                            else:
                                st.error("Failed to import graph from text!")
                        except Exception as e:
                            st.error(f"Error importing graph: {str(e)}")
                    else:
                        st.warning("Please enter JSON text to import!")
    
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
                    show_levels=list(st.session_state.show_levels),  # Convert set to list
                    selected_nodes=st.session_state.selected_nodes if st.session_state.selected_nodes else None,
                    selected_edges=st.session_state.selected_edges if st.session_state.selected_edges else None,
                    show_edge_types=list(st.session_state.show_edge_types),  # Add edge types parameter
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