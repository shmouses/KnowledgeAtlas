import pickle
import os
from pathlib import Path
import networkx as nx
from typing import Optional

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
        
    def save_graph(self, graph: nx.DiGraph) -> bool:
        """
        Save the graph to disk.
        
        Args:
            graph: NetworkX DiGraph object to save
            
        Returns:
            bool: True if save was successful, False otherwise
        """
        try:
            with open(self.graph_file, 'wb') as f:
                pickle.dump(graph, f)
            return True
        except Exception as e:
            print(f"Error saving graph: {e}")
            return False
            
    def load_graph(self) -> Optional[nx.DiGraph]:
        """
        Load the graph from disk.
        
        Returns:
            Optional[nx.DiGraph]: The loaded graph or None if no graph exists or error occurs
        """
        try:
            if not self.graph_file.exists():
                return None
                
            with open(self.graph_file, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Error loading graph: {e}")
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