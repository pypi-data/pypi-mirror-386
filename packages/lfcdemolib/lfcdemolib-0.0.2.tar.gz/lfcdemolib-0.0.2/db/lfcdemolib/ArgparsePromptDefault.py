"""
ArgparsePromptDefault - Interactive Argument Prompting Library

This module extends argparse functionality to provide interactive prompts for
missing required arguments. It displays defaults, validates input, provides
numbered menu selections, and confirms settings before execution.

Features:
- Automatic prompting for missing arguments
- Default value display and acceptance
- Numbered menu selection
- Multi-select support
- Input validation with retry
- Configuration summary and confirmation
- Clean exit on cancellation

Usage:
    from lfcdemolib.ArgparsePromptDefault import PromptArgumentParser, PromptConfig
    
    parser = PromptArgumentParser(description='My Script')
    
    # Define arguments with prompt config
    parser.add_argument_with_prompt(
        '--name',
        prompt_config=PromptConfig(
            prompt_text="Enter your name",
            required=True,
            default="user"
        )
    )
    
    args = parser.parse_args_with_prompts()
"""

import sys
import argparse
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class PromptConfig:
    """Configuration for an argument prompt"""
    
    prompt_text: str = ""                    # Text to display when prompting
    required: bool = False                   # Whether the argument is required
    default: Any = None                      # Default value
    choices: Optional[List[Any]] = None      # Available choices (for menu)
    multi_select: bool = False               # Allow multiple selections
    validator: Optional[Callable] = None     # Custom validation function
    show_as_menu: bool = False              # Show choices as numbered menu
    help_text: str = ""                      # Additional help text
    
    # For file/directory selection
    is_file: bool = False
    is_dir: bool = False
    must_exist: bool = False
    glob_pattern: Optional[str] = None
    base_dir: Optional[Path] = None


class InteractivePrompter:
    """Handles interactive prompting for missing arguments"""
    
    def __init__(self, show_banner: bool = True):
        """Initialize the prompter
        
        Args:
            show_banner: Whether to show the interactive configuration banner
        """
        self.show_banner = show_banner
        self.collected_params = {}
        
    def prompt_for_value(
        self,
        arg_name: str,
        config: PromptConfig
    ) -> Any:
        """Prompt user for a single value
        
        Args:
            arg_name: Name of the argument
            config: Prompt configuration
            
        Returns:
            The value entered by the user
        """
        # Build prompt text
        prompt_text = config.prompt_text or f"{arg_name.replace('_', ' ').title()}"
        
        # Add default indicator
        if config.default is not None:
            prompt_text += f" [default: {config.default}]"
        
        # Add required indicator
        if config.required:
            prompt_text += " (required)"
        
        prompt_text += ": "
        
        # Handle menu selection
        if config.show_as_menu and config.choices:
            return self._prompt_menu_selection(prompt_text, config)
        
        # Handle regular input
        return self._prompt_regular_input(prompt_text, config)
    
    def _prompt_menu_selection(
        self,
        prompt_text: str,
        config: PromptConfig
    ) -> Any:
        """Prompt for menu selection
        
        Args:
            prompt_text: Prompt text to display
            config: Prompt configuration
            
        Returns:
            Selected value(s)
        """
        if not config.choices:
            raise ValueError("Menu selection requires choices")
        
        # Display menu
        print()
        print(f"Select {prompt_text.split('[')[0].strip()}:")
        if config.multi_select:
            print("  (Enter numbers separated by spaces, or press Enter for default)")
        
        for idx, choice in enumerate(config.choices, 1):
            print(f"  {idx}. {choice}")
        print()
        
        while True:
            if config.multi_select:
                user_input = input(f"Select options [1-{len(config.choices)}]: ").strip()
            else:
                user_input = input(f"Select option [1-{len(config.choices)}] or enter value: ").strip()
            
            # Handle empty input (default)
            if not user_input and config.default is not None:
                return config.default
            
            if not user_input and not config.required:
                return None
            
            # Handle multi-select
            if config.multi_select:
                selected = []
                for item in user_input.split():
                    if item.isdigit():
                        idx = int(item)
                        if 1 <= idx <= len(config.choices):
                            selected.append(config.choices[idx - 1])
                    elif item in config.choices:
                        selected.append(item)
                
                if selected:
                    return selected
                elif not config.required:
                    return None
                else:
                    print(f"  ⚠️  Invalid selection. Try again.")
                    continue
            
            # Handle single select by number
            if user_input.isdigit():
                idx = int(user_input)
                if 1 <= idx <= len(config.choices):
                    return config.choices[idx - 1]
                else:
                    print(f"  ⚠️  Invalid selection. Choose 1-{len(config.choices)}")
                    continue
            
            # Handle single select by value
            if user_input in config.choices:
                return user_input
            
            # Handle custom value (if not required to be from choices)
            if user_input and not config.required:
                confirm = input(f"  ⚠️  '{user_input}' not in choices. Use anyway? [y/N]: ").strip().lower()
                if confirm in ['y', 'yes']:
                    return user_input
            
            if config.required:
                print(f"  ⚠️  Invalid selection. Try again.")
    
    def _prompt_regular_input(
        self,
        prompt_text: str,
        config: PromptConfig
    ) -> Any:
        """Prompt for regular text input
        
        Args:
            prompt_text: Prompt text to display
            config: Prompt configuration
            
        Returns:
            Entered value
        """
        while True:
            user_input = input(prompt_text).strip()
            
            # Handle empty input
            if not user_input:
                if config.default is not None:
                    return config.default
                elif not config.required:
                    return None
                else:
                    print(f"  ⚠️  This field is required")
                    continue
            
            # Validate choices
            if config.choices and user_input not in config.choices:
                print(f"  ⚠️  Must be one of: {', '.join(str(c) for c in config.choices)}")
                continue
            
            # Handle file/directory validation
            if config.is_file or config.is_dir:
                path = Path(user_input).expanduser()
                if config.must_exist and not path.exists():
                    confirm = input(f"  ⚠️  Path not found: {path}. Use anyway? [y/N]: ").strip().lower()
                    if confirm not in ['y', 'yes']:
                        continue
                user_input = str(path)
            
            # Custom validation
            if config.validator:
                try:
                    result = config.validator(user_input)
                    if result is False:
                        print(f"  ⚠️  Invalid input. Try again.")
                        continue
                    elif result is not True:
                        user_input = result  # Validator can transform the value
                except Exception as e:
                    print(f"  ⚠️  Validation error: {e}")
                    continue
            
            return user_input
    
    def show_configuration_banner(self, defaults: Dict[str, Any]):
        """Show the interactive configuration banner
        
        Args:
            defaults: Dictionary of default values to display
        """
        if not self.show_banner:
            return
        
        print(f"\n{'='*80}")
        print(f"🔧 INTERACTIVE CONFIGURATION")
        print(f"{'='*80}\n")
        
        if defaults:
            print("📋 Default Configuration:")
            for key, value in defaults.items():
                print(f"   {key}: {value}")
            print()
    
    def ask_to_proceed(self, message: str = "Enter parameters interactively?") -> bool:
        """Ask user if they want to proceed with interactive mode
        
        Args:
            message: Message to display
            
        Returns:
            True if user wants to proceed, False otherwise
        """
        proceed = input(f"{message} [Y/n]: ").strip().lower()
        if proceed and proceed not in ['y', 'yes', '']:
            print("❌ Cancelled by user")
            return False
        print()
        return True
    
    def show_summary(self, params: Dict[str, Any], title: str = "Configuration Summary"):
        """Show configuration summary
        
        Args:
            params: Dictionary of parameters to display
            title: Title for the summary
        """
        print(f"\n{'='*80}")
        print(f"📋 {title}:")
        for key, value in params.items():
            # Format lists nicely
            if isinstance(value, list):
                value = ', '.join(str(v) for v in value)
            print(f"   {key.replace('_', ' ').title()}: {value}")
        print(f"{'='*80}\n")
    
    def confirm_settings(self) -> bool:
        """Ask user to confirm settings
        
        Returns:
            True if confirmed, False otherwise
        """
        confirm = input("Proceed with these settings? [Y/n]: ").strip().lower()
        if confirm and confirm not in ['y', 'yes', '']:
            print("❌ Cancelled by user")
            return False
        return True


class PromptArgumentParser(argparse.ArgumentParser):
    """Extended ArgumentParser with interactive prompting support"""
    
    def __init__(self, *args, **kwargs):
        """Initialize the parser"""
        super().__init__(*args, **kwargs)
        self._prompt_configs = {}
        self._prompt_order = []  # Track order of prompts
        self._show_banner = kwargs.get('show_banner', True)
        
    def add_argument_with_prompt(
        self,
        *name_or_flags,
        prompt_config: Optional[PromptConfig] = None,
        **kwargs
    ):
        """Add an argument with prompt configuration
        
        Args:
            *name_or_flags: Argument name(s) and flags
            prompt_config: Configuration for interactive prompting
            **kwargs: Standard argparse.add_argument kwargs
        """
        # Add the argument normally
        action = self.add_argument(*name_or_flags, **kwargs)
        
        # Store prompt config if provided
        if prompt_config:
            dest = action.dest
            self._prompt_configs[dest] = prompt_config
            self._prompt_order.append(dest)
        
        return action
    
    def parse_args_with_prompts(
        self,
        args=None,
        namespace=None,
        interactive_callback: Optional[Callable] = None
    ):
        """Parse arguments and prompt for missing values
        
        Args:
            args: Arguments to parse (None = sys.argv)
            namespace: Namespace object to populate
            interactive_callback: Optional callback function that returns a dict
                                 of values to use for prompting (for custom logic)
            
        Returns:
            Namespace with all arguments populated
        """
        # Parse command-line arguments first
        parsed_args = super().parse_args(args, namespace)
        
        # Check if any required prompts are missing
        missing_prompts = []
        for dest in self._prompt_order:
            config = self._prompt_configs.get(dest)
            if config and config.required:
                value = getattr(parsed_args, dest, None)
                if value is None or (isinstance(value, str) and not value):
                    missing_prompts.append(dest)
        
        # If nothing missing, return as-is
        if not missing_prompts and not interactive_callback:
            return parsed_args
        
        # Use custom callback if provided
        if interactive_callback:
            interactive_values = interactive_callback()
            if interactive_values:
                for key, value in interactive_values.items():
                    if not getattr(parsed_args, key, None):
                        setattr(parsed_args, key, value)
                return parsed_args
        
        # Initialize prompter
        prompter = InteractivePrompter(show_banner=self._show_banner)
        
        # Show banner
        defaults = {
            dest: config.default
            for dest, config in self._prompt_configs.items()
            if config.default is not None
        }
        prompter.show_configuration_banner(defaults)
        
        # Ask to proceed
        if not prompter.ask_to_proceed():
            sys.exit(0)
        
        # Collect values for missing prompts
        collected = {}
        for dest in self._prompt_order:
            # Skip if already provided via command line
            value = getattr(parsed_args, dest, None)
            if value is not None and value != '':
                continue
            
            config = self._prompt_configs.get(dest)
            if not config:
                continue
            
            # Prompt for value
            prompted_value = prompter.prompt_for_value(dest, config)
            if prompted_value is not None:
                collected[dest] = prompted_value
                setattr(parsed_args, dest, prompted_value)
        
        # Show summary and confirm
        if collected:
            # Build summary with all effective values
            summary = {}
            for dest in self._prompt_order:
                value = getattr(parsed_args, dest, None)
                if value is not None:
                    summary[dest] = value
            
            prompter.show_summary(summary)
            
            if not prompter.confirm_settings():
                sys.exit(0)
        
        return parsed_args


def create_file_prompt_config(
    prompt_text: str,
    required: bool = True,
    default: Optional[str] = None,
    must_exist: bool = True,
    glob_pattern: Optional[str] = None,
    base_dir: Optional[Path] = None
) -> PromptConfig:
    """Helper to create file selection prompt config
    
    Args:
        prompt_text: Text to display when prompting
        required: Whether the file is required
        default: Default file path
        must_exist: Whether the file must exist
        glob_pattern: Glob pattern to list available files
        base_dir: Base directory for file search
        
    Returns:
        PromptConfig for file selection
    """
    choices = None
    if glob_pattern and base_dir:
        try:
            choices = [f.name for f in sorted(base_dir.glob(glob_pattern))]
        except Exception:
            choices = None
    
    return PromptConfig(
        prompt_text=prompt_text,
        required=required,
        default=default,
        is_file=True,
        must_exist=must_exist,
        choices=choices,
        show_as_menu=bool(choices),
        glob_pattern=glob_pattern,
        base_dir=base_dir
    )


def create_menu_prompt_config(
    prompt_text: str,
    choices: List[Any],
    required: bool = True,
    default: Optional[Any] = None,
    multi_select: bool = False
) -> PromptConfig:
    """Helper to create menu selection prompt config
    
    Args:
        prompt_text: Text to display when prompting
        choices: List of available choices
        required: Whether a selection is required
        default: Default value
        multi_select: Allow multiple selections
        
    Returns:
        PromptConfig for menu selection
    """
    return PromptConfig(
        prompt_text=prompt_text,
        choices=choices,
        required=required,
        default=default,
        multi_select=multi_select,
        show_as_menu=True
    )

