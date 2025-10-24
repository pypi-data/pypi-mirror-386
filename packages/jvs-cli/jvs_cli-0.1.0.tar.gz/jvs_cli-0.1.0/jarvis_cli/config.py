import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class DisplayConfig(BaseModel):
    show_thinking: bool = True
    show_tools: bool = True
    show_knowledge_sources: bool = True
    markdown: bool = True
    colors: bool = True
    live_mode: bool = False
    theme: str = "claude_dark"
    typewriter_effect: bool = False


class JarvisOptionsConfig(BaseModel):
    enable_sse_events: bool = True
    include_thinking: bool = True
    include_tool_calls: bool = True
    include_knowledge_refs: bool = True


class Config(BaseModel):
    api_base_url: str = ""
    user_id: str = ""
    jarvis_options: JarvisOptionsConfig = Field(default_factory=JarvisOptionsConfig)
    display: DisplayConfig = Field(default_factory=DisplayConfig)


class ConfigManager:
    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path.home() / ".jarvis-cli" / "config.json"

        self.config_path = config_path
        self.config_dir = config_path.parent
        self._config: Optional[Config] = None

    def _ensure_config_dir(self) -> None:
        # Create config directory if it doesn't exist
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> Config:
        # Load configuration from file or return default
        if not self.config_path.exists():
            return Config()

        try:
            with open(self.config_path, "r") as f:
                data = json.load(f)
            self._config = Config(**data)
            return self._config
        except Exception as e:
            raise RuntimeError(f"Failed to load config from {self.config_path}: {e}")

    def save(self, config: Config) -> None:
        # Save configuration to file
        self._ensure_config_dir()

        try:
            with open(self.config_path, "w") as f:
                json.dump(config.model_dump(), f, indent=2)
            self._config = config
        except Exception as e:
            raise RuntimeError(f"Failed to save config to {self.config_path}: {e}")

    def get(self) -> Config:
        # Get current configuration (load if not cached)
        if self._config is None:
            self._config = self.load()
        return self._config

    def set_value(self, key_path: str, value: Any) -> None:
        # Set a nested configuration value using dot notation (e.g., "display.show_thinking")
        config = self.get()
        config_dict = config.model_dump()

        # Navigate to nested key
        keys = key_path.split(".")
        current = config_dict

        for key in keys[:-1]:
            if key not in current:
                raise ValueError(f"Invalid config key path: {key_path}")
            current = current[key]

        # Set the value
        final_key = keys[-1]
        if final_key not in current:
            raise ValueError(f"Invalid config key: {final_key}")

        # Type conversion
        if isinstance(current[final_key], bool):
            value = value.lower() in ("true", "1", "yes", "on") if isinstance(value, str) else bool(value)

        current[final_key] = value

        # Save updated config
        updated_config = Config(**config_dict)
        self.save(updated_config)

    def exists(self) -> bool:
        # Check if config file exists
        return self.config_path.exists()

    def init_interactive(self) -> Config:
        from rich.console import Console
        from rich.prompt import Prompt, Confirm

        console = Console()
        console.print("\n[bold cyan]Jarvis CLI Configuration Wizard[/bold cyan]\n")

        console.print("[dim]This CLI requires an OpenAI-compatible API endpoint.[/dim]")
        console.print("[dim]Example: https://api.example.com/v1[/dim]\n")

        api_url = ""
        while not api_url:
            api_url = Prompt.ask("Enter your API base URL").strip()
            if not api_url:
                console.print("[red]API URL is required[/red]")
            elif not (api_url.startswith("http://") or api_url.startswith("https://")):
                console.print("[red]API URL must start with http:// or https://[/red]")
                api_url = ""

        user_id = Prompt.ask("Enter your user ID")

        show_thinking = Confirm.ask("Show AI thinking steps?", default=True)
        show_tools = Confirm.ask("Show tool execution details?", default=True)
        live_mode = Confirm.ask("Enable live workflow display mode?", default=False)

        theme = "claude_dark"
        if live_mode:
            theme = Prompt.ask(
                "Select color theme",
                choices=["claude_dark", "github_dark", "monokai", "dracula", "nord"],
                default="claude_dark"
            )

        typewriter_effect = Confirm.ask("Enable typewriter effect for responses?", default=False)

        config = Config(
            api_base_url=api_url,
            user_id=user_id,
            display=DisplayConfig(
                show_thinking=show_thinking,
                show_tools=show_tools,
                live_mode=live_mode,
                theme=theme,
                typewriter_effect=typewriter_effect
            )
        )

        self.save(config)

        console.print(f"\n[green]✓[/green] Configuration saved to: {self.config_path}")

        return config


# Global config manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    # Get or create global config manager instance
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
