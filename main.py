import os
import re
import yaml
import json
import requests
import subprocess
from typing import List, Dict, Tuple

# --- CONFIGURATION ---
API_URL = "http://localhost:8080/v1/chat/completions"
CONTEXT_DIR = "context"

class TerminalTool:
    """
    Handles the actual execution of Linux commands.
    """
    @staticmethod
    def execute(command: str) -> str:
        try:
            # Using shell=True allows for pipes and redirects common in Bash
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            output = result.stdout if result.stdout else ""
            errors = result.stderr if result.stderr else ""
            
            if result.returncode != 0:
                return f"Error (Exit Code {result.returncode}): {errors}"
            return output if output else "Command executed successfully (no output)."
            
        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 30 seconds."
        except Exception as e:
            return f"Error executing command: {str(e)}"

class OSAgentOrchestrator:
    """
    Manages progressive disclosure of context files.
    """
    def __init__(self, directory: str):
        self.directory = directory
        self.registry: Dict[str, Dict] = {}
        self._initialize_registry()

    def _initialize_registry(self):
        if not os.path.exists(self.directory):
            print(f"[!] Creating directory '{self.directory}'...")
            os.makedirs(self.directory)
            return

        for filename in os.listdir(self.directory):
            if filename.endswith(".md"):
                path = os.path.join(self.directory, filename)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
                        meta = yaml.safe_load(match.group(1)) if match else {}
                        
                        meta['path'] = path
                        if 'name' not in meta: meta['name'] = filename.split('.')[0]
                        if 'triggers' not in meta: meta['triggers'] = [filename.split('.')[0].lower()]
                        
                        self.registry[meta['name']] = meta
                except Exception as e:
                    print(f"[!] Error parsing {filename}: {e}")

    def get_assertive_context(self, user_input: str) -> str:
        disclosed_text = ""
        input_lower = user_input.lower()
        for name, meta in self.registry.items():
            if any(trigger in input_lower for trigger in meta.get('triggers', [])):
                with open(meta['path'], 'r', encoding='utf-8') as f:
                    body = re.sub(r'^---\s*\n.*?\n---\s*\n', '', f.read(), flags=re.DOTALL)
                    disclosed_text += f"\n### SPECIALIZED CONTEXT: {name.upper()} ###\n{body.strip()}\n"
        return disclosed_text

def chat_with_llama(messages: List[Dict]) -> str:
    """
    Standard interface for llama.cpp chat completions.
    """
    payload = {
        "messages": messages,
        "temperature": 0.1,
        "stream": False
    }
    try:
        response = requests.post(API_URL, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"Error: {str(e)}"

def run_interactive_session():
    orchestrator = OSAgentOrchestrator(CONTEXT_DIR)
    terminal = TerminalTool()
    
    # Assertive system prompt including the Tool-Use contract
    base_system = (
        "You are a Linux Specialist Agent. You have the ability to run bash commands. "
        "To run a command, use the format: [[EXEC: your_command_here]]. "
        "After you receive the output of a command, interpret it for the user. "
        "Strictly follow the 'ASSERTIVE CONTEXT' provided for logic and safety rules."
    )

    print("\n--- OS-AGENT INTERACTIVE TERMINAL READY ---")
    
    while True:
        user_input = input("\nUser> ")
        if user_input.lower() in ['exit', 'quit', 'q']:
            break

        # 1. Progressive Disclosure
        context = orchestrator.get_assertive_context(user_input)
        full_system = f"{base_system}\n\n{context}" if context else base_system
        
        # Initialize message chain
        messages = [
            {"role": "system", "content": full_system},
            {"role": "user", "content": user_input}
        ]

        # 2. Agentic Loop (allows for command execution -> feedback -> final answer)
        while True:
            print("AI is thinking...")
            response = chat_with_llama(messages)
            
            # Check for command execution tags: [[EXEC: command]]
            match = re.search(r'\[\[EXEC:\s*(.*?)\s*\]\]', response)
            
            if match:
                cmd = match.group(1)
                print(f"\n[?] AI wants to run: {cmd}")
                confirm = input("Confirm execution? (y/n): ")
                
                if confirm.lower() == 'y':
                    result = terminal.execute(cmd)
                    print(f"[*] Output: {result}")
                    
                    # Feed the result back into the conversation
                    messages.append({"role": "assistant", "content": response})
                    messages.append({"role": "user", "content": f"COMMAND OUTPUT:\n{result}"})
                    # Continue the loop to let the AI see the result
                    continue
                else:
                    messages.append({"role": "user", "content": "System: User denied command execution."})
                    continue
            else:
                # No more commands, print final response and break loop
                print(f"\nAssistant: {response}")
                break

if __name__ == "__main__":
    run_interactive_session()