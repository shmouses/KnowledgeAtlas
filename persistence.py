import pickle
import os
from pathlib import Path
import networkx as nx
from typing import Optional, Dict, Any
import json
from data_model import NodeType, NodeMetadata

class GraphPersistence:
    def __init__(self, storage_dir: str = 'data'):
        """
        Initialize the persistence manager.
        
        Args:
            storage_dir: Directory where graph data will be stored
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.graph_file = self.storage_dir / 'knowledge_graph.pkl'
        
    def save_graph(self, graph: nx.MultiDiGraph, filename: str = 'knowledge_graph.pkl') -> bool:
        """Save graph to a pickle file."""
        try:
            with open(filename, 'wb') as f:
                pickle.dump(graph, f)
            return True
        except Exception as e:
            print(f"Error saving graph: {str(e)}")
            return False
    
    def load_graph(self, filename: str = 'knowledge_graph.pkl') -> Optional[nx.MultiDiGraph]:
        """Load graph from a pickle file."""
        try:
            with open(filename, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Error loading graph: {str(e)}")
            return None

    def export_to_json(self, graph: nx.MultiDiGraph) -> str:
        """Export graph to JSON string."""
        try:
            # Convert graph to dictionary
            graph_dict = {
                'nodes': [],
                'edges': []
            }
            
            # Add nodes with their attributes
            for node, data in graph.nodes(data=True):
                node_data = {
                    'id': node,
                    'type': data.get('type').value if data.get('type') else None,
                    'level': data.get('level', 0)
                }
                
                # Add metadata if exists
                metadata = data.get('metadata')
                if metadata:
                    node_data['url'] = metadata.url
                    node_data['description'] = metadata.description
                
                graph_dict['nodes'].append(node_data)
            
            # Add edges with their attributes
            for source, target, key, data in graph.edges(data=True, keys=True):
                edge_data = {
                    'source': source,
                    'target': target,
                    'relationship': data.get('relationship', 'related_to')
                }
                graph_dict['edges'].append(edge_data)
            
            return json.dumps(graph_dict, indent=2)
        
        except Exception as e:
            print(f"Error exporting graph to JSON: {str(e)}")
            return ""

    def import_from_json(self, json_str: str) -> Optional[nx.MultiDiGraph]:
        """Import graph from JSON string."""
        try:
            # Parse JSON string
            graph_dict = json.loads(json_str)
            
            # Create new graph
            graph = nx.MultiDiGraph()
            
            # Validate the JSON structure
            if not isinstance(graph_dict, dict) or 'nodes' not in graph_dict:
                print("Invalid JSON format: missing 'nodes' array")
                return None
            
            # Get valid node types
            valid_types = {t.value: t for t in NodeType}
            print(f"Valid node types: {list(valid_types.keys())}")
            
            # Add nodes with their attributes
            for node_data in graph_dict['nodes']:
                try:
                    # Validate required node fields
                    if 'id' not in node_data:
                        print(f"Invalid node data: missing 'id' field - {node_data}")
                        continue
                    
                    # Get and validate node type
                    node_type_str = node_data.get('type', '').lower() if node_data.get('type') else None
                    if not node_type_str:
                        print(f"Warning: Node '{node_data['id']}' has no type specified, using 'other'")
                        node_type_str = 'other'
                    
                    if node_type_str not in valid_types:
                        print(f"Invalid node type '{node_type_str}' for node '{node_data['id']}'. Valid types are: {list(valid_types.keys())}")
                        continue
                    
                    # Create metadata
                    metadata = NodeMetadata(
                        url=node_data.get('url'),
                        description=node_data.get('description')
                    )
                    
                    # Add node to graph
                    graph.add_node(
                        node_data['id'],
                        type=valid_types[node_type_str],
                        level=node_data.get('level', 0),
                        metadata=metadata
                    )
                    print(f"Added node: {node_data['id']} (type: {node_type_str})")
                    
                except Exception as e:
                    print(f"Error adding node {node_data.get('id', 'unknown')}: {str(e)}")
                    continue
            
            # Add edges if any nodes were added
            if len(graph.nodes) > 0 and 'edges' in graph_dict:
                for edge_data in graph_dict['edges']:
                    try:
                        source = edge_data.get('source')
                        target = edge_data.get('target')
                        
                        if not source or not target:
                            print(f"Invalid edge data: missing source or target - {edge_data}")
                            continue
                        
                        if source not in graph.nodes or target not in graph.nodes:
                            print(f"Invalid edge: source or target node not found - {edge_data}")
                            continue
                        
                        relationship = edge_data.get('relationship', 'related_to')
                        graph.add_edge(source, target, relationship=relationship)
                        print(f"Added edge: {source} -> {target} ({relationship})")
                        
                    except Exception as e:
                        print(f"Error adding edge: {str(e)}")
                        continue
            
            if len(graph.nodes) == 0:
                print("No valid nodes were found in the JSON data")
                return None
            
            print(f"Successfully imported graph with {len(graph.nodes)} nodes and {len(graph.edges)} edges")
            return graph
            
        except json.JSONDecodeError as e:
            print(f"Invalid JSON format: {str(e)}")
            return None
        except Exception as e:
            print(f"Error importing graph from JSON: {str(e)}")
            return None
            
    def backup_graph(self, backup_name: str = None) -> bool:
        """
        Create a backup of the current graph.
        
        Args:
            backup_name: Optional name for the backup file
            
        Returns:
            bool: True if backup was successful, False otherwise
        """
        if not self.graph_file.exists():
            return False
            
        try:
            backup_file = self.storage_dir / f'knowledge_graph_backup_{backup_name or "latest"}.pkl'
            with open(self.graph_file, 'rb') as src, open(backup_file, 'wb') as dst:
                dst.write(src.read())
            return True
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False 