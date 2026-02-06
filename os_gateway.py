# os_gateway.py

import json
import subprocess
import urllib.request
import os
import sys

# --- Configuration ---
API_URL = "http://localhost:8080/v1/chat/completions"

# Improved Prompt: Encourages the AI to summarize findings for the human
SYSTEM_PROMPT = """You are an OS Agent. You have access to the user's computer.
To run a command, you MUST use the following format:
RUN_COMMAND: ["command", "arg1", "arg2"]

After a command runs, I will give you the output. You should:
1. Analyze the output.
2. If you need more info, run another command.
3. If you have the answer, explain it to the user and start with 'FINISH:'."""

def call_llama(messages):
    """Sends a request to the llama.cpp server."""
    payload = {
        "messages": messages,
        "temperature": 0.1, 
        "stream": False
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(API_URL, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as response:
            res_body = json.loads(response.read().decode('utf-8'))
            return res_body['choices'][0]['message']['content']
    except Exception as e:
        print(f"\n[!] Error connecting to llama.cpp: {e}")
        sys.exit(1)

def execute_os_command(cmd_list):
    """Runs a system command and returns results."""
    # This remains the core execution logic inspired by the host-exec architecture
    try:
        process = subprocess.run(
            cmd_list,
            capture_output=True,
            text=True,
            timeout=60
        )
        return {
            "code": process.returncode,
            "stdout": process.stdout,
            "stderr": process.stderr
        }
    except Exception as e:
        return {"code": -1, "stdout": "", "stderr": str(e)}

def main():
    print("--- Llama OS Bridge Active ---")
    
    user_goal = input("\nWhat should the OS Agent do?: ")
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_goal}
    ]
    
    while True:
        # 1. AI decides what to do
        print("\n[Thinking...]", end="", flush=True)
        ai_response = call_llama(messages)
        messages.append({"role": "assistant", "content": ai_response})
        
        print(f"\n[OS Agent]: {ai_response}")

        if ai_response.startswith("FINISH:"):
            break

        # 2. Extract and execute command
        if "RUN_COMMAND:" in ai_response:
            try:
                # Clean up the string to find the JSON list
                raw_json = ai_response.split("RUN_COMMAND:")[1].strip().split("\n")[0]
                cmd_list = json.loads(raw_json)
                
                print(f"[Executing]: {' '.join(cmd_list)}")
                
                # 3. RUN AND PRINT (The missing step)
                result = execute_os_command(cmd_list)
                
                # We print it here so YOU can see it
                if result['stdout']:
                    print(f"--- STDOUT ---\n{result['stdout']}")
                if result['stderr']:
                    print(f"--- STDERR ---\n{result['stderr']}")
                
                # 4. Feed back to AI
                result_str = f"Exit Code: {result['code']}\nSTDOUT: {result['stdout']}\nSTDERR: {result['stderr']}"
                messages.append({"role": "user", "content": f"COMMAND RESULT:\n{result_str}"})
                
            except Exception as e:
                msg = f"Error: Could not parse or run command. {e}"
                print(f"[!] {msg}")
                messages.append({"role": "user", "content": msg})
        else:
            messages.append({"role": "user", "content": "I didn't see a command. If you are done, say FINISH:. Otherwise, provide a RUN_COMMAND."})

if __name__ == "__main__":
    main()