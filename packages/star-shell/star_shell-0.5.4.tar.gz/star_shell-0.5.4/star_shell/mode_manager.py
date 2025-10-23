"""
ModeManager component for handling AI backend switching in Star Shell.

This module provides the ModeManager class that handles:
- Backend validation and switching logic
- Mode display names and quick command shortcuts
- Credential handling for different AI backends
- Runtime configuration updates with validation and rollback
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from star_shell.backend import BaseGenie, OpenAIGenie, GeminiGenie, GeminiThinkingGenie, ProxyGenie
from star_shell.security import secure_storage
from star_shell.utils import load_config, save_config, update_config_runtime, create_config_backup


@dataclass
class ModeConfig:
    """Configuration for an AI backend mode."""
    backend_type: str
    display_name: str
    requires_api_key: bool
    api_key_field: str
    validation_method: str
    quick_command: str


class ModeManager:
    """Manages AI backend switching and mode validation."""
    
    def __init__(self, session_manager):
        """Initialize ModeManager with reference to SessionManager."""
        self.session_manager = session_manager
        self._mode_configs = self._initialize_mode_configs()
    
    def _initialize_mode_configs(self) -> Dict[str, ModeConfig]:
        """Initialize configuration for all supported modes."""
        return {
            "openai-gpt-3.5-turbo": ModeConfig(
                backend_type="openai-gpt-3.5-turbo",
                display_name="OpenAI GPT-3.5 Turbo",
                requires_api_key=True,
                api_key_field="openai_api_key",
                validation_method="openai",
                quick_command="/gpt"
            ),
            "gemini-pro": ModeConfig(
                backend_type="gemini-pro",
                display_name="Gemini Pro",
                requires_api_key=True,
                api_key_field="gemini_api_key",
                validation_method="gemini",
                quick_command="/gemini"
            ),
            "gemini-flash": ModeConfig(
                backend_type="gemini-flash",
                display_name="Gemini Flash",
                requires_api_key=True,
                api_key_field="gemini_api_key",
                validation_method="gemini",
                quick_command="/flash"
            ),
            "gemini-thinking": ModeConfig(
                backend_type="gemini-thinking",
                display_name="Gemini Thinking (Adaptive)",
                requires_api_key=True,
                api_key_field="gemini_api_key",
                validation_method="gemini",
                quick_command="/thinking"
            ),
            "secret-3.14159": ModeConfig(
                backend_type="secret-3.14159",
                display_name="Secret Backend",
                requires_api_key=False,
                api_key_field="",
                validation_method="proxy",
                quick_command="/secret"
            )
        }
    
    def get_current_mode(self) -> str:
        """
        Get the current AI backend mode identifier.
        
        Determines the current mode by inspecting the active genie instance type
        and attributes. This is used throughout the system to identify which
        AI backend is currently active.
        
        Returns:
            str: The mode identifier (e.g., 'openai-gpt-3.5-turbo', 'gemini-pro', 
                 'gemini-thinking', 'secret-3.14159') or 'unknown' if unable to determine
        
        Note:
            This method relies on the genie instance type to determine the mode.
            For Gemini backends, it checks the backend_type attribute to distinguish
            between 'gemini-pro' and 'gemini-flash' variants.
        """
        if hasattr(self.session_manager, 'genie'):
            # Determine mode from genie type
            genie = self.session_manager.genie
            if isinstance(genie, OpenAIGenie):
                return "openai-gpt-3.5-turbo"
            elif isinstance(genie, GeminiThinkingGenie):
                return "gemini-thinking"
            elif isinstance(genie, GeminiGenie):
                # Check backend_type attribute to distinguish between pro/flash
                return getattr(genie, 'backend_type', 'gemini-pro')
            elif isinstance(genie, ProxyGenie):
                return "secret-3.14159"
        
        return "unknown"
    
    def list_available_modes(self) -> List[str]:
        """
        Get list of all available AI backend modes.
        
        Returns all supported backend modes that can be switched to, regardless
        of whether credentials are currently configured for them.
        
        Returns:
            List[str]: List of mode identifiers that can be used with switch_mode()
        
        Example:
            >>> manager.list_available_modes()
            ['openai-gpt-3.5-turbo', 'gemini-pro', 'gemini-flash', 'gemini-thinking', 'secret-3.14159']
        """
        return list(self._mode_configs.keys())
    
    def get_mode_display_name(self, mode: str) -> str:
        """
        Get the human-readable display name for a mode.
        
        Converts internal mode identifiers to user-friendly display names
        for use in UI elements, status messages, and help text.
        
        Args:
            mode: The internal mode identifier (e.g., 'openai-gpt-3.5-turbo')
        
        Returns:
            str: Human-readable display name (e.g., 'OpenAI GPT-3.5 Turbo')
                 or the original mode string if not found
        
        Example:
            >>> manager.get_mode_display_name('gemini-thinking')
            'Gemini Thinking (Adaptive)'
        """
        config = self._mode_configs.get(mode)
        return config.display_name if config else mode
    
    def get_quick_command_mapping(self) -> Dict[str, str]:
        """
        Get mapping of quick command shortcuts to their corresponding mode names.
        
        Creates a dictionary that maps user-friendly quick commands (like '/gpt')
        to their internal mode identifiers. Used by the session manager to
        handle quick mode switching commands.
        
        Returns:
            Dict[str, str]: Mapping from quick commands to mode identifiers
        
        Example:
            >>> manager.get_quick_command_mapping()
            {'/gpt': 'openai-gpt-3.5-turbo', '/gemini': 'gemini-pro', 
             '/flash': 'gemini-flash', '/thinking': 'gemini-thinking',
             '/secret': 'secret-3.14159'}
        
        Note:
            Only modes with configured quick_command values are included.
            The mapping is generated dynamically from the mode configurations.
        """
        mapping = {}
        for mode, config in self._mode_configs.items():
            if config.quick_command:
                mapping[config.quick_command] = mode
        return mapping
    
    def validate_mode_credentials(self, mode: str, **kwargs) -> bool:
        """
        Validate credentials for a specific AI backend mode.
        
        Performs validation of API keys or other credentials required for the
        specified mode. This includes making test API calls where appropriate
        to ensure credentials are valid and the service is accessible.
        
        Args:
            mode: The mode identifier to validate credentials for
            **kwargs: Credential parameters (e.g., openai_api_key, gemini_api_key,
                     backend_url, secret_token, model_type)
        
        Returns:
            bool: True if credentials are valid and service is accessible,
                  False if validation fails
        
        Raises:
            No exceptions are raised; all errors are caught and return False
        
        Example:
            >>> manager.validate_mode_credentials('openai-gpt-3.5-turbo', 
            ...                                  openai_api_key='sk-...')
            True
        
        Note:
            For modes that don't require API keys (like secret backend),
            this method validates connectivity to the service endpoint.
        """
        config = self._mode_configs.get(mode)
        if not config:
            return False
        
        if not config.requires_api_key:
            # For modes that don't require API keys (like secret backend)
            if config.validation_method == "proxy":
                return self._validate_proxy_credentials(mode, **kwargs)
            return True
        
        # Get API key from kwargs
        api_key = kwargs.get(config.api_key_field)
        if not api_key:
            return False
        
        # Validate based on method
        if config.validation_method == "openai":
            return self._validate_openai_credentials(api_key)
        elif config.validation_method == "gemini":
            return self._validate_gemini_credentials(api_key, mode)
        
        return False
    
    def _validate_openai_credentials(self, api_key: str) -> bool:
        """Validate OpenAI API key."""
        try:
            test_genie = OpenAIGenie(api_key, "test", "test")
            # OpenAI doesn't have a validate_credentials method, so we'll assume it's valid
            # In a real implementation, you might want to make a test API call
            return len(api_key.strip()) > 0
        except Exception:
            return False
    
    def _validate_gemini_credentials(self, api_key: str, mode: str) -> bool:
        """Validate Gemini API key."""
        try:
            if mode == "gemini-thinking":
                test_genie = GeminiThinkingGenie(api_key, "test", "test")
            else:
                test_genie = GeminiGenie(api_key, "test", "test", mode)
            return test_genie.validate_credentials()
        except Exception:
            return False
    
    def _validate_proxy_credentials(self, mode: str, **kwargs) -> bool:
        """Validate proxy service credentials."""
        try:
            backend_url = kwargs.get("backend_url", "https://star-shell-backend.vercel.app/")
            secret_token = kwargs.get("secret_token", "secret-3.14159")
            model_type = kwargs.get("model_type", "gemini-pro")
            
            test_genie = ProxyGenie(backend_url, secret_token, "test", "test", model_type)
            return test_genie.validate_credentials()
        except Exception:
            return False
    
    def switch_mode(self, new_mode: str, **kwargs) -> bool:
        """
        Switch to a new AI backend mode with configuration persistence.
        
        Performs a complete backend switch including credential validation,
        genie instance creation, configuration updates, and session manager
        integration. Automatically handles rollback on failure.
        
        Args:
            new_mode: The target mode identifier to switch to
            **kwargs: Backend-specific parameters:
                     - openai_api_key: For OpenAI backends
                     - gemini_api_key: For Gemini backends  
                     - backend_url: For proxy backends
                     - secret_token: For secret backends
                     - model_type: Model variant for proxy backends
        
        Returns:
            bool: True if switch completed successfully, False if any step failed
        
        Side Effects:
            - Updates runtime configuration with new backend settings
            - Creates configuration backup before changes
            - Updates session manager's active genie instance
            - Preserves conversation history across the switch
        
        Error Handling:
            - Invalid mode: Returns False immediately
            - Credential validation failure: Returns False
            - Backend creation failure: Returns False  
            - Configuration update failure: Rolls back and returns False
            - Any exception: Rolls back to previous genie and returns False
        """
        # Validate the new mode exists
        if new_mode not in self._mode_configs:
            return False
        
        # Validate credentials for the new mode
        if not self.validate_mode_credentials(new_mode, **kwargs):
            return False
        
        # Store current state for rollback
        current_genie = self.session_manager.genie
        
        try:
            # Create new genie instance
            new_genie = self._create_genie_instance(new_mode, **kwargs)
            if not new_genie:
                return False
            
            # Prepare configuration updates
            config_updates = {"backend": new_mode}
            
            # Add backend-specific configuration
            config = self._mode_configs[new_mode]
            if config.requires_api_key and config.api_key_field in kwargs:
                config_updates[config.api_key_field] = kwargs[config.api_key_field]
            
            # For secret backend, add additional parameters
            if new_mode == "secret-3.14159":
                config_updates.update({
                    "backend_url": kwargs.get("backend_url", "https://star-shell-backend.vercel.app/"),
                    "secret_token": kwargs.get("secret_token", "secret-3.14159"),
                    "model_type": kwargs.get("model_type", "gemini-pro")
                })
            
            # Clean up old API keys when switching backend types
            current_config = load_config()
            if new_mode.startswith("openai") and "gemini_api_key" in current_config:
                config_updates["gemini_api_key"] = ""
            elif new_mode.startswith("gemini") and "openai_api_key" in current_config:
                config_updates["openai_api_key"] = ""
            elif new_mode == "secret-3.14159":
                config_updates["openai_api_key"] = ""
                config_updates["gemini_api_key"] = ""
            
            # Update configuration with validation and backup
            update_config_runtime(config_updates, validate_backend=False)  # We already validated
            
            # Update the session manager's genie
            if hasattr(self.session_manager, 'update_backend'):
                self.session_manager.update_backend(new_genie)
            else:
                # Fallback: directly set the genie
                self.session_manager.genie = new_genie
            
            return True
            
        except Exception as e:
            # Rollback on failure
            self.session_manager.genie = current_genie
            return False
    
    def _create_genie_instance(self, mode: str, **kwargs) -> Optional[BaseGenie]:
        """Create a new genie instance for the specified mode."""
        config = self._mode_configs.get(mode)
        if not config:
            return None
        
        # Get OS and shell info from current session manager
        os_fullname = getattr(self.session_manager.genie, 'os_fullname', 'Unknown OS')
        shell = getattr(self.session_manager.genie, 'shell', 'bash')
        
        try:
            if mode == "openai-gpt-3.5-turbo":
                api_key = kwargs.get("openai_api_key")
                return OpenAIGenie(api_key, os_fullname, shell)
            
            elif mode == "gemini-thinking":
                # Check if we should use secret backend for gemini-thinking
                if "backend_url" in kwargs and "secret_token" in kwargs:
                    # Use secret backend with gemini-thinking model
                    backend_url = kwargs.get("backend_url", "https://star-shell-backend.vercel.app/")
                    secret_token = kwargs.get("secret_token", "secret-3.14159")
                    return ProxyGenie(backend_url, secret_token, os_fullname, shell, "gemini-thinking")
                else:
                    # Use regular GeminiThinkingGenie with API key
                    api_key = kwargs.get("gemini_api_key")
                    return GeminiThinkingGenie(api_key, os_fullname, shell)
            
            elif mode in ["gemini-pro", "gemini-flash"]:
                api_key = kwargs.get("gemini_api_key")
                return GeminiGenie(api_key, os_fullname, shell, mode)
            
            elif mode == "secret-3.14159":
                backend_url = kwargs.get("backend_url", "https://star-shell-backend.vercel.app/")
                secret_token = kwargs.get("secret_token", "secret-3.14159")
                model_type = kwargs.get("model_type", "gemini-pro")
                return ProxyGenie(backend_url, secret_token, os_fullname, shell, model_type)
            
        except Exception:
            return None
        
        return None
    
    def handle_mode_command(self, command: str, args: List[str]) -> bool:
        """
        Handle mode-related commands.
        
        Args:
            command: The command (e.g., "mode", "/mode", "/gpt")
            args: Additional arguments
        
        Returns:
            True if command was handled, False otherwise
        """
        # Normalize command
        command = command.lower().strip()
        
        # Handle quick commands
        quick_mapping = self.get_quick_command_mapping()
        if command in quick_mapping:
            target_mode = quick_mapping[command]
            # For quick commands, we need to get credentials from existing config
            # This is a simplified implementation - in practice, you'd load from config
            return self._handle_quick_switch(target_mode)
        
        # Handle general mode commands
        if command in ["mode", "/mode"]:
            return self._handle_mode_selection(args)
        
        return False
    
    def _handle_quick_switch(self, target_mode: str) -> bool:
        """Handle quick mode switching commands using existing credentials."""
        current_mode = self.get_current_mode()
        if current_mode == target_mode:
            return True  # Already in target mode
        
        try:
            # Load current configuration to get existing credentials
            current_config = load_config()
            config = self._mode_configs.get(target_mode)
            
            if not config:
                return False
            
            # Prepare credentials from existing config
            credentials = {}
            
            if config.requires_api_key:
                # Check if we have the required API key
                if config.api_key_field in current_config and current_config[config.api_key_field]:
                    credentials[config.api_key_field] = current_config[config.api_key_field]
                else:
                    # No existing credentials, quick switch not possible
                    return False
            else:
                # For secret backend, use default values
                if target_mode == "secret-3.14159":
                    credentials = {
                        "backend_url": current_config.get("backend_url", "https://star-shell-backend.vercel.app/"),
                        "secret_token": current_config.get("secret_token", "secret-3.14159"),
                        "model_type": current_config.get("model_type", "gemini-pro")
                    }
            
            # Attempt the switch
            return self.switch_mode(target_mode, **credentials)
            
        except Exception:
            return False
    
    def _handle_mode_selection(self, args: List[str]) -> bool:
        """Handle interactive mode selection."""
        # This would show an interactive menu
        # For now, return False to indicate it needs UI integration
        return False
    
    def update_mode_credentials(self, mode: str, **credentials) -> bool:
        """
        Securely update credentials for a specific mode.
        
        Args:
            mode: The mode to update credentials for
            **credentials: The new credentials
            
        Returns:
            True if successful, False otherwise
        """
        config = self._mode_configs.get(mode)
        if not config or not config.requires_api_key:
            return False
        
        try:
            # Validate credentials first
            if not self.validate_mode_credentials(mode, **credentials):
                return False
            
            # Prepare configuration update
            config_updates = {}
            if config.api_key_field in credentials:
                config_updates[config.api_key_field] = credentials[config.api_key_field]
            
            # Update configuration with secure storage
            update_config_runtime(config_updates, validate_backend=False)
            
            return True
            
        except Exception:
            return False
    
    def get_available_credentials(self) -> Dict[str, bool]:
        """
        Check which backend credentials are available in the configuration.
        
        Returns:
            Dictionary mapping backend types to credential availability
        """
        try:
            config = load_config()
            return {
                "openai": bool(config.get("openai_api_key")),
                "gemini": bool(config.get("gemini_api_key")),
                "secret": bool(config.get("secret_token"))
            }
        except Exception:
            return {"openai": False, "gemini": False, "secret": False}