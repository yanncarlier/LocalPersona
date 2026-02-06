#!/usr/bin/env python3
"""
AI Personality System with Progressive Disclosure
Main entry point for the personality engine.
"""

import sys
from pathlib import Path
from personality_engine import PersonalityEngine
from cli_interface import CLIInterface


def main():
    """Main entry point for the AI personality system."""
    print("=" * 60)
    print("AI Personality System with Progressive Disclosure")
    print("=" * 60)
    print()
    
    # Initialize the personality engine
    config_dir = Path("../context_files")
    
    if not config_dir.exists():
        print(f"Error: Configuration directory '{config_dir}' not found.")
        print("Please create the directory and add the required files:")
        print("  - AGENT.md")
        print("  - IDENTITY.md")
        print("  - TOOLS.md")
        print("  - SOUL.md")
        print("  - HEARTBEAT.md")
        sys.exit(1)
    
    try:
        # Create personality engine
        engine = PersonalityEngine(config_dir)
        
        # Initialize CLI interface
        cli = CLIInterface(engine)
        
        # Start the interactive session
        cli.run()
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure all required configuration files exist.")
        sys.exit(1)
    except Exception as e:
        print(f"Error initializing personality engine: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()