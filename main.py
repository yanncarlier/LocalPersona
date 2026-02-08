import os
import re
import yaml
import json
import requests
from typing import List, Dict

# --- CONFIGURATION ---
API_URL = "http://localhost:8080/v1/chat/completions"
CONTEXT_DIR = "context"

class OSAgentOrchestrator:
    """
    Implements progressive disclosure by scanning files in a specified directory 
    and only injecting relevant assertive context into the LLM prompt.
    """
    
    def __init__(self, directory: str):
        self.directory = directory
        self.registry: Dict[str, Dict] = {}
        self._initialize_registry()

    def _initialize_registry(self):
        """
        Layer 1: The 'Thin' Scan.
        Indexes the metadata (triggers and descriptions) of all context files.
        """
        if not os.path.exists(self.directory):
            print(f"[!] Warning: Directory '{self.directory}' not found. Creating it...")
            os.makedirs(self.directory)
            return

        print(f"[*] Indexing knowledge from {self.directory}...")
        for filename in os.listdir(self.directory):
            if filename.endswith(".md"):
                path = os.path.join(self.directory, filename)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Extract YAML frontmatter
                        match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
                        if match:
                            meta = yaml.safe_load(match.group(1))
                        else:
                            # Create default metadata if no YAML frontmatter
                            meta = {}
                        
                        meta['path'] = path
                        # Set name from YAML or use filename
                        if 'name' not in meta:
                            meta['name'] = filename.split('.')[0]
                        # Set triggers from YAML or use filename as fallback
                        if 'triggers' not in meta:
                            meta['triggers'] = [filename.split('.')[0].lower()]
                        
                        self.registry[meta.get('name')] = meta
                        print(f"[+] Loaded: {meta['name']} (triggers: {meta['triggers']})")
                except Exception as e:
                    print(f"[!] Error parsing {filename}: {e}")

    def get_assertive_context(self, user_input: str) -> str:
        """
        Layer 2: Progressive Disclosure.
        Retrieves full assertive instructions only if keywords match.
        """
        disclosed_text = ""
        input_lower = user_input.lower()
        
        for name, meta in self.registry.items():
            if any(trigger in input_lower for trigger in meta.get('triggers', [])):
                print(f"[+] Disclosing specialized context: {name}")
                with open(meta['path'], 'r', encoding='utf-8') as f:
                    # Remove the YAML block to keep the prompt clean
                    body = re.sub(r'^---\s*\n.*?\n---\s*\n', '', f.read(), flags=re.DOTALL)
                    disclosed_text += f"\n### SPECIALIZED INSTRUCTIONS: {name.upper()} ###\n"
                    disclosed_text += body.strip() + "\n"
        
        return disclosed_text

def chat_with_llama(user_query: str, context: str):
    """
    Constructs the payload and posts to the llama.cpp server.
    """
    system_prompt = (
        "You are a specialized AI assistant. "
        "Strictly follow the formatting and logic rules provided in the context below. "
        "If no context is provided, answer concisely."
    )
    
    if context:
        system_prompt += f"\n\nCURRENT ASSERTIVE CONTEXT:\n{context}"

    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ],
        "temperature": 0.1,  # Low temp for high assertion/rule adherence
        "stream": False
    }

    try:
        response = requests.post(API_URL, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to llama.cpp. Is the server running at :8080?"
    except Exception as e:
        return f"Error: {str(e)}"

def run_interactive_session():
    orchestrator = OSAgentOrchestrator(CONTEXT_DIR)
    
    print("\n--- OSAgent CONTEXT ENGINE READY ---")
    print(f"Directory: {CONTEXT_DIR}/")
    print(f"Endpoint: {API_URL}")
    print("--------------------------------------\n")

    while True:
        prompt = input("User> ")
        if prompt.lower() in ['exit', 'quit', 'q']:
            break

        # 1. Progressive Disclosure Step
        context = orchestrator.get_assertive_context(prompt)
        
        # 2. Inference Step
        print("AI Thinking...")
        response = chat_with_llama(prompt, context)
        
        print(f"\nAssistant:\n{response}\n")
        print("-" * 20)

if __name__ == "__main__":
    run_interactive_session()