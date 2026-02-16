import os
import re
import json
import requests
import subprocess
import sys
from datetime import datetime
from typing import List, Dict, Optional

# --- CONFIGURATION ---
API_URL = "http://localhost:1234/v1/chat/completions"
MODEL_TEMPERATURE = 0.1
MODEL_AUTOMATION = False 
LOG_DIR = "logs"

# --- EMBEDDED KNOWLEDGE BASE ---
KNOWLEDGE_BASE = {
    "BashScriptMaster": {
        "description": "Advanced shell scripting best practices and automation logic.",
        "triggers": ["bash", "shell", "script", "loop", "variable", "pipe", "sed", "awk", "grep", "automation"],
        "content": """
### SPECIALIZED CONTEXT: PROFESSIONAL BASH SCRIPTING ###
- **Strict Mode:** Every script suggested must start with `set -euo pipefail`.
- **Portability:** Use `#!/usr/bin/env bash`.
- **Syntax:** Use `[[ ]]` for tests and `$(...)` for command substitution. Quote all variables.
- **Functionality:** Group logic into functions using `local` variables.
- **Performance:** Prefer `awk` or `sed` for large file processing.
"""
    }
}

# --- LOGGING SYSTEM ---

class SessionLogger:
    """
    Handles file-based logging for all agent communications.
    """
    def __init__(self, directory: str):
        self.directory = directory
        self._ensure_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(self.directory, f"session_{timestamp}.log")

    def _ensure_dir(self):
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

    def log(self, sender: str, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {sender.upper()}:\n{message}\n{'-'*40}\n"
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)

# --- TOOLS ---

class TerminalTool:
    @staticmethod
    def execute(command: str) -> str:
        if any(x in command for x in ["rm -rf /", ":(){ :|:& };:"]):
            return "Error: High-risk command blocked by safety filter."
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=30
            )
            output = result.stdout if result.stdout else ""
            errors = result.stderr if result.stderr else ""
            if result.returncode != 0:
                return f"Execution Error (Exit Code {result.returncode}):\n{errors}"
            return output if output.strip() else f"Success (no output). Stderr: {errors}"
        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 30 seconds."
        except Exception as e:
            return f"Error executing command: {str(e)}"

# --- AGENT CORE ---

class ContextManager:
    @staticmethod
    def get_relevant_context(user_input: str) -> str:
        disclosed_text = ""
        input_lower = user_input.lower()
        for name, data in KNOWLEDGE_BASE.items():
            if any(trigger in input_lower for trigger in data.get('triggers', [])):
                disclosed_text += f"\n{data['content']}\n"
        return disclosed_text

class AgentLLM:
    @staticmethod
    def chat(messages: List[Dict]) -> str:
        payload = {"messages": messages, "temperature": MODEL_TEMPERATURE, "stream": False, "stop": ["User>", "System:"]}
        try:
            response = requests.post(API_URL, json=payload, timeout=120)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            return f"Error: {str(e)}"

# --- ORCHESTRATOR ---

def run_agentic_session():
    terminal = TerminalTool()
    logger = SessionLogger(LOG_DIR)
    
    base_system_prompt = (
        "You are an Advanced Linux Automation Agent. You have access to a local terminal.\n\n"
        "**TOOL USE:** To execute a command, use: [[EXEC: <command>]]\n\n"
        "**RULES:** Stop after calling EXEC. Analyze output before final response."
    )

    print(f"\n--- AGENTIC TERMINAL READY (Logging to {LOG_DIR}/) ---")
    history = []

    while True:
        try:
            user_input = input("\nUser> ")
        except KeyboardInterrupt:
            break

        if user_input.lower() in ['exit', 'quit', 'q']:
            logger.log("SYSTEM", "User terminated session.")
            break

        logger.log("USER", user_input)
        
        specialized_context = ContextManager.get_relevant_context(user_input)
        current_system_message = base_system_prompt
        if specialized_context:
            current_system_message += f"\n\n--- ACTIVE KNOWLEDGE ---\n{specialized_context}"

        messages = [{"role": "system", "content": current_system_message}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_input})
        history.append({"role": "user", "content": user_input})

        while True:
            print("Agent thinking...", end="\r")
            response = AgentLLM.chat(messages)
            print(f"\rAgent: {response}\n")
            
            logger.log("AGENT", response)
            history.append({"role": "assistant", "content": response})
            messages.append({"role": "assistant", "content": response})

            match = re.search(r'\[\[EXEC:\s*(.*?)\s*\]\]', response, re.DOTALL)
            if match:
                cmd = match.group(1).strip()
                print(f"\n[?] Agent requests execution: \033[93m{cmd}\033[0m")
                
                if MODEL_AUTOMATION:
                    confirm = 'y'
                else:
                    confirm = input("[y/n] > ").lower()
                
                if confirm == 'y':
                    logger.log("SYSTEM", f"Executing Command: {cmd}")
                    execution_result = terminal.execute(cmd)
                    logger.log("TERMINAL_OUTPUT", execution_result)
                    print(f"[*] Output:\n{execution_result}")
                else:
                    execution_result = "User denied execution."
                    logger.log("SYSTEM", "User denied command execution.")
                    print("[!] Execution denied.")

                messages.append({"role": "user", "content": f"COMMAND OUTPUT:\n{execution_result}"})
                continue 
            else:
                break

if __name__ == "__main__":
    run_agentic_session()