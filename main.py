import os
import re
import json
import requests
import subprocess
import sys
from typing import List, Dict, Optional

# --- CONFIGURATION ---
# Point this to your local LLM (e.g., LM Studio, Ollama, Llama.cpp)
API_URL = "http://localhost:8080/v1/chat/completions"
MODEL_TEMPERATURE = 0.1

# --- EMBEDDED KNOWLEDGE BASE (Originally bash_pro.md) ---
# This dictionary replaces the external file loading mechanism.
# It acts as the agent's long-term memory for specific domains.
KNOWLEDGE_BASE = {
    "BashScriptMaster": {
        "description": "Advanced shell scripting best practices and automation logic.",
        "triggers": ["bash", "shell", "script", "loop", "variable", "pipe", "sed", "awk", "grep", "automation"],
        "content": """
### SPECIALIZED CONTEXT: PROFESSIONAL BASH SCRIPTING ###

# ASSERTIVE CONTEXT: PROFESSIONAL BASH SCRIPTING
- **Strict Mode:** Every script suggested must start with `set -euo pipefail` to ensure immediate failure on errors or undefined variables.
- **Portability:** Use `#!/usr/bin/env bash` for the shebang to ensure the script finds the bash binary in the user's PATH.
- **Syntax:** - Always use `[[ ]]` for tests instead of `[ ]`.
  - Prefer `$(...)` over backticks for command substitution.
  - Quote all variables (e.g., `"$VAR"`) to prevent word splitting and globbing.
- **Functionality:** Group logic into functions. Use `local` for all function-scoped variables to avoid namespace pollution.
- **Performance:** For large file processing, prefer `awk` or `sed` over pure bash loops to maintain efficiency.
"""
    }
}

# --- TOOLS ---

class TerminalTool:
    """
    Handles the actual execution of Linux commands.
    """
    @staticmethod
    def execute(command: str) -> str:
        # Security: Simple prompt to prevent accidental high-risk commands
        if any(x in command for x in ["rm -rf /", ":(){ :|:& };:"]):
            return "Error: High-risk command blocked by safety filter."

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
                return f"Execution Error (Exit Code {result.returncode}):\n{errors}"
            
            # If successful but no output (common for file operations)
            return output if output.strip() else f"Command executed successfully (no output). Stderr: {errors}"
            
        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 30 seconds."
        except Exception as e:
            return f"Error executing command: {str(e)}"

# --- AGENT CORE ---

class ContextManager:
    """
    Analyzes user input to inject specialized knowledge (RAG-lite).
    """
    @staticmethod
    def get_relevant_context(user_input: str) -> str:
        disclosed_text = ""
        input_lower = user_input.lower()
        
        # Check our embedded knowledge base for triggers
        for name, data in KNOWLEDGE_BASE.items():
            if any(trigger in input_lower for trigger in data.get('triggers', [])):
                disclosed_text += f"\n{data['content']}\n"
        
        return disclosed_text

class AgentLLM:
    """
    Handles communication with the Llama/Ollama API.
    """
    @staticmethod
    def chat(messages: List[Dict]) -> str:
        payload = {
            "messages": messages,
            "temperature": MODEL_TEMPERATURE,
            "stream": False,
            # Ensure the model knows when to stop generating
            "stop": ["User>", "System:"] 
        }
        try:
            response = requests.post(API_URL, json=payload, timeout=120)
            response.raise_for_status()
            content = response.json()['choices'][0]['message']['content']
            return content
        except requests.exceptions.ConnectionError:
            return "Error: Could not connect to LLM. Is it running on localhost:8080?"
        except Exception as e:
            return f"Error: {str(e)}"

# --- ORCHESTRATOR ---

def run_agentic_session():
    terminal = TerminalTool()
    
    # Base System Prompt: Defines the persona and tool usage syntax
    base_system_prompt = (
        "You are an Advanced Linux Automation Agent. "
        "You have access to a local terminal.\n\n"
        "**TOOL USE:**\n"
        "To execute a command, you MUST use this exact format:\n"
        "[[EXEC: <command>]]\n\n"
        "**RULES:**\n"
        "1. When you execute a command, stop generating text immediately. Wait for the user to provide the Output.\n"
        "2. Analyze the Output before responding to the user.\n"
        "3. If the user asks for a script, strictly follow the specialized context guidelines provided dynamically."
    )

    print("\n--- AGENTIC BASH TERMINAL READY ---")
    print(f"Target API: {API_URL}")
    print("Type 'exit' to quit.\n")
    
    # Conversation History
    history = []

    while True:
        try:
            user_input = input("\nUser> ")
        except KeyboardInterrupt:
            break

        if user_input.lower() in ['exit', 'quit', 'q']:
            print("Shutting down agent.")
            break

        # 1. Context Injection (Retrieval)
        # We perform a lightweight RAG step here to check if we need the Bash Rules
        specialized_context = ContextManager.get_relevant_context(user_input)
        
        # Construct the current system prompt (Base + Retrieved Context)
        current_system_message = base_system_prompt
        if specialized_context:
            current_system_message += f"\n\n--- ACTIVE KNOWLEDGE ---\n{specialized_context}"
            print(" * Knowledge Base 'BashScriptMaster' Active *")

        # Reset history for this turn OR append to existing context if you want long memory
        # Here we rebuild the message chain to ensure the system prompt is fresh
        messages = [{"role": "system", "content": current_system_message}]
        
        # Add conversation history (optional: limit this to last N turns for context window management)
        messages.extend(history)
        
        # Add current user input
        messages.append({"role": "user", "content": user_input})
        
        # Update local history
        history.append({"role": "user", "content": user_input})

        # 2. Agentic Loop (Reasoning -> Action -> Observation)
        while True:
            print("Agent thinking...", end="\r")
            response = AgentLLM.chat(messages)
            print(f"\rAgent: {response}\n") # Print the thought/response
            
            # Store agent response in history
            history.append({"role": "assistant", "content": response})
            messages.append({"role": "assistant", "content": response})

            # Check for Tool Invocation
            # Regex looks for [[EXEC: command ]]
            match = re.search(r'\[\[EXEC:\s*(.*?)\s*\]\]', response, re.DOTALL)
            
            if match:
                cmd = match.group(1).strip()
                
                # Human-in-the-loop confirmation
                print(f"\n[?] Agent requests execution: \033[93m{cmd}\033[0m")
                confirm = input("[y/n] > ").lower()
                
                execution_result = ""
                if confirm == 'y':
                    execution_result = terminal.execute(cmd)
                    print(f"[*] Output:\n{execution_result}")
                else:
                    execution_result = "User denied execution."
                    print("[!] Execution denied.")

                # 3. Observation Feedback
                # We feed the result back to the LLM so it can reflect
                observation_msg = f"COMMAND OUTPUT:\n{execution_result}"
                messages.append({"role": "user", "content": observation_msg})
                # Note: We do not add the raw observation to the 'history' variable displayed to the user 
                # effectively, but we keep it in the 'messages' list for the immediate reasoning loop.
                
                # Loop continues: The AI will now generate a response based on the output
                continue 
            
            else:
                # No execution requested; the agent has finished this turn.
                break

if __name__ == "__main__":
    run_agentic_session()