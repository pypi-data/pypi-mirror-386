import json
import os
import subprocess
from pathlib import Path

import pyperclip
import typer
from rich import print
from rich.prompt import Confirm, Prompt

from star_shell.utils import get_backend, get_os_info, load_config, save_config, get_legacy_config_migration_needed, migrate_legacy_config
from star_shell.security import secure_storage
from star_shell.context import ContextProvider
from star_shell.command_executor import CommandExecutor
from star_shell.session_manager import SessionManager

APP_NAME = ".star_shell"
app = typer.Typer()

def check_initialization():
    """Check if Star Shell has been initialized."""
    try:
        config = load_config()
        
        # Check if migration is needed
        if get_legacy_config_migration_needed():
            print("[yellow]Migrating configuration to new format...[/yellow]")
            if migrate_legacy_config():
                print("[green]Configuration migrated successfully.[/green]")
            else:
                print("[red]Configuration migration failed.[/red]")
                return False
        
        return True
    except FileNotFoundError:
        return False
    except ValueError as e:
        print(f"[red]Configuration error: {e}[/red]")
        print("[yellow]You may need to run 'star-shell init' to fix the configuration.[/yellow]")
        return False

def require_initialization():
    """Ensure Star Shell is initialized before running commands."""
    if not check_initialization():
        print("[red]⚠️  Star Shell is not initialized![/red]")
        print("[yellow]Please run 'star-shell init' first to set up your AI backend.[/yellow]")
        raise typer.Exit(1)


@app.command()
def init():

    # Allow hidden option for secret backend
    print("Select backend:")
    print("1. openai-gpt-3.5-turbo")
    print("2. gemini-pro") 
    print("3. gemini-flash")
    print("4. gemini-thinking (adaptive multi-step execution)")
    
    backend_input = Prompt.ask("Enter your choice (1-4 or backend name)")
    
    # Map choices
    backend_map = {
        "1": "openai-gpt-3.5-turbo",
        "2": "gemini-pro",
        "3": "gemini-flash",
        "4": "gemini-thinking",
        "openai-gpt-3.5-turbo": "openai-gpt-3.5-turbo",
        "gemini-pro": "gemini-pro",
        "gemini-flash": "gemini-flash",
        "gemini-thinking": "gemini-thinking",
        "secret-3.14159": "secret-3.14159"  # Hidden option
    }
    
    backend = backend_map.get(backend_input)
    if not backend:
        print("[red]Invalid backend selection.[/red]")
        return
    additional_params = {}

    if backend == "openai-gpt-3.5-turbo":
        openai_api_key = Prompt.ask("Enter a OpenAI API key")
        # Encrypt the API key before storing
        additional_params["openai_api_key"] = secure_storage.encrypt_api_key(openai_api_key)

    if backend == "secret-3.14159":
        print("[green]🎉 Secret backend activated! Using shared Gemini keys.[/green]")
        
        # Ask for model preference
        model_choice = Prompt.ask(
            "Select model:", 
            choices=["gemini-pro", "gemini-flash"],
            default="gemini-pro"
        )
        
        # Default backend URL - replace with your deployed Vercel URL
        backend_url = "https://star-shell-backend.vercel.app/"  # Replace with your actual Vercel URL
        
        # Test connection to proxy service
        print("[yellow]Testing connection to Star Shell backend...[/yellow]")
        try:
            from star_shell.backend import ProxyGenie
            test_genie = ProxyGenie(backend_url, "secret-3.14159", "test", "test", model_choice)
            if test_genie.validate_credentials():
                print("[green]✓ Connected to Star Shell backend successfully[/green]")
                additional_params["backend_url"] = backend_url
                additional_params["secret_token"] = "secret-3.14159"
                additional_params["model_type"] = model_choice
            else:
                print("[red]✗ Could not connect to Star Shell backend. Please try again later.[/red]")
                return
        except Exception as e:
            print(f"[red]✗ Error connecting to Star Shell backend: {e}[/red]")
            return
            
    elif backend in ["gemini-pro", "gemini-flash", "gemini-thinking"]:
        if backend == "gemini-pro":
            model_name = "Gemini Pro"
        elif backend == "gemini-flash":
            model_name = "Gemini Flash"
        else:
            model_name = "Gemini Thinking (Adaptive)"
        
        gemini_api_key = Prompt.ask(f"Enter a {model_name} API key")
        
        # Basic API key validation for Gemini
        print(f"[yellow]Validating {model_name} API key...[/yellow]")
        try:
            from star_shell.backend import GeminiGenie
            # Pass the backend type to determine which model to use
            test_genie = GeminiGenie(gemini_api_key, "test", "test", backend)
            if test_genie.validate_credentials():
                print(f"[green]✓ {model_name} API key is valid[/green]")
                # Encrypt the API key before storing
                additional_params["gemini_api_key"] = secure_storage.encrypt_api_key(gemini_api_key)
            else:
                print(f"[red]✗ Invalid {model_name} API key. Please check your key and try again.[/red]")
                return
        except Exception as e:
            print(f"[red]✗ Error validating {model_name} API key: {e}[/red]")
            return


    os_family, os_fullname = get_os_info()

    if os_family:
        if not Confirm.ask(f"Is your OS {os_fullname}?"):
            os_fullname = Prompt.ask("What is your OS and version? (e.g. MacOS 13.1)")
    else:
        os_fullname = Prompt.ask("What is your OS and version? (e.g. MacOS 13.1)")

    if os_family == "Windows":
        shell = Prompt.ask(
            "What shell are you using?",
            choices=["cmd", "powershell"],
        )

    if os_family in ("Linux", "MacOS"):
        shell_str = os.environ.get("SHELL") or ""
        if "bash" in shell_str:
            shell = "bash"
        elif "zsh" in shell_str:
            shell = "zsh"
        elif "fish" in shell_str:
            shell = "fish"
        else:
            typer.prompt("What shell are you using?")

    config = {
        "backend": backend,
        "os": os_family,
        "os_fullname": os_fullname,
        "shell": shell,
    } | additional_params

    app_dir = typer.get_app_dir(APP_NAME)
    config_path: Path = Path(app_dir) / "config.json"

    print("The following configuration will be saved:")
    print(config)

    # Check if config already exists
    from star_shell.utils import get_config_path
    config_path = get_config_path()
    
    if config_path.exists():
        overwrite = Confirm.ask(
            "A config file already exists. Do you want to overwrite it?"
        )
        if not overwrite:
            print("Did not overwrite config file.")
            return

    # Use the new save_config function for consistency and validation
    try:
        save_config(config, create_backup=False)  # No backup needed for init
        print(f"[bold green]Config file saved at {config_path}[/bold green]")
    except ValueError as e:
        print(f"[red]Error saving configuration: {e}[/red]")
        return


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Star Shell - AI-powered command line assistant."""
    if ctx.invoked_subcommand is None:
        # No subcommand provided, check if initialized
        if not check_initialization():
            print("[bold blue]⭐ Welcome to Star Shell![/bold blue]")
            print("[yellow]You need to initialize Star Shell first.[/yellow]")
            print("[cyan]Run: star-shell init[/cyan]")
            raise typer.Exit(1)
        else:
            # Already initialized, show status
            try:
                config = load_config()
                current_mode = config.get("backend", "unknown")
                print("[bold blue]⭐ Star Shell is ready![/bold blue]")
                print(f"[dim]Current mode: {current_mode}[/dim]")
                print()
                print("[cyan]Commands:[/cyan]")
                print("  [white]star-shell run[/white]  - Start interactive terminal")
                print("  [white]star-shell mode[/white] - Switch AI backend/mode")
                print("  [white]star-shell --help[/white] - Show all options")
            except Exception:
                print("[bold blue]⭐ Star Shell is ready![/bold blue]")
                print("[cyan]Run: star-shell run[/cyan] to start the interactive terminal")
                print("[cyan]Run: star-shell --help[/cyan] for more options")

@app.command()
def ask(
    wish: str = typer.Argument(..., help="What do you want to do?"),
    explain: bool = False,
):
    """Ask Star Shell to generate a specific command."""
    require_initialization()
    
    config = load_config()

    # Create context provider and gather context
    context_provider = ContextProvider()
    context = context_provider.build_context()

    genie = get_backend(**config)
    try:
        command, description = genie.ask(wish, explain, context)
    except Exception as e:
        print(f"[red]Error: {e}[/red]")
        return

    # Create command executor for enhanced display and execution
    executor = CommandExecutor()

    if config["os"] == "Windows" and config["shell"] == "powershell":
        # For PowerShell, just display and copy to clipboard
        executor.display_command(command, description)
        pyperclip.copy(command)
        print("[green]Command copied to clipboard.[/green]")
    else:
        # For other systems, use the enhanced execution flow
        command_executed = executor.handle_command_execution(command, description)
        
        # Send feedback to the backend (currently only used by some backends)
        genie.post_execute(
            wish=wish,
            explain=explain,
            command=command,
            description=description,
            feedback=False,
        )


@app.command()
def run():
    """Start the Star Shell interactive terminal."""
    require_initialization()
    
    config = load_config()

    # Create context provider and genie
    context_provider = ContextProvider()
    genie = get_backend(**config)
    
    # Create and start session manager
    session_manager = SessionManager(genie, context_provider)
    session_manager.start_conversation()

@app.command()
def mode():
    """Switch between different AI backends/modes."""
    # Check if Star Shell is initialized
    if not check_initialization():
        print("[red]⚠️  Star Shell is not initialized![/red]")
        print("[yellow]Please run 'star-shell init' first to set up your AI backend.[/yellow]")
        raise typer.Exit(1)
    
    # Ensure backward compatibility by checking for any configuration issues
    try:
        current_config = load_config()
    except ValueError as e:
        print(f"[red]Configuration error: {e}[/red]")
        print("[yellow]Your configuration may be corrupted. Consider running 'star-shell init' to reset it.[/yellow]")
        raise typer.Exit(1)
    
    # Load current config (already validated above)
    current_backend = current_config.get("backend", "unknown")
    print(f"[blue]Current mode: {current_backend}[/blue]")
    print()
    
    # Show available modes
    print("Available modes:")
    print("1. openai-gpt-3.5-turbo")
    print("2. gemini-pro") 
    print("3. gemini-flash")
    print("4. gemini-thinking (adaptive multi-step execution)")
    print("5. Keep current mode")
    
    backend_input = Prompt.ask("Select new mode (1-5 or mode name)")
    
    # Map choices
    backend_map = {
        "1": "openai-gpt-3.5-turbo",
        "2": "gemini-pro",
        "3": "gemini-flash",
        "4": "gemini-thinking",
        "5": current_backend,
        "openai-gpt-3.5-turbo": "openai-gpt-3.5-turbo",
        "gemini-pro": "gemini-pro",
        "gemini-flash": "gemini-flash",
        "gemini-thinking": "gemini-thinking",
        "secret-3.14159": "secret-3.14159"  # Hidden option
    }
    
    new_backend = backend_map.get(backend_input)
    if not new_backend:
        print("[red]Invalid mode selection.[/red]")
        return
    
    if new_backend == current_backend:
        print(f"[green]Already using {current_backend}. No changes made.[/green]")
        return
    
    # Handle different backend types
    additional_params = {}
    
    if new_backend == "openai-gpt-3.5-turbo":
        # Check if we already have an OpenAI key
        if "openai_api_key" in current_config and current_config["openai_api_key"]:
            use_existing = Confirm.ask("Use existing OpenAI API key?")
            if use_existing:
                additional_params["openai_api_key"] = current_config["openai_api_key"]
            else:
                openai_api_key = Prompt.ask("Enter a new OpenAI API key")
                additional_params["openai_api_key"] = secure_storage.encrypt_api_key(openai_api_key)
        else:
            openai_api_key = Prompt.ask("Enter an OpenAI API key")
            additional_params["openai_api_key"] = secure_storage.encrypt_api_key(openai_api_key)
    
    elif new_backend == "secret-3.14159":
        print("[green]🎉 Secret backend activated! Using shared Gemini keys.[/green]")
        
        # Ask for model preference
        model_choice = Prompt.ask(
            "Select model:", 
            choices=["gemini-pro", "gemini-flash"],
            default="gemini-pro"
        )
        
        backend_url = "https://star-shell-backend.vercel.app/"
        
        # Test connection to proxy service
        print("[yellow]Testing connection to Star Shell backend...[/yellow]")
        try:
            from star_shell.backend import ProxyGenie
            test_genie = ProxyGenie(backend_url, "secret-3.14159", "test", "test", model_choice)
            if test_genie.validate_credentials():
                print("[green]✓ Connected to Star Shell backend successfully[/green]")
                additional_params["backend_url"] = backend_url
                additional_params["secret_token"] = "secret-3.14159"
                additional_params["model_type"] = model_choice
            else:
                print("[red]✗ Could not connect to Star Shell backend. Please try again later.[/red]")
                return
        except Exception as e:
            print(f"[red]✗ Error connecting to Star Shell backend: {e}[/red]")
            return
            
    elif new_backend in ["gemini-pro", "gemini-flash", "gemini-thinking"]:
        # Special case: If currently using secret backend, offer to stay on secret backend
        if current_backend == "secret-3.14159":
            use_secret = Confirm.ask(
                f"[bold blue]Stay on secret backend and use {new_backend.replace('-', ' ').title()}?[/bold blue]",
                default=True
            )
            if use_secret:
                # Use secret backend with the new model type
                additional_params["backend_url"] = current_config.get("backend_url", "https://star-shell-backend.vercel.app/")
                additional_params["secret_token"] = current_config.get("secret_token", "secret-3.14159")
                additional_params["model_type"] = new_backend
                # Override the backend to stay as secret
                new_backend = "secret-3.14159"
            else:
                # User wants to switch to real Gemini backend, ask for API key
                gemini_api_key = Prompt.ask("Enter a Gemini API key")
                additional_params["gemini_api_key"] = secure_storage.encrypt_api_key(gemini_api_key)
        else:
            # Check if we already have a Gemini key
            if "gemini_api_key" in current_config and current_config["gemini_api_key"]:
                use_existing = Confirm.ask("Use existing Gemini API key?")
                if use_existing:
                    additional_params["gemini_api_key"] = current_config["gemini_api_key"]
                else:
                    gemini_api_key = Prompt.ask("Enter a new Gemini API key")
                    additional_params["gemini_api_key"] = secure_storage.encrypt_api_key(gemini_api_key)
            else:
                gemini_api_key = Prompt.ask("Enter a Gemini API key")
                additional_params["gemini_api_key"] = secure_storage.encrypt_api_key(gemini_api_key)
    
    # Update configuration
    updated_config = current_config.copy()
    updated_config["backend"] = new_backend
    updated_config.update(additional_params)
    
    # Remove old API keys if switching backend types
    if new_backend.startswith("openai") and "gemini_api_key" in updated_config:
        del updated_config["gemini_api_key"]
    elif new_backend.startswith("gemini") and "openai_api_key" in updated_config:
        del updated_config["openai_api_key"]
    elif new_backend == "secret-3.14159":
        # Remove both API keys for secret backend
        updated_config.pop("openai_api_key", None)
        updated_config.pop("gemini_api_key", None)
    
    # Use the new save_config function for consistency and validation
    try:
        save_config(updated_config, create_backup=True)
    except ValueError as e:
        print(f"[red]Error saving configuration: {e}[/red]")
        return
    
    print(f"[bold green]✓ Successfully switched to {new_backend} mode![/bold green]")
    print(f"[cyan]You can now use 'star-shell run' with the new backend.[/cyan]")

@app.command()
def chat():
    """Legacy command - use 'run' instead."""
    print("[yellow]The 'chat' command is deprecated. Use 'star-shell run' instead.[/yellow]")
    run()


if __name__ == "__main__":
    app()