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
    

    
    def process_input(self, user_input: str) -> bool:
        """
        Process user input and generate AI response.
        
        Returns:
            True to continue session, False to exit
        """
        # Check for exit commands
        if user_input.lower().strip() in ['exit', 'quit', 'bye', 'goodbye']:
            return False
        
        # Handle help command
        if user_input.lower().strip() == 'help':
            self.display_help()
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
        
        return True
    
    def display_welcome(self):
        """Display welcome message for the interactive terminal."""
        welcome_text = Text()
        welcome_text.append("⭐ Welcome to Star Shell Interactive Terminal!\n\n", style="bold blue")
        welcome_text.append("I'm your AI assistant for command line tasks. You can:\n", style="white")
        welcome_text.append("• Ask me to run commands: ", style="cyan")
        welcome_text.append("'list all Python files'\n", style="white")
        welcome_text.append("• Request multiple commands: ", style="cyan")
        welcome_text.append("'create a directory and navigate to it'\n", style="white")
        welcome_text.append("• Have conversations: ", style="cyan")
        welcome_text.append("'What's the difference between git merge and rebase?'\n", style="white")
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
        """Display help information."""
        help_text = Text()
        help_text.append("⭐ Star Shell Help\n\n", style="bold blue")
        help_text.append("Commands:\n", style="bold white")
        help_text.append("• ", style="cyan")
        help_text.append("help", style="bold cyan")
        help_text.append(" - Show this help message\n", style="white")
        help_text.append("• ", style="cyan")
        help_text.append("exit/quit", style="bold cyan")
        help_text.append(" - Exit Star Shell\n\n", style="white")
        
        help_text.append("Examples:\n", style="bold white")
        help_text.append("Single commands:\n", style="bold white")
        help_text.append("• 'create a new directory called projects'\n", style="green")
        help_text.append("• 'show me all running processes'\n", style="green")
        help_text.append("• 'what does the ls command do?'\n", style="green")
        help_text.append("\nMultiple commands:\n", style="bold white")
        help_text.append("• 'create a directory and navigate to it'\n", style="green")
        help_text.append("• 'install dependencies and run the project'\n", style="green")
        help_text.append("• 'backup my files and clean up temp files'\n", style="green")
        
        self.console.print(Panel(
            help_text,
            title="[bold blue]Help[/bold blue]",
            border_style="blue",
            padding=(0, 1)
        ))
    
    def start_conversation(self):
        """Start the interactive chat session."""
        self.display_welcome()
        
        while self.running:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold blue]⭐[/bold blue]", console=self.console)
                
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