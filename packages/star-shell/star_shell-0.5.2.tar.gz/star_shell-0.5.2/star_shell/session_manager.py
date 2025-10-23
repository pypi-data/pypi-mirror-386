import signal
import sys
from typing import List, Dict, Optional, Tuple
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text

from star_shell.backend import BaseGenie
from star_shell.context import ContextProvider
from star_shell.command_executor import CommandExecutor
from star_shell.mode_manager import ModeManager


class SessionManager:
    """Manages interactive chat sessions with conversation history."""
    
    def __init__(self, genie: BaseGenie, context_provider: ContextProvider):
        self.genie = genie
        self.context_provider = context_provider
        self.console = Console()
        self.executor = CommandExecutor()
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history_length = 10  # Keep last 10 exchanges
        self.running = True
        
        # Initialize mode manager for backend switching
        self.mode_manager = ModeManager(self)
        
        # Session statistics and tracking
        import datetime
        self.session_start_time = datetime.datetime.now()
        self.mode_switch_history: List[Dict] = []
        self.commands_executed = 0
        self.successful_commands = 0
        
        # Set up signal handler for graceful exit
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully."""
        self.console.print("\n[yellow]Chat session interrupted. Goodbye![/yellow]")
        self.running = False
        sys.exit(0)
    
    def add_to_history(self, role: str, content: str):
        """Add a message to conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content
        })
        
        # Trim history if it gets too long
        if len(self.conversation_history) > self.max_history_length * 2:  # *2 for user+assistant pairs
            self.conversation_history = self.conversation_history[-self.max_history_length * 2:]
    
    def get_context(self) -> Dict:
        """Get current system context."""
        return self.context_provider.build_context()
    
    def format_history_for_prompt(self) -> str:
        """Format conversation history for inclusion in AI prompts."""
        if not self.conversation_history:
            return ""
        
        history_lines = ["Recent conversation:"]
        for msg in self.conversation_history[-6:]:  # Last 3 exchanges
            role_label = "You" if msg["role"] == "user" else "Assistant"
            history_lines.append(f"{role_label}: {msg['content']}")
        
        return "\n".join(history_lines) + "\n\n"
    
    def handle_special_commands(self, user_input: str) -> bool:
        """
        Handle special commands like mode switching, status, and help.
        
        Processes commands that control Star Shell's behavior rather than
        generating AI responses. This includes mode switching, status display,
        help information, and quick backend shortcuts.
        
        Args:
            user_input: The user's input string to check for special commands
            
        Returns:
            bool: True if a special command was recognized and handled,
                  False if the input should be processed as a regular AI query
        
        Supported Commands:
            - mode, /mode: Interactive backend selection
            - status, /status: Current session information  
            - help, /help: Display help information
            - /gpt, /gemini (menu), /flash, /thinking, /secret, /secret-temp: Quick mode switches
        
        Note:
            Commands are case-insensitive and leading/trailing whitespace is ignored.
            Quick mode switches will only work if appropriate credentials are configured.
        """
        # Normalize input for command detection
        normalized_input = user_input.lower().strip()
        
        # Parse command and arguments
        parts = normalized_input.split()
        if not parts:
            return False
        
        command = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        # Handle mode switching commands
        if command in ['mode', '/mode']:
            return self._handle_mode_command(args)
        
        # Handle status commands
        if command in ['status', '/status']:
            # Check for detailed status flag
            if args and args[0] in ['--detailed', '-d', 'detailed']:
                self.display_detailed_status()
            else:
                self.display_current_mode()
            return True
        
        # Handle help commands
        if command in ['help', '/help']:
            self.display_help()
            return True
        
        # Handle quick mode switching shortcuts
        quick_commands = ['/gpt', '/gemini', '/flash', '/thinking', '/secret', '/secret-temp']
        if command in quick_commands:
            return self._handle_quick_mode_switch(command)
        
        return False
    
    def _handle_mode_command(self, args: List[str]) -> bool:
        """
        Handle the /mode command for interactive mode selection.
        
        Displays an interactive menu showing all available AI backends with
        descriptions, current status, and allows the user to select a new
        backend to switch to. Handles credential prompting if needed.
        
        Args:
            args: Additional command arguments (currently unused)
            
        Returns:
            bool: Always returns True since this command is always handled
        
        User Experience:
            1. Shows current backend with clear indication
            2. Lists all available backends with descriptions
            3. Prompts for numeric selection or 0 to cancel
            4. Handles credential setup for new backends
            5. Provides clear feedback on success/failure
        """
        available_modes = self.mode_manager.list_available_modes()
        current_mode = self.mode_manager.get_current_mode()
        
        # Display current mode first
        current_display_name = self.mode_manager.get_mode_display_name(current_mode)
        self.console.print(f"\n[bold green]Current AI Backend:[/bold green] {current_display_name}")
        
        # Display available modes with descriptions
        self.console.print("\n[bold blue]Available AI Backends:[/bold blue]")
        mode_descriptions = {
            "openai-gpt-3.5-turbo": "Fast and reliable for general tasks",
            "gemini-pro": "Google's advanced model with strong reasoning",
            "gemini-flash": "Faster responses with good performance",
            "gemini-thinking": "Adaptive planning for complex multi-step tasks",
            "secret-3.14159": "Hosted backend service (no API key required)"
        }
        
        for i, mode in enumerate(available_modes, 1):
            display_name = self.mode_manager.get_mode_display_name(mode)
            description = mode_descriptions.get(mode, "")
            current_indicator = " [green](current)[/green]" if mode == current_mode else ""
            
            self.console.print(f"  {i}. [bold]{display_name}[/bold]{current_indicator}")
            if description:
                self.console.print(f"     [dim]{description}[/dim]")
        
        # Get user selection
        try:
            from rich.prompt import IntPrompt
            choice = IntPrompt.ask(
                f"\n[bold blue]Select backend (1-{len(available_modes)}) or 0 to cancel[/bold blue]",
                default=0
            )
            
            if choice == 0:
                self.console.print("[yellow]Mode selection cancelled.[/yellow]")
                return True
            
            if 1 <= choice <= len(available_modes):
                selected_mode = available_modes[choice - 1]
                
                # Check if already using this mode
                if selected_mode == current_mode:
                    display_name = self.mode_manager.get_mode_display_name(selected_mode)
                    self.console.print(f"[yellow]Already using {display_name}[/yellow]")
                    return True
                
                return self._switch_to_mode(selected_mode)
            else:
                self.console.print(f"[red]Invalid selection. Please choose a number between 0 and {len(available_modes)}.[/red]")
                return True
                
        except (KeyboardInterrupt, EOFError):
            self.console.print("\n[yellow]Mode selection cancelled.[/yellow]")
            return True
    
    def _handle_quick_mode_switch(self, command: str) -> bool:
        """Handle quick mode switching shortcuts like /gpt, /gemini, etc."""
        # Special handling for /gemini - show Gemini model selection
        if command == '/gemini':
            return self._handle_gemini_mode_selection()
        
        # Special handling for temporary secret mode
        if command == '/secret-temp':
            return self._handle_temporary_secret_mode()
        
        # Map other quick commands to modes
        quick_mapping = {
            '/gpt': 'openai-gpt-3.5-turbo',
            '/flash': 'gemini-flash',
            '/thinking': 'gemini-thinking',
            '/secret': 'secret-3.14159'
        }
        
        target_mode = quick_mapping.get(command)
        if not target_mode:
            return False
        
        current_mode = self.mode_manager.get_current_mode()
        if current_mode == target_mode:
            display_name = self.mode_manager.get_mode_display_name(target_mode)
            self.console.print(f"[yellow]Already using {display_name}[/yellow]")
            return True
        
        return self._switch_to_mode(target_mode)
    
    def _handle_gemini_mode_selection(self) -> bool:
        """Handle /gemini command by showing Gemini model selection menu."""
        from rich.prompt import Prompt
        
        # Show current mode
        current_mode = self.mode_manager.get_current_mode()
        current_display = self.mode_manager.get_mode_display_name(current_mode)
        
        self.console.print(f"\n[bold blue]Gemini Model Selection[/bold blue]")
        self.console.print(f"[dim]Current mode: {current_display}[/dim]\n")
        
        # Show available Gemini models
        gemini_options = {
            "1": ("gemini-pro", "Gemini Pro - Google's advanced model with strong reasoning"),
            "2": ("gemini-flash", "Gemini Flash - Faster responses with good performance"), 
            "3": ("gemini-thinking", "Gemini Thinking - Adaptive planning for complex multi-step tasks")
        }
        
        for key, (mode, description) in gemini_options.items():
            current_indicator = " [green](current)[/green]" if current_mode == mode else ""
            self.console.print(f"[bold cyan]{key}.[/bold cyan] {description}{current_indicator}")
        
        self.console.print(f"[bold cyan]0.[/bold cyan] Cancel")
        
        try:
            choice = Prompt.ask("\nSelect Gemini model", choices=["0", "1", "2", "3"], default="0")
            
            if choice == "0":
                self.console.print("[yellow]Selection cancelled.[/yellow]")
                return True
            
            target_mode, _ = gemini_options[choice]
            
            # Check if already using selected mode
            if current_mode == target_mode:
                display_name = self.mode_manager.get_mode_display_name(target_mode)
                self.console.print(f"[yellow]Already using {display_name}[/yellow]")
                return True
            
            return self._switch_to_mode(target_mode)
            
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Selection cancelled.[/yellow]")
            return True
        except Exception as e:
            self.console.print(f"[red]Error in model selection: {str(e)}[/red]")
            return True
    
    def _handle_temporary_secret_mode(self) -> bool:
        """Handle temporary secret mode - use secret backend for next query only."""
        current_mode = self.mode_manager.get_current_mode()
        current_display = self.mode_manager.get_mode_display_name(current_mode)
        
        self.console.print(f"\n[bold blue]Temporary Secret Mode[/bold blue]")
        self.console.print(f"[dim]Current mode: {current_display}[/dim]")
        self.console.print("[yellow]Next query will use the secret backend, then return to your current mode.[/yellow]")
        
        # Store the current backend for restoration
        self._temp_mode_restore = {
            'mode': current_mode,
            'genie': self.genie
        }
        
        # Switch to secret mode temporarily
        credentials = {
            "backend_url": "https://star-shell-backend.vercel.app/",
            "secret_token": "secret-3.14159",
            "model_type": "gemini-pro"
        }
        
        try:
            # Create temporary secret genie
            from star_shell.backend import ProxyGenie
            os_fullname = getattr(self.genie, 'os_fullname', 'Unknown OS')
            shell = getattr(self.genie, 'shell', 'bash')
            
            temp_genie = ProxyGenie(
                credentials["backend_url"], 
                credentials["secret_token"], 
                os_fullname, 
                shell, 
                credentials["model_type"]
            )
            
            if temp_genie.validate_credentials():
                self.genie = temp_genie
                self._temp_mode_active = True
                self.console.print("[green]✓ Temporary secret mode activated. Enter your query:[/green]")
                return True
            else:
                self.console.print("[red]✗ Failed to connect to secret backend[/red]")
                return True
                
        except Exception as e:
            self.console.print(f"[red]✗ Error activating temporary secret mode: {str(e)}[/red]")
            return True
    
    def _restore_from_temporary_mode(self):
        """Restore the original mode after temporary secret mode usage."""
        if hasattr(self, '_temp_mode_restore') and hasattr(self, '_temp_mode_active'):
            if self._temp_mode_active:
                self.genie = self._temp_mode_restore['genie']
                mode_display = self.mode_manager.get_mode_display_name(self._temp_mode_restore['mode'])
                self.console.print(f"[dim]Restored to {mode_display} mode[/dim]")
                self._temp_mode_active = False
                delattr(self, '_temp_mode_restore')
    
    def _switch_to_mode(self, target_mode: str) -> bool:
        """
        Switch to the specified mode, handling credential prompts if needed.
        
        Orchestrates the complete mode switching process including credential
        validation, backend initialization, and user feedback. Provides detailed
        error messages and troubleshooting guidance on failure.
        
        Args:
            target_mode: The mode identifier to switch to (e.g., 'gemini-pro')
            
        Returns:
            bool: Always returns True since the command is handled regardless
                  of success/failure (user remains in session)
        
        Process Flow:
            1. Get and validate credentials for target mode
            2. Initialize new backend instance
            3. Update session manager with new backend
            4. Preserve conversation history
            5. Display success confirmation or error guidance
        
        Error Handling:
            - Invalid credentials: Shows specific validation help
            - Network issues: Suggests connectivity troubleshooting  
            - Service unavailable: Recommends alternative backends
            - Unexpected errors: Provides general troubleshooting steps
        """
        display_name = self.mode_manager.get_mode_display_name(target_mode)
        previous_mode = self.mode_manager.get_current_mode()
        previous_display_name = self.mode_manager.get_mode_display_name(previous_mode)
        
        try:
            self.console.print(f"\n[bold blue]Switching from {previous_display_name} to {display_name}...[/bold blue]")
            
            # Get credentials if needed
            credentials = self._get_mode_credentials(target_mode)
            if credentials is None:
                self.console.print("[yellow]Mode switch cancelled.[/yellow]")
                return True
            
            # Show switching progress
            self.console.print("[dim]Initializing new backend...[/dim]")
            
            # Attempt to switch mode
            if self.mode_manager.switch_mode(target_mode, **credentials):
                # Success - show confirmation with details
                self.console.print(f"\n[bold green]✓ Successfully switched to {display_name}![/bold green]")
                
                # Show additional info about the new mode
                if target_mode == "gemini-thinking":
                    self.console.print("[dim]This mode supports adaptive planning for complex multi-step tasks.[/dim]")
                elif target_mode == "gemini-flash":
                    self.console.print("[dim]This mode provides faster responses with good performance.[/dim]")
                elif target_mode == "secret-3.14159":
                    self.console.print("[dim]Using hosted backend service - no API key required.[/dim]")
                
                # Show conversation history preservation
                if self.conversation_history:
                    self.console.print(f"[dim]Conversation history preserved ({len(self.conversation_history)} messages)[/dim]")
                
                return True
            else:
                self.console.print(f"[red]✗ Failed to switch to {display_name}[/red]")
                self.console.print(f"[yellow]Remaining in {previous_display_name} mode[/yellow]")
                
                # Provide detailed error guidance based on the mode
                self._display_mode_switch_error_help(target_mode)
                
                return True
                
        except Exception as e:
            self.console.print(f"[red]✗ Error switching to {display_name}: {str(e)}[/red]")
            self.console.print(f"[yellow]Remaining in {previous_display_name} mode[/yellow]")
            
            # Provide context-specific error help
            self._display_generic_error_help(target_mode, str(e))
            return True
    
    def _get_mode_credentials(self, mode: str) -> Optional[Dict]:
        """Get credentials for the specified mode, prompting user if needed."""
        from rich.prompt import Prompt, Confirm
        
        # Get mode configuration
        mode_configs = self.mode_manager._mode_configs
        config = mode_configs.get(mode)
        
        if not config:
            self.console.print(f"[red]Unknown mode: {mode}[/red]")
            return None
        
        credentials = {}
        
        # Handle modes that don't require API keys
        if not config.requires_api_key:
            if mode == "secret-3.14159":
                # For secret backend, use default values
                credentials = {
                    "backend_url": "https://star-shell-backend.vercel.app/",
                    "secret_token": "secret-3.14159",
                    "model_type": "gemini-pro"
                }
            return credentials
        
        # Check if we already have valid credentials for this mode
        current_mode = self.mode_manager.get_current_mode()
        if current_mode == mode:
            # Already using this mode, no need for new credentials
            return {}
        
        # Prompt for API key with validation
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                self.console.print(f"\n[bold blue]Setting up {config.display_name}[/bold blue]")
                
                if config.api_key_field == "openai_api_key":
                    self.console.print("[dim]You can get your API key from: https://platform.openai.com/api-keys[/dim]")
                elif config.api_key_field == "gemini_api_key":
                    self.console.print("[dim]You can get your API key from: https://aistudio.google.com/app/apikey[/dim]")
                
                api_key = Prompt.ask(
                    f"[bold blue]Enter {config.display_name} API key[/bold blue]",
                    password=True
                )
                
                if not api_key.strip():
                    self.console.print("[yellow]API key cannot be empty.[/yellow]")
                    continue
                
                credentials[config.api_key_field] = api_key.strip()
                
                # Validate credentials before returning
                self.console.print("[dim]Validating credentials...[/dim]")
                if self.mode_manager.validate_mode_credentials(mode, **credentials):
                    self.console.print("[green]✓ Credentials validated successfully[/green]")
                    return credentials
                else:
                    self.console.print(f"[red]✗ Invalid API key for {config.display_name}[/red]")
                    
                    # Provide specific validation failure help
                    if config.api_key_field == "openai_api_key":
                        self.console.print("[dim]OpenAI API key should start with 'sk-' and be 51+ characters[/dim]")
                    elif config.api_key_field == "gemini_api_key":
                        self.console.print("[dim]Gemini API key should be 39+ characters long[/dim]")
                    
                    if attempt < max_attempts - 1:
                        if not Confirm.ask("[yellow]Try again?[/yellow]"):
                            break
                    credentials = {}
                    
            except (KeyboardInterrupt, EOFError):
                self.console.print("\n[yellow]Credential setup cancelled.[/yellow]")
                return None
        
        self.console.print(f"[red]Failed to validate credentials for {config.display_name} after {max_attempts} attempts.[/red]")
        self._display_credential_error_help(config)
        return None
    
    def _display_mode_switch_error_help(self, target_mode: str) -> None:
        """
        Display helpful error messages and troubleshooting tips for mode switching failures.
        
        Provides specific guidance based on the target mode and common failure scenarios
        to help users resolve issues and successfully switch backends.
        
        Args:
            target_mode: The mode that failed to switch to
        """
        config = self.mode_manager._mode_configs.get(target_mode)
        if not config:
            self.console.print("[dim]Unknown backend mode. Use 'mode' to see available options.[/dim]")
            return
        
        self.console.print("\n[bold yellow]💡 Troubleshooting Tips:[/bold yellow]")
        
        if config.requires_api_key:
            if config.api_key_field == "openai_api_key":
                self.console.print("[dim]• Check your OpenAI API key is valid and has sufficient credits[/dim]")
                self.console.print("[dim]• Get your API key from: https://platform.openai.com/api-keys[/dim]")
                self.console.print("[dim]• Verify your account has billing set up[/dim]")
                self.console.print("[dim]• Try using '/secret' for a no-API-key option[/dim]")
            elif config.api_key_field == "gemini_api_key":
                self.console.print("[dim]• Check your Gemini API key is valid and active[/dim]")
                self.console.print("[dim]• Get your API key from: https://aistudio.google.com/app/apikey[/dim]")
                self.console.print("[dim]• Ensure the Gemini API service is accessible from your location[/dim]")
                self.console.print("[dim]• Try using '/secret' for a no-API-key option[/dim]")
        else:
            if target_mode == "secret-3.14159":
                self.console.print("[dim]• Check your internet connection[/dim]")
                self.console.print("[dim]• The hosted backend service might be temporarily unavailable[/dim]")
                self.console.print("[dim]• Try again in a few moments[/dim]")
        
        self.console.print("[dim]• Use 'mode' to see all available backends and their status[/dim]")
        self.console.print("[dim]• Use 'status' to check your current session information[/dim]")
    
    def _display_credential_error_help(self, config) -> None:
        """
        Display helpful error messages for credential validation failures.
        
        Provides specific guidance for resolving API key and credential issues
        based on the backend type and common problems users encounter.
        
        Args:
            config: The ModeConfig object for the backend that failed validation
        """
        self.console.print(f"\n[bold yellow]💡 {config.display_name} Setup Help:[/bold yellow]")
        
        if config.api_key_field == "openai_api_key":
            self.console.print("[dim]Common issues with OpenAI API keys:[/dim]")
            self.console.print("[dim]• Key format should start with 'sk-'[/dim]")
            self.console.print("[dim]• Check for extra spaces or characters[/dim]")
            self.console.print("[dim]• Verify your account has billing enabled[/dim]")
            self.console.print("[dim]• Ensure the key hasn't been revoked or expired[/dim]")
            self.console.print("[dim]• Get a new key at: https://platform.openai.com/api-keys[/dim]")
        elif config.api_key_field == "gemini_api_key":
            self.console.print("[dim]Common issues with Gemini API keys:[/dim]")
            self.console.print("[dim]• Check for extra spaces or characters when pasting[/dim]")
            self.console.print("[dim]• Verify the key is enabled for the Gemini API[/dim]")
            self.console.print("[dim]• Ensure your Google Cloud project has the API enabled[/dim]")
            self.console.print("[dim]• Check if there are usage quotas or restrictions[/dim]")
            self.console.print("[dim]• Get a new key at: https://aistudio.google.com/app/apikey[/dim]")
        
        self.console.print("\n[dim]Alternative: Use '/secret' to try the hosted backend (no API key required)[/dim]")
    
    def _display_generic_error_help(self, target_mode: str, error_message: str) -> None:
        """
        Display generic error help for unexpected mode switching failures.
        
        Provides general troubleshooting guidance when mode switching fails
        due to unexpected errors or system issues.
        
        Args:
            target_mode: The mode that failed to switch to
            error_message: The error message that was caught
        """
        self.console.print(f"\n[bold yellow]💡 General Troubleshooting:[/bold yellow]")
        
        # Check for common error patterns
        error_lower = error_message.lower()
        
        if "network" in error_lower or "connection" in error_lower:
            self.console.print("[dim]• Check your internet connection[/dim]")
            self.console.print("[dim]• Try again in a few moments[/dim]")
            self.console.print("[dim]• Consider using '/secret' if other backends are unavailable[/dim]")
        elif "api" in error_lower or "key" in error_lower:
            self.console.print("[dim]• Verify your API key is correct and active[/dim]")
            self.console.print("[dim]• Check if the service has usage limits or quotas[/dim]")
            self.console.print("[dim]• Try regenerating your API key[/dim]")
        elif "timeout" in error_lower:
            self.console.print("[dim]• The service might be experiencing high load[/dim]")
            self.console.print("[dim]• Try again in a few moments[/dim]")
            self.console.print("[dim]• Check your internet connection stability[/dim]")
        else:
            self.console.print("[dim]• This appears to be an unexpected error[/dim]")
            self.console.print("[dim]• Try restarting Star Shell if the problem persists[/dim]")
            self.console.print("[dim]• Use 'mode' to see available backends[/dim]")
        
        self.console.print("[dim]• Use 'status' to check your current session[/dim]")
        self.console.print("[dim]• Use 'help' for more information about commands[/dim]")
    
    def update_backend(self, new_genie: BaseGenie) -> None:
        """
        Switch to new backend while preserving context and conversation history.
        
        Args:
            new_genie: The new AI backend instance to switch to
        """
        # Store previous backend for rollback if needed
        previous_genie = self.genie
        previous_mode = self.mode_manager.get_current_mode()
        
        try:
            # Update to new backend
            self.genie = new_genie
            
            # Conversation history is preserved automatically since it's stored in SessionManager
            # Context will be rebuilt fresh for each request, so no special handling needed
            
            # Track the mode switch
            current_mode = self.mode_manager.get_current_mode()
            display_name = self.mode_manager.get_mode_display_name(current_mode)
            
            # Add to mode switch history
            import datetime
            self.mode_switch_history.append({
                "timestamp": datetime.datetime.now(),
                "from_mode": previous_mode,
                "to_mode": current_mode,
                "from_display_name": self.mode_manager.get_mode_display_name(previous_mode),
                "to_display_name": display_name
            })
            
            # Add a system message to track the mode switch
            self.add_to_history("system", f"Switched to {display_name}")
            
        except Exception as e:
            # Rollback to previous backend on failure
            self.genie = previous_genie
            raise e
    
    def display_current_mode(self) -> None:
        """Display current backend mode and session information."""
        current_mode = self.mode_manager.get_current_mode()
        display_name = self.mode_manager.get_mode_display_name(current_mode)
        
        # Calculate session duration
        import datetime
        session_duration = datetime.datetime.now() - self.session_start_time
        duration_str = self._format_duration(session_duration)
        
        # Create status information
        status_text = Text()
        
        # Current backend info
        status_text.append("🤖 Current AI Backend\n", style="bold blue")
        status_text.append("   Name: ", style="white")
        status_text.append(f"{display_name}\n", style="bold green")
        status_text.append("   Mode ID: ", style="white")
        status_text.append(f"{current_mode}\n", style="cyan")
        
        # Add quick command info
        quick_mapping = self.mode_manager.get_quick_command_mapping()
        current_quick = None
        for cmd, mode in quick_mapping.items():
            if mode == current_mode:
                current_quick = cmd
                break
        
        if current_quick:
            status_text.append("   Quick Command: ", style="white")
            status_text.append(f"{current_quick}\n", style="bold cyan")
        
        # Session statistics
        status_text.append("\n📊 Session Statistics\n", style="bold blue")
        status_text.append("   Duration: ", style="white")
        status_text.append(f"{duration_str}\n", style="yellow")
        status_text.append("   Messages: ", style="white")
        status_text.append(f"{len(self.conversation_history)} exchanges\n", style="yellow")
        status_text.append("   Commands Executed: ", style="white")
        status_text.append(f"{self.commands_executed}\n", style="yellow")
        
        if self.commands_executed > 0:
            success_rate = (self.successful_commands / self.commands_executed) * 100
            status_text.append("   Success Rate: ", style="white")
            status_text.append(f"{success_rate:.1f}% ({self.successful_commands}/{self.commands_executed})\n", style="green" if success_rate >= 80 else "yellow")
        
        # Mode switch history
        if self.mode_switch_history:
            status_text.append("\n🔄 Mode Switch History\n", style="bold blue")
            # Show last 3 switches
            recent_switches = self.mode_switch_history[-3:]
            for switch in recent_switches:
                time_str = switch["timestamp"].strftime("%H:%M:%S")
                status_text.append(f"   {time_str}: ", style="dim")
                status_text.append(f"{switch['from_display_name']}", style="red")
                status_text.append(" → ", style="white")
                status_text.append(f"{switch['to_display_name']}\n", style="green")
            
            if len(self.mode_switch_history) > 3:
                status_text.append(f"   ... and {len(self.mode_switch_history) - 3} more\n", style="dim")
        
        # Available commands
        status_text.append("\n💡 Available Commands\n", style="bold blue")
        status_text.append("   mode, /mode - Switch AI backend\n", style="dim")
        status_text.append("   status, /status - Show this status\n", style="dim")
        status_text.append("   help, /help - Show help information\n", style="dim")
        status_text.append("   /gpt, /gemini, /flash, /thinking, /secret, /secret-temp - Quick switches\n", style="dim")
        
        self.console.print(Panel(
            status_text,
            title="[bold blue]⭐ Star Shell Status[/bold blue]",
            border_style="blue",
            padding=(0, 1)
        ))
    
    def display_detailed_status(self) -> None:
        """Display detailed session information and backend details."""
        current_mode = self.mode_manager.get_current_mode()
        display_name = self.mode_manager.get_mode_display_name(current_mode)
        
        # Calculate session duration
        import datetime
        session_duration = datetime.datetime.now() - self.session_start_time
        duration_str = self._format_duration(session_duration)
        
        # Create detailed status information
        status_text = Text()
        
        # Session overview
        status_text.append("📋 Session Overview\n", style="bold blue")
        status_text.append(f"   Started: {self.session_start_time.strftime('%Y-%m-%d %H:%M:%S')}\n", style="white")
        status_text.append(f"   Duration: {duration_str}\n", style="white")
        status_text.append(f"   Current Backend: {display_name}\n", style="bold green")
        
        # Backend details
        status_text.append(f"\n🔧 Backend Configuration\n", style="bold blue")
        config = self.mode_manager._mode_configs.get(current_mode)
        if config:
            status_text.append(f"   Type: {config.backend_type}\n", style="white")
            status_text.append(f"   Requires API Key: {'Yes' if config.requires_api_key else 'No'}\n", style="white")
            status_text.append(f"   Quick Command: {config.quick_command}\n", style="white")
        
        # Conversation statistics
        status_text.append(f"\n💬 Conversation Statistics\n", style="bold blue")
        status_text.append(f"   Total Messages: {len(self.conversation_history)}\n", style="white")
        
        # Count user vs assistant messages
        user_messages = sum(1 for msg in self.conversation_history if msg["role"] == "user")
        assistant_messages = sum(1 for msg in self.conversation_history if msg["role"] == "assistant")
        system_messages = sum(1 for msg in self.conversation_history if msg["role"] == "system")
        
        status_text.append(f"   User Messages: {user_messages}\n", style="cyan")
        status_text.append(f"   Assistant Messages: {assistant_messages}\n", style="green")
        status_text.append(f"   System Messages: {system_messages}\n", style="yellow")
        
        # Command execution statistics
        status_text.append(f"\n⚡ Command Execution\n", style="bold blue")
        status_text.append(f"   Total Commands: {self.commands_executed}\n", style="white")
        status_text.append(f"   Successful: {self.successful_commands}\n", style="green")
        status_text.append(f"   Failed: {self.commands_executed - self.successful_commands}\n", style="red")
        
        if self.commands_executed > 0:
            success_rate = (self.successful_commands / self.commands_executed) * 100
            status_text.append(f"   Success Rate: {success_rate:.1f}%\n", style="bold green" if success_rate >= 80 else "bold yellow")
        
        # Complete mode switch history
        if self.mode_switch_history:
            status_text.append(f"\n🔄 Complete Mode Switch History\n", style="bold blue")
            for i, switch in enumerate(self.mode_switch_history, 1):
                time_str = switch["timestamp"].strftime("%H:%M:%S")
                status_text.append(f"   {i}. {time_str}: ", style="dim")
                status_text.append(f"{switch['from_display_name']}", style="red")
                status_text.append(" → ", style="white")
                status_text.append(f"{switch['to_display_name']}\n", style="green")
        
        # Available backends
        status_text.append(f"\n🎯 Available Backends\n", style="bold blue")
        available_modes = self.mode_manager.list_available_modes()
        for mode in available_modes:
            mode_display_name = self.mode_manager.get_mode_display_name(mode)
            mode_config = self.mode_manager._mode_configs.get(mode)
            current_indicator = " (current)" if mode == current_mode else ""
            
            status_text.append(f"   • {mode_display_name}{current_indicator}\n", style="green" if mode == current_mode else "white")
            if mode_config:
                status_text.append(f"     Quick: {mode_config.quick_command} | ", style="dim")
                status_text.append(f"API Key: {'Required' if mode_config.requires_api_key else 'Not Required'}\n", style="dim")
        
        self.console.print(Panel(
            status_text,
            title="[bold blue]⭐ Detailed Star Shell Status[/bold blue]",
            border_style="blue",
            padding=(0, 1)
        ))
    
    def _format_duration(self, duration) -> str:
        """Format a timedelta object into a human-readable string."""
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def get_enhanced_prompt(self) -> str:
        """Get enhanced prompt that includes mode indicator."""
        current_mode = self.mode_manager.get_current_mode()
        display_name = self.mode_manager.get_mode_display_name(current_mode)
        
        # Create a short mode indicator
        mode_indicators = {
            "openai-gpt-3.5-turbo": "GPT",
            "gemini-pro": "Gemini",
            "gemini-flash": "Flash",
            "gemini-thinking": "Think",
            "secret-3.14159": "Secret"
        }
        
        indicator = mode_indicators.get(current_mode, "AI")
        return f"[bold blue]⭐[/bold blue][dim cyan]({indicator})[/dim cyan]"
    

    
    def process_input(self, user_input: str) -> bool:
        """
        Process user input and generate AI response.
        
        Returns:
            True to continue session, False to exit
        """
        # Check for exit commands
        if user_input.lower().strip() in ['exit', 'quit', 'bye', 'goodbye']:
            return False
        
        # Handle special commands (mode switching, status, help)
        if self.handle_special_commands(user_input):
            return True
        
        # Add user input to history
        self.add_to_history("user", user_input)
        
        try:
            # Get current context
            context = self.get_context()
            context["conversation_history"] = self.conversation_history
            
            # Get AI response using the new chat method
            response_type, content, description = self.genie.chat(user_input, context=context)
            
            if response_type == "command":
                # AI wants to execute a single command
                self.add_to_history("assistant", f"Command: {content}" + (f"\nDescription: {description}" if description else ""))
                
                # Display the command
                self.executor.display_command(content, description)
                
                # Ask if user wants to execute
                if self.executor.prompt_for_execution():
                    if self.executor.check_command_safety(content):
                        self.console.print("[blue]Executing command...[/blue]")
                        return_code, stdout, stderr = self.executor.execute_command(content)
                        self.executor.display_execution_result(return_code, stdout, stderr)
                        
                        # Track command execution
                        self.commands_executed += 1
                        if return_code == 0:
                            self.successful_commands += 1
                        
                        # Add execution result to history
                        if return_code == 0:
                            self.add_to_history("system", f"Command executed successfully: {stdout[:200]}")
                        else:
                            self.add_to_history("system", f"Command failed: {stderr[:200]}")
                    else:
                        self.console.print("[yellow]Command execution cancelled due to safety concerns.[/yellow]")
                else:
                    self.console.print("[yellow]Command execution cancelled by user.[/yellow]")
                    
            elif response_type == "commands":
                # AI wants to execute multiple commands in sequence
                commands_list = content  # This is a list of command dictionaries
                
                # Display all commands first
                self.console.print(Panel(
                    f"[bold blue]⭐ Star Shell wants to execute {len(commands_list)} commands in sequence:[/bold blue]",
                    border_style="blue",
                    padding=(0, 1)
                ))
                
                for i, cmd_info in enumerate(commands_list, 1):
                    self.console.print(f"\n[bold cyan]{i}.[/bold cyan] [white]{cmd_info['command']}[/white]")
                    if cmd_info['description']:
                        self.console.print(f"   [dim]{cmd_info['description']}[/dim]")
                
                # Ask if user wants to execute all commands
                from rich.prompt import Confirm
                if Confirm.ask(f"\n[bold blue]Execute all {len(commands_list)} commands in sequence?[/bold blue]"):
                    
                    # Execute commands one by one
                    all_successful = True
                    execution_results = []
                    
                    for i, cmd_info in enumerate(commands_list, 1):
                        command = cmd_info['command']
                        cmd_description = cmd_info['description']
                        
                        self.console.print(f"\n[bold blue]Executing command {i}/{len(commands_list)}:[/bold blue] [white]{command}[/white]")
                        
                        # Check command safety
                        if not self.executor.check_command_safety(command):
                            self.console.print(f"[yellow]Command {i} cancelled due to safety concerns.[/yellow]")
                            all_successful = False
                            break
                        
                        # Execute the command
                        return_code, stdout, stderr = self.executor.execute_command(command)
                        self.executor.display_execution_result(return_code, stdout, stderr)
                        
                        # Track command execution
                        self.commands_executed += 1
                        if return_code == 0:
                            self.successful_commands += 1
                        
                        # Track results
                        execution_results.append({
                            'command': command,
                            'return_code': return_code,
                            'stdout': stdout[:200],
                            'stderr': stderr[:200]
                        })
                        
                        if return_code != 0:
                            self.console.print(f"[red]Command {i} failed. Stopping execution sequence.[/red]")
                            all_successful = False
                            break
                        
                        # Small delay between commands
                        import time
                        time.sleep(0.5)
                    
                    # Add execution summary to history
                    if all_successful:
                        self.add_to_history("system", f"Successfully executed {len(commands_list)} commands in sequence")
                        self.console.print(f"\n[green]✅ All {len(commands_list)} commands executed successfully![/green]")
                    else:
                        failed_at = len(execution_results)
                        self.add_to_history("system", f"Command sequence failed at step {failed_at}")
                        self.console.print(f"\n[red]❌ Command sequence stopped at step {failed_at}[/red]")
                    
                    # Add to conversation history
                    commands_summary = "; ".join([cmd['command'] for cmd in commands_list])
                    self.add_to_history("assistant", f"Commands: {commands_summary}")
                    
                else:
                    self.console.print("[yellow]Command sequence cancelled by user.[/yellow]")
                    
            elif response_type == "plan":
                # AI created a step-by-step plan (Gemini Thinking mode)
                plan_info = content
                plan_steps = plan_info["plan"]
                
                # Display the plan
                self.console.print(Panel(
                    plan_info["description"],
                    title="[bold blue]⭐ Execution Plan Created[/bold blue]",
                    border_style="blue",
                    padding=(0, 1)
                ))
                
                # Ask if user wants to start execution
                from rich.prompt import Confirm
                if Confirm.ask(f"\n[bold blue]Start executing this {len(plan_steps)}-step plan?[/bold blue]"):
                    self._execute_thinking_plan(plan_steps, context)
                else:
                    self.console.print("[yellow]Plan execution cancelled by user.[/yellow]")
                    # Reset the plan in the genie
                    if hasattr(self.genie, 'reset_plan'):
                        self.genie.reset_plan()
                    
            elif response_type == "text":
                # AI is responding with natural language
                self.add_to_history("assistant", content)
                
                self.console.print(Panel(
                    content,
                    title="[bold green]⭐ Star Shell[/bold green]",
                    border_style="green",
                    padding=(0, 1)
                ))
            
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")
        
        # Restore from temporary mode if active
        self._restore_from_temporary_mode()
        
        return True
    
    def display_welcome(self):
        """Display welcome message for the interactive terminal."""
        # Get current mode information
        current_mode = self.mode_manager.get_current_mode()
        display_name = self.mode_manager.get_mode_display_name(current_mode)
        
        welcome_text = Text()
        welcome_text.append("⭐ Welcome to Star Shell Interactive Terminal!\n\n", style="bold blue")
        
        # Show current AI backend
        welcome_text.append("Current AI Backend: ", style="white")
        welcome_text.append(f"{display_name}\n\n", style="bold green")
        
        welcome_text.append("I'm your AI assistant for command line tasks. You can:\n", style="white")
        welcome_text.append("• Ask me to run commands: ", style="cyan")
        welcome_text.append("'list all Python files'\n", style="white")
        welcome_text.append("• Request multiple commands: ", style="cyan")
        welcome_text.append("'create a directory and navigate to it'\n", style="white")
        welcome_text.append("• Use adaptive planning: ", style="cyan")
        welcome_text.append("'set up a new Python project' (with Gemini Thinking)\n", style="white")
        welcome_text.append("• Have conversations: ", style="cyan")
        welcome_text.append("'What's the difference between git merge and rebase?'\n", style="white")
        welcome_text.append("• Switch AI backends: ", style="cyan")
        welcome_text.append("'mode' or '/gpt', '/gemini', '/thinking'\n", style="white")
        welcome_text.append("• Get help: ", style="cyan")
        welcome_text.append("'help'\n", style="white")
        welcome_text.append("• Exit: ", style="cyan")
        welcome_text.append("'exit' or Ctrl+C\n\n", style="white")
        welcome_text.append("I'll automatically detect if you need a command or just want to chat!", style="yellow")
        
        self.console.print(Panel(
            welcome_text,
            title="[bold blue]⭐ Star Shell Terminal[/bold blue]",
            border_style="blue",
            padding=(1, 2)
        ))
    
    def display_help(self):
        """
        Display comprehensive help information including mode switching commands.
        
        Shows all available commands, mode switching options, and usage examples
        to help users understand Star Shell's capabilities.
        """
        help_text = Text()
        help_text.append("⭐ Star Shell Help\n\n", style="bold blue")
        
        # Basic Commands Section
        help_text.append("Basic Commands:\n", style="bold white")
        help_text.append("• ", style="cyan")
        help_text.append("help", style="bold cyan")
        help_text.append(" or ", style="white")
        help_text.append("/help", style="bold cyan")
        help_text.append(" - Show this help message\n", style="white")
        help_text.append("• ", style="cyan")
        help_text.append("exit", style="bold cyan")
        help_text.append(" or ", style="white")
        help_text.append("quit", style="bold cyan")
        help_text.append(" - Exit Star Shell (or use Ctrl+C)\n", style="white")
        help_text.append("• ", style="cyan")
        help_text.append("mode", style="bold cyan")
        help_text.append(" or ", style="white")
        help_text.append("/mode", style="bold cyan")
        help_text.append(" - Interactive AI backend selection menu\n", style="white")
        help_text.append("• ", style="cyan")
        help_text.append("status", style="bold cyan")
        help_text.append(" or ", style="white")
        help_text.append("/status", style="bold cyan")
        help_text.append(" - Show current backend and session info\n", style="white")
        help_text.append("• ", style="cyan")
        help_text.append("status detailed", style="bold cyan")
        help_text.append(" - Show comprehensive session statistics\n\n", style="white")
        
        # Mode Switching Section
        help_text.append("AI Backend Switching:\n", style="bold white")
        help_text.append("• ", style="cyan")
        help_text.append("/gpt", style="bold cyan")
        help_text.append(" - Quick switch to OpenAI GPT-3.5 Turbo (fast, reliable)\n", style="white")
        help_text.append("• ", style="cyan")
        help_text.append("/gemini", style="bold cyan")
        help_text.append(" - Show Gemini model selection menu (Pro/Flash/Thinking)\n", style="white")
        help_text.append("• ", style="cyan")
        help_text.append("/flash", style="bold cyan")
        help_text.append(" - Quick switch to Gemini Flash (faster responses)\n", style="white")
        help_text.append("• ", style="cyan")
        help_text.append("/thinking", style="bold cyan")
        help_text.append(" - Quick switch to Gemini Thinking (adaptive planning)\n", style="white")
        help_text.append("• ", style="cyan")
        help_text.append("/secret", style="bold cyan")
        help_text.append(" - Quick switch to Secret Backend (no API key needed)\n", style="white")
        help_text.append("• ", style="cyan")
        help_text.append("/secret-temp", style="bold cyan")
        help_text.append(" - Use secret backend for next query only, then restore current mode\n\n", style="white")
        
        # Mode Switching Tips
        help_text.append("Mode Switching Tips:\n", style="bold yellow")
        help_text.append("• Use ", style="white")
        help_text.append("mode", style="cyan")
        help_text.append(" for interactive selection with descriptions\n", style="white")
        help_text.append("• Quick commands (", style="white")
        help_text.append("/gpt", style="cyan")
        help_text.append(", ", style="white")
        help_text.append("/gemini", style="cyan")
        help_text.append(", etc.) switch instantly if credentials exist\n", style="white")
        help_text.append("• Conversation history is preserved when switching modes\n", style="white")
        help_text.append("• Use ", style="white")
        help_text.append("status", style="cyan")
        help_text.append(" to see your current backend and session stats\n\n", style="white")
        
        # Usage Examples Section
        help_text.append("Usage Examples:\n", style="bold white")
        help_text.append("Single commands:\n", style="bold white")
        help_text.append("• 'create a new directory called projects'\n", style="green")
        help_text.append("• 'show me all running processes'\n", style="green")
        help_text.append("• 'what does the ls command do?'\n", style="green")
        help_text.append("• 'find all Python files in this directory'\n", style="green")
        help_text.append("\nMultiple commands:\n", style="bold white")
        help_text.append("• 'create a directory and navigate to it'\n", style="green")
        help_text.append("• 'install dependencies and run the project'\n", style="green")
        help_text.append("• 'backup my files and clean up temp files'\n", style="green")
        help_text.append("• 'update system packages and restart services'\n", style="green")
        help_text.append("\nAdaptive planning (Gemini Thinking mode):\n", style="bold white")
        help_text.append("• 'set up a complete Python project with tests'\n", style="green")
        help_text.append("• 'deploy my app to production'\n", style="green")
        help_text.append("• 'optimize my system performance'\n", style="green")
        help_text.append("• 'migrate my database and update the schema'\n", style="green")
        help_text.append("\nConversational queries:\n", style="bold white")
        help_text.append("• 'What's the difference between git merge and rebase?'\n", style="green")
        help_text.append("• 'How do I configure SSH keys for GitHub?'\n", style="green")
        help_text.append("• 'Explain Docker containers vs virtual machines'\n", style="green")
        
        # Troubleshooting Section
        help_text.append("\nTroubleshooting:\n", style="bold yellow")
        help_text.append("• If mode switching fails, check your API keys with ", style="white")
        help_text.append("mode", style="cyan")
        help_text.append("\n", style="white")
        help_text.append("• Use ", style="white")
        help_text.append("/secret", style="cyan")
        help_text.append(" if you don't have API keys (hosted backend)\n", style="white")
        help_text.append("• Commands are safety-checked before execution\n", style="white")
        help_text.append("• Press Ctrl+C anytime to interrupt or exit\n", style="white")
        
        self.console.print(Panel(
            help_text,
            title="[bold blue]⭐ Star Shell Help & Commands[/bold blue]",
            border_style="blue",
            padding=(0, 1)
        ))
    
    def start_conversation(self):
        """Start the interactive chat session."""
        self.display_welcome()
        
        while self.running:
            try:
                # Get user input with enhanced prompt
                prompt_text = self.get_enhanced_prompt()
                user_input = Prompt.ask(f"\n{prompt_text}", console=self.console)
                
                if not user_input.strip():
                    continue
                
                # Process the input
                should_continue = self.process_input(user_input)
                
                if not should_continue:
                    break
                    
            except KeyboardInterrupt:
                # Handle Ctrl+C
                self.console.print("\n[yellow]Chat session ended. Goodbye![/yellow]")
                break
            except EOFError:
                # Handle Ctrl+D
                self.console.print("\n[yellow]Chat session ended. Goodbye![/yellow]")
                break
        
        self.console.print("[green]Thanks for using Star Shell![/green]")
    
    def _execute_thinking_plan(self, plan_steps, initial_context):
        """Execute a thinking plan step by step with adaptive execution."""
        from star_shell.backend import GeminiThinkingGenie
        
        if not isinstance(self.genie, GeminiThinkingGenie):
            self.console.print("[red]Error: Thinking plan execution only available with Gemini Thinking mode.[/red]")
            return
        
        self.console.print(f"\n[bold green]🚀 Starting adaptive execution of {len(plan_steps)} steps...[/bold green]")
        
        for step_num in range(len(plan_steps)):
            # Get fresh context for each step
            current_context = self.context_provider.build_context()
            current_context["conversation_history"] = self.conversation_history
            
            self.console.print(f"\n[bold cyan]Step {step_num + 1}/{len(plan_steps)}:[/bold cyan] {plan_steps[step_num]}")
            
            try:
                # Get the next command from the thinking genie
                response_type, command, description = self.genie.execute_next_step(current_context)
                
                if response_type == "command":
                    # Display the command
                    self.console.print(f"[white]Command:[/white] {command}")
                    if description:
                        self.console.print(f"[dim]{description}[/dim]")
                    
                    # Check command safety
                    if not self.executor.check_command_safety(command):
                        self.console.print(f"[red]Step {step_num + 1} cancelled due to safety concerns.[/red]")
                        self.genie.record_execution(command, False, "", "Safety check failed")
                        break
                    
                    # Execute the command
                    return_code, stdout, stderr = self.executor.execute_command(command)
                    
                    # Track command execution
                    self.commands_executed += 1
                    if return_code == 0:
                        self.successful_commands += 1
                    
                    # Display results
                    if return_code == 0:
                        self.console.print(f"[green]✓ Step {step_num + 1} completed successfully[/green]")
                        if stdout.strip():
                            # Show first few lines of output
                            output_preview = stdout.strip().split('\n')[:3]
                            self.console.print(f"[dim]Output: {' | '.join(output_preview)}[/dim]")
                        
                        # Record successful execution
                        self.genie.record_execution(command, True, stdout, "")
                    else:
                        self.console.print(f"[red]✗ Step {step_num + 1} failed[/red]")
                        if stderr.strip():
                            self.console.print(f"[red]Error: {stderr.strip()[:200]}[/red]")
                        
                        # Record failed execution
                        self.genie.record_execution(command, False, stdout, stderr)
                        
                        # Ask if user wants to continue despite failure
                        from rich.prompt import Confirm
                        if not Confirm.ask(f"[yellow]Step {step_num + 1} failed. Continue with remaining steps?[/yellow]"):
                            break
                
                elif response_type == "text":
                    # Step completed or informational message
                    self.console.print(f"[green]✓ {command}[/green]")
                
                # Small delay between steps
                import time
                time.sleep(0.5)
                
            except Exception as e:
                self.console.print(f"[red]Error in step {step_num + 1}: {str(e)}[/red]")
                break
        
        # Final summary
        if hasattr(self.genie, 'execution_history') and self.genie.execution_history:
            successful_steps = sum(1 for h in self.genie.execution_history if h['success'])
            total_steps = len(self.genie.execution_history)
            
            if successful_steps == total_steps:
                self.console.print(f"\n[bold green]🎉 Plan completed successfully! All {total_steps} steps executed.[/bold green]")
            else:
                self.console.print(f"\n[yellow]⚠️ Plan partially completed: {successful_steps}/{total_steps} steps successful.[/yellow]")
            
            # Add summary to conversation history
            self.add_to_history("system", f"Executed {successful_steps}/{total_steps} steps of adaptive plan")
        
        # Reset the plan
        self.genie.reset_plan()