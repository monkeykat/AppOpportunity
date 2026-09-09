"""Ollama API client for the Scout app."""

import requests
import json
from typing import Optional, Dict, Any
from config import config


class OllamaClient:
    """Client for interacting with Ollama API."""
    
    def __init__(self, url: str = None, model: str = None):
        self.url = url or config['ollama_url']
        self.model = model or config['ollama_model']
    
    def warmup(self) -> bool:
        """Warm up the Ollama model by making a test call.
        
        This helps avoid long delays on the first actual request.
        
        Returns:
            True if warmup succeeded, False otherwise
        """
        try:
            response = requests.post(
                f"{self.url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": "hi",
                    "stream": False
                },
                timeout=120
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Warning: Ollama warmup failed: {e}")
            return False
    
    def generate(self, prompt: str, stream: bool = False) -> Optional[str]:
        """Generate a response from Ollama.
        
        Args:
            prompt: The prompt to send to Ollama
            stream: Whether to stream the response
            
        Returns:
            The generated response text, or None if there was an error
        """
        try:
            response = requests.post(
                f"{self.url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": stream
                },
                timeout=300
            )
            response.raise_for_status()
            
            if stream:
                # Handle streaming response
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        if 'response' in data:
                            full_response += data['response']
                return full_response
            else:
                # Handle non-streaming response
                data = response.json()
                return data.get('response', '')
                
        except requests.exceptions.RequestException as e:
            print(f"Error calling Ollama: {e}")
            return None
    
    def generate_json(self, prompt: str, expected_keys: list = None) -> Optional[Dict[str, Any]]:
        """Generate a JSON response from Ollama.
        
        Args:
            prompt: The prompt to send to Ollama
            expected_keys: List of expected keys in the JSON response
            
        Returns:
            The JSON response as a dictionary, or None if there was an error
        """
        # Add JSON format instruction to prompt
        json_prompt = f"""{prompt}

Return your response as a valid JSON object. If a response format is specified, use that format."""

        response = self.generate(json_prompt)
        
        if response is None:
            return None
        
        # Try to extract JSON from response
        try:
            # First try to parse the whole response as JSON
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                
                # Validate expected keys if provided
                if expected_keys:
                    for key in expected_keys:
                        if key not in data:
                            print(f"Missing expected key: {key}")
                            return None
                
                return data
            else:
                print("No JSON object found in response")
                return None
                
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            print(f"Response was: {response}")
            return None
