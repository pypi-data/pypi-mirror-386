"""
Interactive setup wizard for first-time configuration.
Works without LLM - pure hardcoded logic for collecting user settings.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.text import Text

console = Console()


class SetupWizard:
    """Interactive setup wizard for configuring RagOps Agent CE."""

    def __init__(self, env_path: Path | None = None):
        self.env_path = env_path or Path.cwd() / ".env"
        self.config: dict[str, str] = {}

    def run(self) -> bool:
        """Run the setup wizard. Returns True if setup completed successfully."""
        console.clear()
        self._show_welcome()

        # Step 1: Choose LLM provider
        provider = self._choose_provider()
        if not provider:
            return False

        self.config["RAGOPS_LLM_PROVIDER"] = provider

        # Step 2: Configure provider credentials
        if not self._configure_provider(provider):
            return False

        # Step 3: Optional settings
        self._configure_optional_settings()

        # Step 4: Save configuration
        return self._save_config()

    def _show_welcome(self) -> None:
        """Show welcome message."""
        welcome_text = Text()
        welcome_text.append("Welcome to ", style="white")
        welcome_text.append("RagOps Agent CE", style="bold cyan")
        welcome_text.append(" Setup Wizard!\n\n", style="white")

        # Strong recommendation about workspace
        welcome_text.append("💡 ", style="bold cyan")
        welcome_text.append("IMPORTANT: ", style="bold cyan")
        welcome_text.append("Run the agent from a new, empty directory!\n", style="cyan")
        welcome_text.append(
            "The agent will create project files, .env, and other artifacts.\n", style="dim"
        )
        welcome_text.append("Recommended:\n", style="dim")
        welcome_text.append(
            "  mkdir ~/ragops-workspace && cd ~/ragops-workspace\n\n", style="green"
        )

        welcome_text.append(
            "This wizard will help you configure the agent for first use.\n", style="dim"
        )
        welcome_text.append("You'll need an API key for your chosen LLM provider.\n\n", style="dim")
        welcome_text.append("⚠️  ", style="yellow")
        welcome_text.append("PoC Version: ", style="yellow bold")
        welcome_text.append("Currently only Vertex AI is fully supported.\n", style="yellow")
        welcome_text.append(
            "Other providers (OpenAI, Anthropic, Ollama) are coming soon!", style="dim italic"
        )

        console.print(Panel(welcome_text, title="🚀 Setup", border_style="cyan"))
        console.print()

    def _choose_provider(self) -> str | None:
        """Let user choose LLM provider."""
        console.print("[bold]Step 1:[/bold] Choose your LLM provider\n")

        providers = {
            "1": {
                "name": "vertexai",
                "display": "Vertex AI (Google Cloud)",
                "description": "Google's Gemini models via Vertex AI",
                "available": True,
            },
            "2": {
                "name": "openai",
                "display": "OpenAI",
                "description": "Coming soon",
                "available": False,
            },
            "3": {
                "name": "azure_openai",
                "display": "Azure OpenAI",
                "description": "Coming soon",
                "available": False,
            },
            "4": {
                "name": "anthropic",
                "display": "Anthropic Claude",
                "description": "Coming soon",
                "available": False,
            },
            "5": {
                "name": "ollama",
                "display": "Ollama (Local)",
                "description": "Coming soon",
                "available": False,
            },
        }

        for key, info in providers.items():
            if info["available"]:
                console.print(f"  {key}. [bold]{info['display']}[/bold] - {info['description']}")
            else:
                console.print(f"  {key}. [dim]{info['display']} - {info['description']}[/dim]")

        console.print()
        choice = Prompt.ask(
            "Select provider",
            choices=["1"],  # Only allow Vertex AI for now
            default="1",
        )

        provider = providers[choice]["name"]
        console.print(f"✓ Selected: [green]{providers[choice]['display']}[/green]\n")
        return provider

    def _configure_provider(self, provider: str) -> bool:
        """Configure credentials for chosen provider."""
        console.print(f"[bold]Step 2:[/bold] Configure {provider} credentials\n")

        if provider == "vertexai":
            return self._configure_vertex()
        elif provider == "openai":
            return self._configure_openai()
        elif provider == "anthropic":
            return self._configure_anthropic()
        elif provider == "ollama":
            return self._configure_ollama()

        return False

    def _configure_vertex(self) -> bool:
        """Configure Vertex AI credentials."""
        console.print("[dim]You need a service account key file from Google Cloud.[/dim]")
        console.print(
            "[dim]Get it at: https://console.cloud.google.com/iam-admin/serviceaccounts[/dim]\n"
        )

        path = Prompt.ask("Enter path to service account JSON file")
        path = os.path.expanduser(path)

        if not Path(path).exists():
            console.print(f"[red]✗ File not found:[/red] {path}")
            retry = Confirm.ask("Try again?", default=True)
            if retry:
                return self._configure_vertex()
            return False

        self.config["RAGOPS_VERTEX_CREDENTIALS"] = path
        console.print(f"✓ Credentials file: [green]{path}[/green]\n")
        return True

    def _configure_openai(self) -> bool:
        """Configure OpenAI credentials."""
        console.print("[dim]Get your API key at: https://platform.openai.com/api-keys[/dim]\n")

        api_key = Prompt.ask("Enter OpenAI API key", password=True)

        if not api_key or not api_key.startswith("sk-"):
            console.print("[yellow]⚠ API key should start with 'sk-'[/yellow]")
            retry = Confirm.ask("Continue anyway?", default=False)
            if not retry:
                return self._configure_openai()

        self.config["RAGOPS_OPENAI_API_KEY"] = api_key
        console.print("✓ API key configured\n")
        return True

    def _configure_anthropic(self) -> bool:
        """Configure Anthropic credentials."""
        console.print("[dim]Get your API key at: https://console.anthropic.com/[/dim]\n")

        api_key = Prompt.ask("Enter Anthropic API key", password=True)

        if not api_key or not api_key.startswith("sk-ant-"):
            console.print("[yellow]⚠ API key should start with 'sk-ant-'[/yellow]")
            retry = Confirm.ask("Continue anyway?", default=False)
            if not retry:
                return self._configure_anthropic()

        self.config["RAGOPS_ANTHROPIC_API_KEY"] = api_key
        console.print("✓ API key configured\n")
        return True

    def _configure_ollama(self) -> bool:
        """Configure Ollama local instance."""
        console.print("[dim]Make sure Ollama is installed and running.[/dim]")
        console.print("[dim]Install at: https://ollama.ai[/dim]\n")

        default_url = "http://localhost:11434"
        url = Prompt.ask("Ollama base URL", default=default_url)

        self.config["RAGOPS_OLLAMA_BASE_URL"] = url
        console.print(f"✓ Ollama URL: [green]{url}[/green]\n")
        return True

    def _configure_optional_settings(self) -> None:
        """Configure optional settings."""
        console.print("[bold]Step 3:[/bold] Optional settings\n")

        # Log level
        if Confirm.ask("Configure log level?", default=False):
            log_level = Prompt.ask(
                "Log level",
                choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                default="INFO",
            )
            self.config["RAGOPS_LOG_LEVEL"] = log_level
            console.print(f"✓ Log level: [green]{log_level}[/green]\n")
        else:
            console.print("[dim]Using default log level: INFO[/dim]\n")

    def _save_config(self) -> bool:
        """Save configuration to .env file."""
        console.print("[bold]Step 4:[/bold] Save configuration\n")

        # Show summary
        summary = Text()
        summary.append("Configuration summary:\n\n", style="bold")
        for key, value in self.config.items():
            display_value = value
            # Mask sensitive values
            if "KEY" in key and len(value) > 10:
                display_value = value[:8] + "..." + value[-4:]
            summary.append(f"  {key} = ", style="dim")
            summary.append(f"{display_value}\n", style="green")

        console.print(Panel(summary, border_style="cyan"))
        console.print()

        # Check if we have write permissions
        target_dir = self.env_path.parent
        if not os.access(target_dir, os.W_OK):
            console.print(f"[red]✗ No write permission in:[/red] {target_dir}\n")
            # Suggest alternative location
            home_dir = Path.home() / "ragops-workspace"
            console.print(
                f"[yellow]Suggestion:[/yellow] Create workspace directory first:\n"
                f"  mkdir -p {home_dir}\n"
                f"  cd {home_dir}\n"
                f"  donkit-ragops-ce --setup\n"
            )
            return False

        # Check if .env already exists
        if self.env_path.exists():
            console.print(f"[yellow]⚠ File already exists:[/yellow] {self.env_path}")
            if not Confirm.ask("Overwrite?", default=False):
                console.print("[red]Setup cancelled.[/red]")
                return False

        # Save to .env
        try:
            lines = ["# RagOps Agent CE Configuration", "# Generated by setup wizard", ""]
            for key, value in self.config.items():
                lines.append(f"{key}={value}")
            lines.append("")  # Empty line at end

            self.env_path.write_text("\n".join(lines))
            console.print(f"✓ Configuration saved to: [green]{self.env_path}[/green]\n")
            return True
        except PermissionError:
            console.print(f"[red]✗ Permission denied:[/red] Cannot write to {self.env_path}\n")
            console.print(
                "[yellow]Try running from a directory where you have write permissions.[/yellow]"
            )
            return False
        except Exception as e:
            console.print(f"[red]✗ Failed to save configuration:[/red] {e}")
            return False

    def show_success(self) -> None:
        """Show success message after setup."""
        success_text = Text()
        success_text.append("🎉 Setup completed successfully!\n\n", style="bold green")
        success_text.append("You can now start the agent with:\n", style="white")
        success_text.append("  donkit-ragops-ce\n\n", style="bold cyan")
        success_text.append("Or edit ", style="dim")
        success_text.append(f"{self.env_path}", style="yellow")
        success_text.append(" manually to change settings.", style="dim")

        console.print(Panel(success_text, title="✓ Ready", border_style="green"))


def check_needs_setup(env_path: Path | None = None) -> bool:
    """Check if setup is needed (no .env file or missing required settings)."""
    env_path = env_path or Path.cwd() / ".env"

    if not env_path.exists():
        return True

    # Check if .env has required settings
    try:
        config = dotenv_values(env_path)
        provider = config.get("RAGOPS_LLM_PROVIDER")

        if not provider:
            return True

        # Check provider-specific credentials
        if provider == "vertexai" and not config.get("RAGOPS_VERTEX_CREDENTIALS"):
            return True
        if provider == "openai" and not config.get("RAGOPS_OPENAI_API_KEY"):
            return True
        if provider == "anthropic" and not config.get("RAGOPS_ANTHROPIC_API_KEY"):
            return True

        return False
    except Exception:
        return True


def run_setup_if_needed(force: bool = False) -> bool:
    """Run setup wizard if needed. Returns True if agent can proceed."""
    env_path = Path.cwd() / ".env"

    if force or check_needs_setup(env_path):
        if not force:
            console.print("[yellow]⚠ No configuration found. Running setup wizard...[/yellow]\n")

        wizard = SetupWizard(env_path)
        success = wizard.run()

        if success:
            wizard.show_success()
            console.print()
            return True
        else:
            console.print("[red]Setup failed or cancelled. Cannot start agent.[/red]")
            return False

    return True
