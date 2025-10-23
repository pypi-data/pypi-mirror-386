import platform
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any
import typer
from star_shell.backend import OpenAIGenie, GeminiGenie, GeminiThinkingGenie, ProxyGenie
from star_shell.security import secure_storage


def get_os_info():
    oper_sys = platform.system()
    if oper_sys == "Windows" or oper_sys == "Darwin":
        oper_sys = "MacOS" if oper_sys == "Darwin" else "Windows"
        return (oper_sys, platform.platform(aliased=True, terse=True))
    if oper_sys == "Linux":
        return (oper_sys, platform.freedesktop_os_release()["PRETTY_NAME"])
    return (None, None)


def get_config_path() -> Path:
    """Get the path to the configuration file."""
    APP_NAME = ".star_shell"
    app_dir = typer.get_app_dir(APP_NAME)
    return Path(app_dir) / "config.json"


def get_backup_config_path() -> Path:
    """Get the path to the backup configuration file."""
    APP_NAME = ".star_shell"
    app_dir = typer.get_app_dir(APP_NAME)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path(app_dir) / f"config_backup_{timestamp}.json"


def create_config_backup() -> Optional[Path]:
    """
    Create a backup of the current configuration file.
    
    Returns:
        Path to backup file if successful, None otherwise
    """
    config_path = get_config_path()
    if not config_path.exists():
        return None
    
    try:
        backup_path = get_backup_config_path()
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(config_path, backup_path)
        return backup_path
    except Exception:
        return None


def validate_config_structure(config: Dict[str, Any]) -> bool:
    """
    Validate that a configuration dictionary has the required structure.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ["backend", "os", "os_fullname", "shell"]
    
    # Check required fields exist
    for field in required_fields:
        if field not in config:
            return False
    
    # Validate backend-specific requirements
    backend = config.get("backend")
    if backend == "openai-gpt-3.5-turbo":
        if "openai_api_key" not in config or not config["openai_api_key"]:
            return False
    elif backend in ["gemini-pro", "gemini-flash", "gemini-thinking"]:
        if "gemini_api_key" not in config or not config["gemini_api_key"]:
            return False
    elif backend == "secret-3.14159":
        required_secret_fields = ["backend_url", "secret_token", "model_type"]
        for field in required_secret_fields:
            if field not in config or not config[field]:
                return False
    else:
        # Unknown backend
        return False
    
    return True


def load_config():
    """Load and decrypt configuration from the config file."""
    config_path = get_config_path()
    
    if not config_path.exists():
        raise FileNotFoundError("Configuration file not found. Please run 'star-shell init' first.")
    
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        
        # Validate configuration structure
        if not validate_config_structure(config):
            raise ValueError("Invalid configuration structure")
        
        # Decrypt API keys if they exist and are encrypted
        if "openai_api_key" in config and config["openai_api_key"]:
            try:
                config["openai_api_key"] = secure_storage.decrypt_api_key(config["openai_api_key"])
            except Exception:
                # If decryption fails, assume it's already decrypted (for backward compatibility)
                pass
        
        if "gemini_api_key" in config and config["gemini_api_key"]:
            try:
                config["gemini_api_key"] = secure_storage.decrypt_api_key(config["gemini_api_key"])
            except Exception:
                # If decryption fails, assume it's already decrypted (for backward compatibility)
                pass
        
        return config
        
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"Invalid configuration file: {e}")


def save_config(config: Dict[str, Any], create_backup: bool = True) -> bool:
    """
    Save configuration to file with validation and backup.
    
    Args:
        config: Configuration dictionary to save
        create_backup: Whether to create a backup before saving
        
    Returns:
        True if successful, False otherwise
    """
    # Validate configuration before saving
    if not validate_config_structure(config):
        raise ValueError("Invalid configuration structure")
    
    config_path = get_config_path()
    
    # Create backup if requested and config exists
    backup_path = None
    if create_backup and config_path.exists():
        backup_path = create_config_backup()
    
    try:
        # Create a copy for encryption
        config_to_save = config.copy()
        
        # Encrypt API keys before saving
        if "openai_api_key" in config_to_save and config_to_save["openai_api_key"]:
            config_to_save["openai_api_key"] = secure_storage.encrypt_api_key(config_to_save["openai_api_key"])
        
        if "gemini_api_key" in config_to_save and config_to_save["gemini_api_key"]:
            config_to_save["gemini_api_key"] = secure_storage.encrypt_api_key(config_to_save["gemini_api_key"])
        
        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write configuration
        with open(config_path, "w") as f:
            json.dump(config_to_save, f, indent=2)
        
        return True
        
    except Exception as e:
        # If save failed and we created a backup, try to restore it
        if backup_path and backup_path.exists():
            try:
                shutil.copy2(backup_path, config_path)
            except Exception:
                pass  # Restoration failed, but original error is more important
        
        raise ValueError(f"Failed to save configuration: {e}")


def update_config_runtime(updates: Dict[str, Any], validate_backend: bool = True) -> bool:
    """
    Update configuration at runtime with validation and rollback capability.
    
    Args:
        updates: Dictionary of configuration updates to apply
        validate_backend: Whether to validate the backend after updates
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Load current configuration
        current_config = load_config()
        
        # Create backup
        backup_path = create_config_backup()
        
        # Apply updates
        updated_config = current_config.copy()
        updated_config.update(updates)
        
        # Validate updated configuration
        if not validate_config_structure(updated_config):
            raise ValueError("Updated configuration would be invalid")
        
        # If backend validation is requested, test the new backend
        if validate_backend and "backend" in updates:
            try:
                # Test backend creation with new config
                test_backend = get_backend(**updated_config)
                # For some backends, we can validate credentials
                if hasattr(test_backend, 'validate_credentials'):
                    if not test_backend.validate_credentials():
                        raise ValueError("Backend credentials validation failed")
            except Exception as e:
                raise ValueError(f"Backend validation failed: {e}")
        
        # Save updated configuration
        save_config(updated_config, create_backup=False)  # We already created a backup
        
        return True
        
    except Exception as e:
        # If we created a backup and something failed, we could restore it here
        # For now, we'll just re-raise the error
        raise e


def get_legacy_config_migration_needed() -> bool:
    """
    Check if configuration needs migration from legacy format.
    
    Returns:
        True if migration is needed, False otherwise
    """
    try:
        config_path = get_config_path()
        if not config_path.exists():
            return False
        
        with open(config_path, "r") as f:
            config = json.load(f)
        
        # Check for legacy indicators
        # 1. Missing required fields that were added later
        required_fields = ["backend", "os", "os_fullname", "shell"]
        for field in required_fields:
            if field not in config:
                return True
        
        # 2. Check for old backend names or formats
        backend = config.get("backend")
        if backend and backend not in ["openai-gpt-3.5-turbo", "gemini-pro", "gemini-flash", "gemini-thinking", "secret-3.14159"]:
            return True
        
        # 3. Check for unencrypted API keys (legacy format)
        # If API keys exist but are not encrypted (don't start with expected prefix)
        if "openai_api_key" in config and config["openai_api_key"]:
            try:
                # Try to decrypt - if it fails, it might be unencrypted
                secure_storage.decrypt_api_key(config["openai_api_key"])
            except Exception:
                # Could be unencrypted legacy format
                if not config["openai_api_key"].startswith("gAAAAAB"):  # Fernet token prefix
                    return True
        
        if "gemini_api_key" in config and config["gemini_api_key"]:
            try:
                secure_storage.decrypt_api_key(config["gemini_api_key"])
            except Exception:
                if not config["gemini_api_key"].startswith("gAAAAAB"):
                    return True
        
        return False
        
    except (json.JSONDecodeError, FileNotFoundError):
        return False


def ensure_config_compatibility() -> bool:
    """
    Ensure configuration is compatible with current version.
    
    Returns:
        True if configuration is compatible or was successfully updated
    """
    try:
        config_path = get_config_path()
        if not config_path.exists():
            return True  # No config to check
        
        # Load and validate current configuration
        config = load_config()
        
        # Check if all required fields are present
        required_fields = ["backend", "os", "os_fullname", "shell"]
        missing_fields = [field for field in required_fields if field not in config]
        
        if missing_fields:
            # Add missing fields with sensible defaults
            if "os" in missing_fields or "os_fullname" in missing_fields:
                os_family, os_fullname = get_os_info()
                config["os"] = os_family or "Unknown"
                config["os_fullname"] = os_fullname or "Unknown OS"
            
            if "shell" in missing_fields:
                import os
                shell_str = os.environ.get("SHELL", "")
                if "bash" in shell_str:
                    config["shell"] = "bash"
                elif "zsh" in shell_str:
                    config["shell"] = "zsh"
                elif "fish" in shell_str:
                    config["shell"] = "fish"
                else:
                    config["shell"] = "bash"
            
            # Save updated configuration
            save_config(config, create_backup=True)
        
        return True
        
    except Exception:
        return False


def migrate_legacy_config() -> bool:
    """
    Migrate configuration from legacy format to current format.
    
    Returns:
        True if migration successful, False otherwise
    """
    try:
        config_path = get_config_path()
        if not config_path.exists():
            return False
        
        # Create backup before migration
        backup_path = create_config_backup()
        if not backup_path:
            return False
        
        with open(config_path, "r") as f:
            config = json.load(f)
        
        # Migrate backend names
        backend = config.get("backend")
        if backend:
            # Map old backend names to new ones
            backend_mapping = {
                "openai": "openai-gpt-3.5-turbo",
                "gpt": "openai-gpt-3.5-turbo",
                "gemini": "gemini-pro",
                "thinking": "gemini-thinking",
                "secret": "secret-3.14159"
            }
            
            if backend in backend_mapping:
                config["backend"] = backend_mapping[backend]
        
        # Add missing required fields with defaults
        if "os" not in config:
            os_family, os_fullname = get_os_info()
            config["os"] = os_family or "Unknown"
            config["os_fullname"] = os_fullname or "Unknown OS"
        
        if "shell" not in config:
            import os
            shell_str = os.environ.get("SHELL", "")
            if "bash" in shell_str:
                config["shell"] = "bash"
            elif "zsh" in shell_str:
                config["shell"] = "zsh"
            elif "fish" in shell_str:
                config["shell"] = "fish"
            else:
                config["shell"] = "bash"  # Default
        
        # Encrypt unencrypted API keys
        if "openai_api_key" in config and config["openai_api_key"]:
            try:
                # Try to decrypt - if it fails, it's probably unencrypted
                secure_storage.decrypt_api_key(config["openai_api_key"])
            except Exception:
                # Encrypt the unencrypted key
                config["openai_api_key"] = secure_storage.encrypt_api_key(config["openai_api_key"])
        
        if "gemini_api_key" in config and config["gemini_api_key"]:
            try:
                secure_storage.decrypt_api_key(config["gemini_api_key"])
            except Exception:
                config["gemini_api_key"] = secure_storage.encrypt_api_key(config["gemini_api_key"])
        
        # Validate migrated configuration
        if not validate_config_structure(config):
            # Restore backup if validation fails
            shutil.copy2(backup_path, config_path)
            return False
        
        # Save migrated configuration
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        
        return True
        
    except Exception:
        # Restore backup on any error
        if backup_path and backup_path.exists():
            try:
                shutil.copy2(backup_path, config_path)
            except Exception:
                pass
        return False


def get_backend(**config: dict):
    backend_name = config["backend"]
    if backend_name == "openai-gpt-3.5-turbo":
        return OpenAIGenie(
            api_key=config["openai_api_key"],
            os_fullname=config["os_fullname"],
            shell=config["shell"],
        )

    elif backend_name == "secret-3.14159":
        return ProxyGenie(
            backend_url=config["backend_url"],
            secret_token=config["secret_token"],
            os_fullname=config["os_fullname"],
            shell=config["shell"],
            model_type=config["model_type"],
        )
    elif backend_name == "gemini-thinking":
        return GeminiThinkingGenie(
            api_key=config["gemini_api_key"],
            os_fullname=config["os_fullname"],
            shell=config["shell"],
        )
    elif backend_name in ["gemini-pro", "gemini-flash"]:
        return GeminiGenie(
            api_key=config["gemini_api_key"],
            os_fullname=config["os_fullname"],
            shell=config["shell"],
            backend_type=backend_name,
        )
    else:
        raise ValueError(f"Unknown backend: {backend_name}")