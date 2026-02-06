"""
Core personality engine implementing progressive disclosure.
Manages context loading and personality state.
"""

from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import re


@dataclass
class ContextLayer:
    """Represents a layer of context that can be progressively disclosed."""
    name: str
    content: str
    priority: int
    tokens_estimate: int
    keywords: Set[str] = field(default_factory=set)
    dependencies: List[str] = field(default_factory=list)
    loaded: bool = False


@dataclass
class ConversationState:
    """Tracks the current state of the conversation."""
    turn_count: int = 0
    topics_discussed: Set[str] = field(default_factory=set)
    tools_used: Set[str] = field(default_factory=set)
    loaded_contexts: Set[str] = field(default_factory=set)
    user_preferences: Dict[str, any] = field(default_factory=dict)
    emotional_state: str = "neutral"


class PersonalityEngine:
    """
    Main engine for managing OS Agent personality with progressive disclosure.
    """
    
    def __init__(self, config_dir: Path):
        """
        Initialize the personality engine.
        
        Args:
            config_dir: Directory containing personality configuration files
        """
        self.config_dir = Path(config_dir)
        self.contexts: Dict[str, ContextLayer] = {}
        self.state = ConversationState()
        self.token_budget = 32768  # Maximum tokens for context
        self.current_token_usage = 0
        
        # Load all personality files
        self._load_personality_files()
        
        # Always load core identity (highest priority)
        self._load_core_context()
    
    def _load_personality_files(self):
        """Load and parse all personality configuration files."""
        files_config = {

            'IDENTITY.md': {
                'priority': 1,  # Highest priority - always loaded
                'keywords': {'name', 'identity', 'core', 'who', 'what'}
            },
            'AGENT.md': {
                'priority': 2,
                'keywords': {'behavior', 'response', 'interaction', 'guidelines'}
            },
            'SOUL.md': {
                'priority': 3,
                'keywords': {'values', 'ethics', 'beliefs', 'principles', 'philosophy'}
            },
            'TOOLS.md': {
                'priority': 4,
                'keywords': {'tool', 'function', 'capability', 'can', 'execute'}
            },            
            'HEARTBEAT.md': {
                'priority': 5,
                'keywords': {'emotion', 'feel', 'empathy', 'mood', 'emotional'}
            },
            'SKILL.md': {
                'priority': 6,
                'keywords': {'skill', 'expertise', 'ability', 'knowledge', 'proficiency'}
            }
        }
        
        for filename, config in files_config.items():
            filepath = self.config_dir / filename
            
            if not filepath.exists():
                raise FileNotFoundError(f"Required file not found: {filepath}")
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Estimate tokens (roughly 4 characters per token)
            tokens_estimate = len(content) // 4
            
            context_name = filename.replace('.md', '').lower()
            
            self.contexts[context_name] = ContextLayer(
                name=context_name,
                content=content,
                priority=config['priority'],
                tokens_estimate=tokens_estimate,
                keywords=config['keywords']
            )
    
    def _load_core_context(self):
        """Load the core identity context (always active)."""
        if 'identity' in self.contexts:
            identity = self.contexts['identity']
            identity.loaded = True
            self.state.loaded_contexts.add('identity')
            self.current_token_usage += identity.tokens_estimate
    
    def analyze_query(self, query: str) -> Dict[str, any]:
        """
        Analyze user query to determine what context is needed.
        
        Args:
            query: User's input query
            
        Returns:
            Analysis results with relevant contexts
        """
        query_lower = query.lower()
        words = set(re.findall(r'\w+', query_lower))
        
        analysis = {
            'query': query,
            'relevant_contexts': [],
            'confidence_scores': {},
            'required_tools': [],
            'emotional_indicators': []
        }
        
        # Check each context for relevance
        for context_name, context in self.contexts.items():
            if context.loaded:
                continue  # Already loaded
            
            # Calculate relevance score
            keyword_matches = len(words.intersection(context.keywords))
            
            if keyword_matches > 0:
                confidence = keyword_matches / len(context.keywords)
                analysis['relevant_contexts'].append(context_name)
                analysis['confidence_scores'][context_name] = confidence
        
        # Sort by confidence and priority
        analysis['relevant_contexts'].sort(
            key=lambda c: (
                analysis['confidence_scores'][c],
                -self.contexts[c].priority
            ),
            reverse=True
        )
        
        # Detect emotional content
        emotional_words = {
            'happy', 'sad', 'angry', 'afraid', 'worried', 'excited',
            'frustrated', 'confused', 'feel', 'feeling', 'emotion'
        }
        if words.intersection(emotional_words):
            analysis['emotional_indicators'].append('emotional_content_detected')
        
        # Detect tool requests
        tool_indicators = {
            'calculate', 'compute', 'search', 'find', 'create',
            'generate', 'analyze', 'process', 'execute'
        }
        if words.intersection(tool_indicators):
            analysis['required_tools'].append('tools_required')
        
        return analysis
    
    def load_context(self, context_name: str, force: bool = False) -> bool:
        """
        Load a specific context if budget allows.
        
        Args:
            context_name: Name of context to load
            force: Force loading even if budget exceeded
            
        Returns:
            True if context was loaded, False otherwise
        """
        if context_name not in self.contexts:
            return False
        
        context = self.contexts[context_name]
        
        if context.loaded:
            return True  # Already loaded
        
        # Check token budget
        new_usage = self.current_token_usage + context.tokens_estimate
        
        if new_usage > self.token_budget and not force:
            # Try to unload lower priority contexts
            if not self._make_room_for_context(context):
                return False
        
        # Load the context
        context.loaded = True
        self.state.loaded_contexts.add(context_name)
        self.current_token_usage += context.tokens_estimate
        
        return True
    
    def _make_room_for_context(self, needed_context: ContextLayer) -> bool:
        """
        Attempt to free up token budget by unloading lower priority contexts.
        
        Args:
            needed_context: Context that needs to be loaded
            
        Returns:
            True if sufficient room was made, False otherwise
        """
        # Find loaded contexts with lower priority
        unloadable = [
            ctx for ctx in self.contexts.values()
            if ctx.loaded and ctx.priority > needed_context.priority
            and ctx.name != 'identity'  # Never unload identity
        ]
        
        # Sort by priority (lowest priority first)
        unloadable.sort(key=lambda c: c.priority, reverse=True)
        
        for context in unloadable:
            self.unload_context(context.name)
            
            # Check if we have enough room now
            new_usage = self.current_token_usage + needed_context.tokens_estimate
            if new_usage <= self.token_budget:
                return True
        
        return False
    
    def unload_context(self, context_name: str):
        """
        Unload a context to free up token budget.
        
        Args:
            context_name: Name of context to unload
        """
        if context_name == 'identity':
            return  # Never unload core identity
        
        if context_name in self.contexts:
            context = self.contexts[context_name]
            if context.loaded:
                context.loaded = False
                self.state.loaded_contexts.discard(context_name)
                self.current_token_usage -= context.tokens_estimate
    
    def get_active_context(self) -> str:
        """
        Get the current active context as a combined string.
        
        Returns:
            Combined context from all loaded layers
        """
        active_contexts = []
        
        # Sort by priority
        loaded = [
            ctx for ctx in self.contexts.values()
            if ctx.loaded
        ]
        loaded.sort(key=lambda c: c.priority)
        
        for context in loaded:
            active_contexts.append(f"=== {context.name.upper()} ===\n")
            active_contexts.append(context.content)
            active_contexts.append("\n\n")
        
        return "".join(active_contexts)
    
    def process_query(self, query: str) -> Dict[str, any]:
        """
        Process a user query with progressive context loading.
        
        Args:
            query: User's input query
            
        Returns:
            Processing result with context and recommendations
        """
        # Increment turn count
        self.state.turn_count += 1
        
        # Analyze the query
        analysis = self.analyze_query(query)
        
        # Load relevant contexts
        loaded_this_turn = []
        for context_name in analysis['relevant_contexts'][:2]:  # Load top 2
            if self.load_context(context_name):
                loaded_this_turn.append(context_name)
        
        # Special handling for emotional content
        if analysis['emotional_indicators'] and 'heartbeat' not in self.state.loaded_contexts:
            if self.load_context('heartbeat'):
                loaded_this_turn.append('heartbeat')
        
        # Special handling for tool requests
        if analysis['required_tools'] and 'tools' not in self.state.loaded_contexts:
            if self.load_context('tools'):
                loaded_this_turn.append('tools')
        
        return {
            'analysis': analysis,
            'loaded_contexts': loaded_this_turn,
            'active_context': self.get_active_context(),
            'token_usage': self.current_token_usage,
            'budget_remaining': self.token_budget - self.current_token_usage,
            'state': self.state
        }
    
    def get_status(self) -> Dict[str, any]:
        """
        Get current engine status.
        
        Returns:
            Status information dictionary
        """
        return {
            'turn_count': self.state.turn_count,
            'loaded_contexts': list(self.state.loaded_contexts),
            'token_usage': self.current_token_usage,
            'token_budget': self.token_budget,
            'budget_utilization': f"{(self.current_token_usage / self.token_budget) * 100:.1f}%",
            'available_contexts': list(self.contexts.keys()),
            'context_details': {
                name: {
                    'loaded': ctx.loaded,
                    'priority': ctx.priority,
                    'tokens': ctx.tokens_estimate
                }
                for name, ctx in self.contexts.items()
            }
        }
    
    def reset_context(self):
        """Reset all context except core identity."""
        for name, context in self.contexts.items():
            if name != 'identity':
                context.loaded = False
        
        self.state = ConversationState()
        self._load_core_context()
    
    def load_all_contexts(self) -> None:
        """Load all available contexts."""
        for context_name in sorted(self.contexts.keys()):
            self.load_context(context_name, force=True)
    
    def print_status(self) -> None:
        """Print current engine status in a formatted way."""
        from colorama import init, Fore, Style
        init(autoreset=True)
        
        status = self.get_status()
        
        print(f"\n{Fore.CYAN}Conversation:{Style.RESET_ALL}")
        print(f"  Turn count: {status['turn_count']}")
        
        print(f"\n{Fore.CYAN}Token Budget:{Style.RESET_ALL}")
        print(f"  Used: {status['token_usage']}/{status['token_budget']}")
        print(f"  Utilization: {status['budget_utilization']}")
        
        print(f"\n{Fore.CYAN}Loaded Contexts ({len(status['loaded_contexts'])} total):{Style.RESET_ALL}")
        for ctx in sorted(status['loaded_contexts']):
            details = status['context_details'][ctx]
            print(f"  ✓ {ctx:<12} {details['tokens']:>5} tokens (priority: {details['priority']})")
        
        print(f"\n{Fore.CYAN}Context Summary:{Style.RESET_ALL}")
        print(f"  Total contexts: {len(status['available_contexts'])}")
        print(f"  Loaded contexts: {len(status['loaded_contexts'])}")
        print(f"  Available contexts: {list(status['available_contexts'])}")
        print()