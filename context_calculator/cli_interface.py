"""
Command-line interface for progressive disclosure OS Agent engine config.
Provides interactive chat and management commands.
"""

import sys
from typing import Optional, Dict
from personality_engine import PersonalityEngine
from colorama import init, Fore, Style
import json


# Initialize colorama for cross-platform colored output
init(autoreset=True)


class CLIInterface:
    """Command-line interface for interacting with the OS Agent engine config."""
    
    def __init__(self, engine: PersonalityEngine):
        """
        Initialize the CLI interface.
        
        Args:
            engine: OSAgent instance
        """
        self.engine = engine
        self.running = True
        self.verbose = False
    
    def run(self):
        """Start the interactive CLI session."""
        self.print_welcome()
        
        while self.running:
            try:
                user_input = input(f"\n{Fore.CYAN}You: {Style.RESET_ALL}").strip()
                
                if not user_input:
                    continue
                
                # Check for commands
                if user_input.startswith('/'):
                    self.handle_command(user_input)
                else:
                    self.handle_query(user_input)
                    
            except KeyboardInterrupt:
                print("\n\nInterrupted by user.")
                self.running = False
            except EOFError:
                print("\n\nEnd of input.")
                self.running = False
        
        self.print_goodbye()
    
    def print_welcome(self):
        """Print welcome message."""
        print(f"\n{Fore.GREEN}{'=' * 60}")
        print(f"{Fore.GREEN}Welcome to the OS Agent engine config system!")
        print(f"{Fore.GREEN}{'=' * 60}{Style.RESET_ALL}")
        print("\nType your messages to interact with the OS Agent.")
        print("Commands:")
        print("  /status    - Show current context status")
        print("  /load <context> - Manually load a context")
        print("  /unload <context> - Unload a context")
        print("  /reset     - Reset all contexts except identity")
        print("  /verbose   - Toggle verbose mode")
        print("  /contexts  - List all available contexts")
        print("  /help      - Show this help message")
        print("  /quit      - Exit the program")
        print()
    
    def print_goodbye(self):
        """Print goodbye message."""
        print(f"\n{Fore.YELLOW}Thank you for using the OS Agent engine config system!")
        print(f"Goodbye!{Style.RESET_ALL}\n")
    
    def handle_command(self, command: str):
        """
        Handle system commands.
        
        Args:
            command: Command string starting with /
        """
        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        if cmd == '/quit' or cmd == '/exit':
            self.running = False
        
        elif cmd == '/status':
            self.show_status()
        
        elif cmd == '/load':
            if args:
                self.load_context_command(args[0])
            else:
                print(f"{Fore.RED}Usage: /load <context_name>{Style.RESET_ALL}")
        
        elif cmd == '/unload':
            if args:
                self.unload_context_command(args[0])
            else:
                print(f"{Fore.RED}Usage: /unload <context_name>{Style.RESET_ALL}")
        
        elif cmd == '/reset':
            self.reset_context_command()
        
        elif cmd == '/verbose':
            self.verbose = not self.verbose
            status = "enabled" if self.verbose else "disabled"
            print(f"{Fore.YELLOW}Verbose mode {status}{Style.RESET_ALL}")
        
        elif cmd == '/contexts':
            self.list_contexts()
        
        elif cmd == '/help':
            self.print_welcome()
        
        else:
            print(f"{Fore.RED}Unknown command: {cmd}{Style.RESET_ALL}")
            print("Type /help for available commands.")
    
    def handle_query(self, query: str):
        """
        Handle a user query.
        
        Args:
            query: User's input query
        """
        # Process the query
        result = self.engine.process_query(query)
        
        # Show verbose information if enabled
        if self.verbose:
            self.print_processing_info(result)
        
        # Show what contexts were loaded this turn
        if result['loaded_contexts']:
            print(f"\n{Fore.YELLOW}[Context loaded: {', '.join(result['loaded_contexts'])}]{Style.RESET_ALL}")
        
        # Display the active context (simulated AI response)
        print(f"\n{Fore.GREEN}AI: {Style.RESET_ALL}", end="")
        print(f"Processing with {len(result['analysis']['relevant_contexts'])} relevant context(s).")
        print(f"{Fore.GREEN}Active contexts: {Style.RESET_ALL}{', '.join(self.engine.state.loaded_contexts)}")
        
        # Show token usage
        usage_percent = (result['token_usage'] / result['state'].turn_count) if result['state'].turn_count > 0 else 0
        print(f"{Fore.CYAN}[Token usage: {result['token_usage']}/{self.engine.token_budget} " +
              f"({(result['token_usage']/self.engine.token_budget)*100:.1f}%)]{Style.RESET_ALL}")
    
    def print_processing_info(self, result: Dict):
        """
        Print detailed processing information (verbose mode).
        
        Args:
            result: Processing result from engine
        """
        print(f"\n{Fore.MAGENTA}{'=' * 60}")
        print("PROCESSING DETAILS")
        print(f"{'=' * 60}{Style.RESET_ALL}")
        
        analysis = result['analysis']
        
        print(f"\n{Fore.CYAN}Query Analysis:{Style.RESET_ALL}")
        print(f"  Relevant contexts: {', '.join(analysis['relevant_contexts']) or 'None'}")
        
        if analysis['confidence_scores']:
            print(f"\n  Confidence scores:")
            for ctx, score in analysis['confidence_scores'].items():
                print(f"    {ctx}: {score:.2f}")
        
        if analysis['emotional_indicators']:
            print(f"\n  Emotional content detected")
        
        if analysis['required_tools']:
            print(f"  Tool usage indicated")
        
        print(f"\n{Fore.CYAN}Context State:{Style.RESET_ALL}")
        print(f"  Loaded: {', '.join(result['state'].loaded_contexts)}")
        print(f"  Tokens: {result['token_usage']}/{self.engine.token_budget}")
        print(f"  Budget remaining: {result['budget_remaining']} tokens")
        print(f"\n{Fore.MAGENTA}{'=' * 60}{Style.RESET_ALL}\n")
    
    def show_status(self):
        """Display current engine status."""
        status = self.engine.get_status()
        
        print(f"\n{Fore.CYAN}{'=' * 60}")
        print("SYSTEM STATUS")
        print(f"{'=' * 60}{Style.RESET_ALL}")
        
        print(f"\n{Fore.GREEN}Conversation:{Style.RESET_ALL}")
        print(f"  Turn count: {status['turn_count']}")
        
        print(f"\n{Fore.GREEN}Token Budget:{Style.RESET_ALL}")
        print(f"  Used: {status['token_usage']}/{status['token_budget']}")
        print(f"  Utilization: {status['budget_utilization']}")
        
        print(f"\n{Fore.GREEN}Loaded Contexts:{Style.RESET_ALL}")
        for ctx in status['loaded_contexts']:
            details = status['context_details'][ctx]
            print(f"  {ctx}: {details['tokens']} tokens (priority: {details['priority']})")
        
        print(f"\n{Fore.GREEN}Available Contexts:{Style.RESET_ALL}")
        for ctx in status['available_contexts']:
            if ctx not in status['loaded_contexts']:
                details = status['context_details'][ctx]
                print(f"  {ctx}: {details['tokens']} tokens (priority: {details['priority']})")
        
        print(f"\n{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
    
    def load_context_command(self, context_name: str):
        """
        Manually load a context.
        
        Args:
            context_name: Name of context to load
        """
        if self.engine.load_context(context_name):
            print(f"{Fore.GREEN}Context '{context_name}' loaded successfully.{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Failed to load context '{context_name}'.{Style.RESET_ALL}")
            print("It may not exist or there may be insufficient token budget.")
    
    def unload_context_command(self, context_name: str):
        """
        Manually unload a context.
        
        Args:
            context_name: Name of context to unload
        """
        if context_name == 'identity':
            print(f"{Fore.RED}Cannot unload core identity context.{Style.RESET_ALL}")
            return
        
        self.engine.unload_context(context_name)
        print(f"{Fore.GREEN}Context '{context_name}' unloaded.{Style.RESET_ALL}")
    
    def reset_context_command(self):
        """Reset all contexts except identity."""
        self.engine.reset_context()
        print(f"{Fore.GREEN}All contexts reset (except identity).{Style.RESET_ALL}")
    
    def list_contexts(self):
        """List all available contexts."""
        status = self.engine.get_status()
        
        print(f"\n{Fore.CYAN}Available Contexts:{Style.RESET_ALL}")
        print(f"{'Name':<15} {'Priority':<10} {'Tokens':<10} {'Status'}")
        print("-" * 50)
        
        for name, details in sorted(
            status['context_details'].items(),
            key=lambda x: x[1]['priority']
        ):
            status_str = f"{Fore.GREEN}LOADED{Style.RESET_ALL}" if details['loaded'] else "Available"
            print(f"{name:<15} {details['priority']:<10} {details['tokens']:<10} {status_str}")