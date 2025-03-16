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
from llm_handler import LLMProvider, LLMConfig, LLMManager, format_json_response

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
if 'llm_manager' not in st.session_state:
    st.session_state.llm_manager = LLMManager()
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'api_keys' not in st.session_state:
    st.session_state.api_keys = {}

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

def initialize_session_state():
    if 'graph' not in st.session_state:
        st.session_state.graph = nx.MultiDiGraph()
    if 'llm_manager' not in st.session_state:
        st.session_state.llm_manager = LLMManager()
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'api_keys' not in st.session_state:
        st.session_state.api_keys = {}

def render_llm_tab():
    st.header("🤖 AI Knowledge Graph Assistant")
    
    # LLM Provider Configuration
    with st.expander("Configure LLM Providers", expanded=True):
        st.write("Configure your preferred LLM providers. Ollama is available for free local use.")
        
        # Ollama status
        ollama_available = st.session_state.llm_manager.handlers[LLMProvider.OLLAMA].is_available()
        st.write("Ollama Status:", "✅ Available" if ollama_available else "❌ Not Available")
        if not ollama_available:
            st.info("To use Ollama:\n1. Install Ollama from https://ollama.ai\n2. Run 'ollama run llama2'")
        
        # API Key Configuration
        for provider in [LLMProvider.OPENAI, LLMProvider.ANTHROPIC, LLMProvider.HUGGINGFACE]:
            col1, col2 = st.columns([3, 1])
            with col1:
                api_key = st.text_input(
                    f"{provider.value.title()} API Key",
                    type="password",
                    value=st.session_state.api_keys.get(provider, ""),
                    key=f"api_key_{provider.value}"
                )
            with col2:
                if st.button("Save", key=f"save_{provider.value}"):
                    if api_key:
                        st.session_state.api_keys[provider] = api_key
                        st.session_state.llm_manager.add_config(
                            LLMConfig(provider, api_key)
                        )
                        st.success(f"✅ {provider.value.title()} API key saved!")
                    else:
                        if provider in st.session_state.api_keys:
                            del st.session_state.api_keys[provider]
                        st.warning(f"❌ {provider.value.title()} API key removed")
    
    # Conversation Interface
    st.subheader("Knowledge Conversation")
    st.write("Describe your knowledge domain and papers, and I'll help create a knowledge graph.")
    
    # Display conversation history
    for i, (role, message) in enumerate(st.session_state.conversation_history):
        with st.chat_message(role):
            st.write(message)
    
    # User input
    if prompt := st.chat_input("Describe your knowledge or ask questions..."):
        st.session_state.conversation_history.append(("user", prompt))
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get available providers
        available_providers = st.session_state.llm_manager.get_available_providers()
        
        if not available_providers:
            with st.chat_message("assistant"):
                st.error("No LLM providers available. Please configure at least one provider.")
            st.session_state.conversation_history.append(
                ("assistant", "No LLM providers available. Please configure at least one provider.")
            )
        else:
            # Use the first available provider
            provider = available_providers[0]
            
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = st.session_state.llm_manager.generate_knowledge_graph_json(
                        "\n".join(msg for _, msg in st.session_state.conversation_history),
                        provider
                    )
                    
                    # Try to extract and format JSON
                    json_response = format_json_response(response)
                    
                    if json_response:
                        st.write("I've created a knowledge graph based on our conversation. You can:")
                        st.write("1. Continue the conversation to refine it")
                        st.write("2. Use the JSON below in the Import tab")
                        st.code(json_response, language="json")
                    else:
                        st.write(response)
                        st.write("Continue describing your knowledge domain, and I'll try to create a graph when there's enough information.")
                    
                    st.session_state.conversation_history.append(("assistant", response))
    
    # Clear conversation button
    if st.button("Clear Conversation"):
        st.session_state.conversation_history = []
        st.rerun()

def main():
    initialize_session_state()
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
    
    tab0, tab1, tab2, tab3, tab4 = st.tabs(["🤖 AI Assistant", "📤 Import", "➕ Add", "🎮 Controls"])
    
    with tab0:
        render_llm_tab()
    
    with tab1:
        render_import_tab()
    
    with tab2:
        render_add_tab()
    
    with tab3:
        render_controls_tab()
    
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