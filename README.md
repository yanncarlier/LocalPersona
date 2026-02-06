# OSAgent

An AI OS Agent system with progressive context disclosure. This project implements a conversational AI assistant that intelligently manages context loading based on user interactions, emotional content detection, and token budget constraints.

## Overview

LocalPersonais designed to simulate a sophisticated AI assistant with:

- **Progressive Disclosure**: Dynamically loads OS Agent layers (identity, values, tools, emotional awareness) as needed during conversation
- **Token Budget Management**: Intelligently manages context within a configurable token budget (default: 8000 tokens)
- **Emotional Intelligence**: Detects emotional indicators in user messages and adapts responses accordingly
- **Modular Architecture**: Separates concerns into OS Agent engine, CLI interface, and configuration files

## Features

### Core Components

- **OS AgentEngine**: Manages context layers, token budgeting, and progressive disclosure
- **CLIInterface**: Interactive command-line interface with commands for status, context management, and configuration
- **Configuration System**: Markdown-based OS Agent files for identity, agent behavior, tools, soul/values, and emotional awareness

### Key Capabilities

- **Context Analysis**: Parses user queries to identify relevant OS Agent layers
- **Smart Loading**: Automatically loads contexts based on relevance scores and keyword matching
- **Token Optimization**: Unloads lower-priority contexts when budget is exceeded
- **Conversation State Tracking**: Maintains turn count, discussed topics, tools used, and emotional state
- **Interactive Management**: Commands to manually load/unload contexts, view status, and reset state

## Project Structure

```
OSAgent/
├── main.py                    # Main entry point
├── OS Agent_engine.py      # Core engine with progressive disclosure logic
├── cli_interface.py           # Interactive CLI interface
├── requirements.txt           # Python dependencies
├── config/
│   ├── AGENT.md              # Behavioral guidelines and response style
│   ├── IDENTITY.md           # Core identity and attributes
│   ├── TOOLS.md              # Available capabilities and tools
│   ├── SOUL.md               # Values, ethics, and emotional principles
│   └── HEARTBEAT.md          # Emotional monitoring and detection
├── SOUL.md                    # Detailed emotional intelligence documentation
└── README.md                  # This file
```

## Installation

### Prerequisites

- Python 3.7+
- `pip` or `uv` package manager

### Setup Steps

#### Option 1: Using `uv` (Recommended)

```bash
gir clone git@github.com:yanncarlier/OSAgent.git
cd OSAgent Agent

# Initialize and activate virtual environment
uv venv

# Activate the virtual environment
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
```

#### Option 2: Using `pip`

```bash
cd OSAgent

# Create virtual environment
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Application

After installation and activation of the virtual environment:

```bash
python main.py
```

Or directly with the venv Python:

```bash
./.venv/bin/python main.py
```

## Usage

### Interactive Commands

Once the application starts, you can interact with it using natural language queries or system commands:

#### Chat Commands

Simply type any message to query the AI:

```
You: What can you do?
OSAgent: Processing with X relevant context(s)...
```

#### System Commands

- **`/status`** - Display current engine status, token usage, and loaded contexts
- **`/load <context>`** - Manually load a specific context (e.g., `/load tools`)
- **`/unload <context>`** - Unload a context to free token budget
- **`/reset`** - Reset all contexts except core identity
- **`/verbose`** - Toggle verbose mode for detailed processing information
- **`/contexts`** - List all available contexts with their status
- **`/help`** - Display available commands
- **`/quit` or `/exit`** - Exit the application

### Using the /load Command

The `/load` command allows you to manually load OS Agent contexts when you need specific capabilities or information, regardless of automatic context detection.

#### Command Syntax

```
/load <context_name>
```

Where `<context_name>` is one of: `agent`, `identity`, `tools`, `soul`, or `heartbeat`

#### Available Contexts to Load

| Context | Priority | Use When | Example |
|---------|----------|----------|---------|
| `agent` | 2 | You want behavior guidelines or interaction rules | `/load agent` |
| `soul` | 3 | You want to understand values and ethics | `/load soul` |
| `tools` | 4 | You need information about capabilities | `/load tools` |
| `heartbeat` | 5 | You want emotional awareness features active | `/load heartbeat` |
| `identity` | 1 | N/A - Always loaded automatically | (Cannot manually load) |

#### Practical Examples

**Example 1: Loading the tools context**
```
You: /load tools
Context 'tools' loaded successfully.

You: What tools are available?
AI: Processing with 1 relevant context(s)...
Active contexts: identity, tools
[Token usage: 765/8000 (9.6%)]
```
*Use Case*: When you want to know what capabilities the AI has available.

**Example 2: Loading the soul context for values discussion**
```
You: /load soul
Context 'soul' loaded successfully.

You: Tell me about your values
[Context loaded: soul]
AI: Processing with 1 relevant context(s)...
Active contexts: identity, soul
[Token usage: 2145/8000 (26.8%)]
```
*Use Case*: When discussing ethics, principles, or what the AI believes in.

**Example 3: Loading emotional awareness**
```
You: /load heartbeat
Context 'heartbeat' loaded successfully.

You: I'm feeling overwhelmed with this task
AI: Processing with 1 relevant context(s)...
Active contexts: identity, heartbeat
[Token usage: 895/8000 (11.2%)]
```
*Use Case*: When you want the AI to be more emotionally attuned to your needs.

**Example 4: Loading behavior guidelines**
```
You: /load agent
Context 'agent' loaded successfully.

You: What are your behavioral guidelines?
AI: Processing with 1 relevant context(s)...
Active contexts: identity, agent
[Token usage: 1340/8000 (16.8%)]
```
*Use Case*: When you want to understand how the AI will behave and interact with you.

#### Why Manually Load Contexts?

1. **Token Budget Control**: Manually loading lets you be strategic about token usage
2. **Specific Needs**: Load exactly what you need when you know what you're asking about
3. **Experimentation**: Test how the AI responds with different context combinations
4. **Override Automatic Selection**: Sometimes the automatic detector might not pick the context you want

#### Load vs. Automatic Loading

The `/load` command differs from automatic context loading:

- **Automatic**: Engine analyzes your query and loads relevant contexts automatically
- **Manual (`/load`)**: You explicitly request a context regardless of query content

**Scenario: Checking token usage**

```
You: /status
============================================================
SYSTEM STATUS
============================================================
Token Budget:
  Used: 450/8000
  Utilization: 5.6%

Available Contexts:
  agent: 890 tokens (priority: 2)
  heartbeat: 520 tokens (priority: 5)
  tools: 310 tokens (priority: 4)
  soul: 1695 tokens (priority: 3)

============================================================

You: /load soul
Context 'soul' loaded successfully.

You: /status
============================================================
SYSTEM STATUS
============================================================
Token Budget:
  Used: 2145/8000
  Utilization: 26.8%

Loaded Contexts:
  identity: 450 tokens (priority: 1)
  soul: 1695 tokens (priority: 3)

============================================================
```

#### Error Cases

**Trying to load a context that doesn't exist:**
```
You: /load creativity
Failed to load context 'creativity'.
It may not exist or there may be insufficient token budget.
```

**Trying to load when token budget is full:**
```
You: /load tools
Failed to load context 'tools'.
It may not exist or there may be insufficient token budget.

You: /reset
All contexts reset (except identity).

You: /load tools
Context 'tools' loaded successfully.
```

#### Best Practices

1. **Check status before loading**: Use `/status` to see available budget
2. **Load strategically**: Load only contexts you actually need
3. **Use `/unload`**: Free up space before loading new contexts if budget is tight
4. **Combine with `/verbose`**: Use `/verbose` to see detailed load information
5. **Reset when needed**: Use `/reset` to clear contexts and start fresh

### Example Session

```
============================================================
AI OS Agent System with Progressive Disclosure
============================================================

Welcome to the AI OS Agent System!
============================================================

Type your messages to interact with the AI.
Commands:
  /status    - Show current context status
  /load <context> - Manually load a context
  /unload <context> - Unload a context
  /reset     - Reset all contexts except identity
  /verbose   - Toggle verbose mode
  /contexts  - List all available contexts
  /help      - Show this help message
  /quit      - Exit the program

You: Tell me about your values
[Context loaded: soul]
AI: Processing with 1 relevant context(s)...
Active contexts: identity, soul
[Token usage: 2145/8000 (26.8%)]

You: /status
============================================================
SYSTEM STATUS
============================================================

Conversation:
  Turn count: 1

Token Budget:
  Used: 2145/8000
  Utilization: 26.8%

Loaded Contexts:
  identity: 450 tokens (priority: 1)
  soul: 1695 tokens (priority: 3)

Available Contexts:
  agent: 890 tokens (priority: 2)
  heartbeat: 520 tokens (priority: 5)
  tools: 310 tokens (priority: 4)

============================================================
```

## Configuration Files

### IDENTITY.md      → Who the AI is (OS Agent, empathy, behavior)
Defines the core identity and name of the AI. Always loaded. Contains essential information about who the AI is.
- **Priority**: 1 (Highest)
- **Status**: Always active

### AGENT.md         → What the AI does (capabilities, tasks, functions)
Behavioral guidelines and response style. Loaded when behavior-related queries are detected.
- **Priority**: 2
- **Keywords**: behavior, response, interaction, guidelines

### SOUL.md          → Why the AI exists (vision, principles, values)
Values, ethics, and principles. Loaded when emotional or value-related queries are detected.
- **Priority**: 3
- **Keywords**: values, ethics, beliefs, principles, philosophy

### TOOLS.md         → How the AI works (technical tools, methods)
Available capabilities and tools reference. Loaded when tool-related actions are requested.
- **Priority**: 4
- **Keywords**: tool, function, capability, can, execute

### HEARTBEAT.md     → Current state (status, recent changes, focus)
Emotional monitoring and detection. Loaded when emotional content is detected in user messages.
- **Priority**: 5
- **Keywords**: emotion, feel, empathy, mood, emotional

## Architecture

### Progressive Disclosure System

The engine implements progressive context loading based on:

1. **Keyword Matching**: Analyzes user queries against context keywords
2. **Relevance Scoring**: Calculates confidence scores for each context
3. **Priority-Based Loading**: Loads contexts ordered by relevance and priority
4. **Token Budget**: Manages memory constraints by unloading lower-priority contexts when needed
5. **Emotional Detection**: Special handling for emotionally-charged queries

### Token Budget Management

- Default budget: 8000 tokens
- Each context has an estimated token count (roughly 1 token per 4 characters)
- When budget is exceeded, lower-priority loaded contexts are unloaded to make room
- Core identity context is never unloaded

### Conversation State Tracking

The system maintains:
- Turn count for conversation length
- Topics discussed (populated by user queries)
- Tools used during conversation
- Loaded contexts (active OS Agent layers)
- User preferences (extensible)
- Emotional state (updated by analysis)

## Dependencies

- **colorama** (>=0.4.6): Cross-platform colored terminal output

See `requirements.txt` for the complete dependency list.

## Development

### Project Layout

- `main.py`: Entry point that initializes the engine and CLI
- `OS Agent_engine.py`: Core logic for context management and progressive disclosure
- `cli_interface.py`: User interface and command handling
- `config/`: Markdown-based OS Agent configuration

### Extending the System

To add new OS Agent layers:

1. Create a new markdown file in `config/` (e.g., `CREATIVITY.md`)
2. Update `OS Agent_engine.py` `_load_OS Agent_files()` method to include it
3. Assign appropriate priority and keywords
4. Define behavior in the CLI if needed

## Understanding the OS Agent Layers

### Why Progressive Disclosure?

Loading all OS Agent context at once would exceed token budgets in real deployments (with LLMs). Progressive disclosure:
- Loads context only when relevant
- Prioritizes core identity (always loaded)
- Optimizes token usage for efficiency
- Allows the system to handle constraints gracefully

### How Contexts Are Selected

When you send a query:

1. The engine extracts keywords from your message
2. Each context is scored based on keyword matches
3. Contexts are ranked by relevance and priority
4. Top contexts are loaded if token budget allows
5. If budget is exceeded, lower-priority contexts are unloaded

### Example Flow

```
User Query: "I'm feeling frustrated, can you help?"
  ↓
Keyword Extraction: {frustrated, feeling, help, can}
  ↓
Context Scoring:
  - heartbeat: 2 keyword matches → load (emotion detected)
  - tools: 2 keyword matches → load (help/can = capability)
  - soul: 0 matches → wait
  - agent: 1 match → wait
  ↓
Load heartbeat (priority 5) and tools (priority 4)
Active contexts: identity, heartbeat, tools
```

## Future Enhancements

- Integration with language models (OpenAI, Claude, etc.)
- Persistent conversation history and learning
- User preference customization
- Advanced emotional state modeling
- Multi-user support
- Web-based interface
- Context prioritization based on conversation history
- Performance metrics and analytics

## Troubleshooting

### ModuleNotFoundError: No module named 'colorama'

Ensure dependencies are installed:
```bash
pip install -r requirements.txt
```

### Config directory not found

The application expects a `config/` directory in the project root with the required markdown files. Ensure all files exist:
- `config/AGENT.md`
- `config/IDENTITY.md`
- `config/TOOLS.md`
- `config/SOUL.md`
- `config/HEARTBEAT.md`

### Low Token Budget Errors

If contexts aren't loading, the token budget may be exhausted. Use `/reset` to clear non-essential contexts or `/verbose` to see detailed information.



## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## Support

For issues or questions, please open an issue in the project repository.



