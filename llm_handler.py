from typing import Dict, Optional, List
from enum import Enum
import json
from abc import ABC, abstractmethod

class LLMProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"
    OLLAMA = "ollama"  # Free, local option

class LLMConfig:
    def __init__(self, provider: LLMProvider, api_key: Optional[str] = None, model_name: str = ""):
        self.provider = provider
        self.api_key = api_key
        self.model_name = model_name

class BaseLLMHandler(ABC):
    @abstractmethod
    def generate_response(self, prompt: str) -> str:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass

class OllamaHandler(BaseLLMHandler):
    def __init__(self, model_name: str = "llama2"):
        self.model_name = model_name
        
    def is_available(self) -> bool:
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags")
            return response.status_code == 200
        except:
            return False
        
    def generate_response(self, prompt: str) -> str:
        import requests
        
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": self.model_name, "prompt": prompt}
            )
            if response.status_code == 200:
                return response.json().get("response", "")
            return f"Error: {response.status_code}"
        except Exception as e:
            return f"Error: {str(e)}"

class LLMManager:
    def __init__(self):
        self.configs: Dict[LLMProvider, LLMConfig] = {}
        self.handlers: Dict[LLMProvider, BaseLLMHandler] = {
            LLMProvider.OLLAMA: OllamaHandler()
        }
    
    def add_config(self, config: LLMConfig):
        self.configs[config.provider] = config
        
    def get_available_providers(self) -> List[LLMProvider]:
        available = []
        for provider in LLMProvider:
            if provider == LLMProvider.OLLAMA:
                if self.handlers[provider].is_available():
                    available.append(provider)
            elif provider in self.configs:
                available.append(provider)
        return available

    def generate_knowledge_graph_json(self, conversation_text: str, provider: LLMProvider) -> str:
        # Base prompt template
        prompt = f"""
Based on the following conversation about knowledge and research papers, create a knowledge graph in JSON format.
The JSON should follow this structure:
{{
    "nodes": [
        {{
            "id": "unique_id",
            "type": "main_topic",  # Valid types: main_topic, sub_topic, paper, concept, method, tool, dataset, other
            "description": "Description text",
            "level": 0,  # 0 for main topics, increasing for subtopics and papers
            "url": "optional_url"
        }}
    ],
    "edges": [
        {{
            "source": "source_node_id",
            "target": "target_node_id",
            "relationship": "contains"  # or other relationship types
        }}
    ]
}}

Conversation:
{conversation_text}

Generate a valid JSON for the knowledge graph based on the conversation above.
"""
        if provider == LLMProvider.OLLAMA:
            return self.handlers[provider].generate_response(prompt)
        # Add handlers for other providers here
        return "Error: Provider not implemented"

def format_json_response(response: str) -> Optional[str]:
    """Extract and format JSON from LLM response."""
    try:
        # Try to find JSON-like content between curly braces
        start = response.find('{')
        end = response.rfind('}')
        if start >= 0 and end > start:
            json_str = response[start:end+1]
            # Validate by parsing
            json_obj = json.loads(json_str)
            return json.dumps(json_obj, indent=2)
        return None
    except:
        return None 