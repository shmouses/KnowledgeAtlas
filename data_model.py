import networkx as nx
from typing import Dict, Any, List, Optional, Set
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

@dataclass
class NodeMetadata:
    url: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

class NodeType(Enum):
    MAIN_TOPIC = "main_topic"
    SUB_TOPIC = "sub_topic"
    PAPER = "paper"
    CONCEPT = "concept"
    METHOD = "method"
    TOOL = "tool"
    DATASET = "dataset"
    OTHER = "other"

class KnowledgeGraph:
    def __init__(self):
        self.graph = nx.MultiDiGraph()  # Using MultiDiGraph for multiple edges
    
    def add_node(self, name: str, node_type: NodeType, level: int, 
                metadata: Optional[NodeMetadata] = None,
                attributes: Optional[Dict[str, Any]] = None) -> bool:
        """Add a node of any type to the graph."""
        if name not in self.graph:
            node_attrs = {
                'type': node_type,
                'level': level,
                'metadata': metadata or NodeMetadata()
            }
            if attributes:
                node_attrs.update(attributes)
            self.graph.add_node(name, **node_attrs)
            return True
        return False

    def add_edge(self, source: str, target: str, 
                relationship: str = 'related_to',
                attributes: Optional[Dict[str, Any]] = None) -> bool:
        """Add an edge between two nodes with optional attributes."""
        if source not in self.graph or target not in self.graph:
            return False
        
        edge_attrs = {'relationship': relationship}
        if attributes:
            edge_attrs.update(attributes)
        
        self.graph.add_edge(source, target, **edge_attrs)
        return True

    def update_node_metadata(self, node: str, metadata: NodeMetadata) -> bool:
        """Update metadata for a node."""
        if node in self.graph:
            self.graph.nodes[node]['metadata'] = metadata
            return True
        return False

    def get_node_metadata(self, node: str) -> Optional[NodeMetadata]:
        """Get metadata for a node."""
        if node in self.graph:
            return self.graph.nodes[node].get('metadata')
        return None

    def get_node_level(self, node: str) -> Optional[int]:
        """Get the level of a node."""
        if node in self.graph:
            return self.graph.nodes[node].get('level')
        return None

    def get_node_type(self, node: str) -> Optional[NodeType]:
        """Get the type of a node."""
        if node in self.graph:
            return self.graph.nodes[node].get('type')
        return None

    def get_edges_between(self, source: str, target: str) -> List[Dict[str, Any]]:
        """Get all edges between two nodes with their attributes."""
        if source in self.graph and target in self.graph:
            return list(self.graph.get_edge_data(source, target).values())
        return []

    def get_nodes_by_type(self, node_type: NodeType) -> List[str]:
        """Get all nodes of a specific type."""
        return [node for node, attr in self.graph.nodes(data=True) 
                if attr.get('type') == node_type]

    def get_nodes_by_level(self, level: int) -> List[str]:
        """Get all nodes at a specific level."""
        return [node for node, attr in self.graph.nodes(data=True) 
                if attr.get('level') == level]

    def get_connected_nodes(self, node: str, 
                          relationship: Optional[str] = None) -> List[str]:
        """Get all nodes connected to a given node, optionally filtered by relationship."""
        if node not in self.graph:
            return []
        
        connected = []
        for neighbor in self.graph.neighbors(node):
            edges = self.get_edges_between(node, neighbor)
            if relationship is None or any(edge.get('relationship') == relationship 
                                         for edge in edges):
                connected.append(neighbor)
        return connected

    def get_node_info(self, node: str) -> Optional[Dict[str, Any]]:
        """Get complete information about a node."""
        if node not in self.graph:
            return None
        
        node_data = self.graph.nodes[node]
        return {
            'name': node,
            'type': node_data.get('type'),
            'level': node_data.get('level'),
            'metadata': node_data.get('metadata'),
            'connected_nodes': self.get_connected_nodes(node)
        }

    def get_graph(self) -> nx.MultiDiGraph:
        """Return the underlying NetworkX graph."""
        return self.graph 