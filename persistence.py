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
            
            # Add nodes with their attributes
            for node_data in graph_dict['nodes']:
                metadata = NodeMetadata(
                    url=node_data.get('url'),
                    description=node_data.get('description')
                )
                
                graph.add_node(
                    node_data['id'],
                    type=NodeType(node_data['type']) if node_data.get('type') else None,
                    level=node_data.get('level', 0),
                    metadata=metadata
                )
            
            # Add edges with their attributes
            for edge_data in graph_dict['edges']:
                graph.add_edge(
                    edge_data['source'],
                    edge_data['target'],
                    relationship=edge_data.get('relationship', 'related_to')
                )
            
            return graph
            
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