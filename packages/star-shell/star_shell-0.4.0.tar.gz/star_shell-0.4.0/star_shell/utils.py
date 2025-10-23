import platform
import json
from pathlib import Path
import typer
from star_shell.backend import OpenAIGenie, GeminiGenie, ProxyGenie
from star_shell.security import secure_storage


def get_os_info():
    oper_sys = platform.system()
    if oper_sys == "Windows" or oper_sys == "Darwin":
        oper_sys = "MacOS" if oper_sys == "Darwin" else "Windows"
        return (oper_sys, platform.platform(aliased=True, terse=True))
    if oper_sys == "Linux":
        return (oper_sys, platform.freedesktop_os_release()["PRETTY_NAME"])
    return (None, None)


def load_config():
    """Load and decrypt configuration from the config file."""
    APP_NAME = ".star_shell"
    app_dir = typer.get_app_dir(APP_NAME)
    config_path = Path(app_dir) / "config.json"
    
    if not config_path.exists():
        raise FileNotFoundError("Configuration file not found. Please run 'star-shell init' first.")
    
    with open(config_path, "r") as f:
        config = json.load(f)
    
    # Decrypt API keys if they exist and are encrypted
    if "openai_api_key" in config and config["openai_api_key"]:
        config["openai_api_key"] = secure_storage.decrypt_api_key(config["openai_api_key"])
    
    if "gemini_api_key" in config and config["gemini_api_key"]:
        config["gemini_api_key"] = secure_storage.decrypt_api_key(config["gemini_api_key"])
    
    return config


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
    elif backend_name in ["gemini-pro", "gemini-flash"]:
        return GeminiGenie(
            api_key=config["gemini_api_key"],
            os_fullname=config["os_fullname"],
            shell=config["shell"],
            backend_type=backend_name,
        )
    else:
        raise ValueError(f"Unknown backend: {backend_name}")