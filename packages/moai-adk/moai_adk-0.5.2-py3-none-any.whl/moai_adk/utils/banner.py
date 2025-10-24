# @CODE:UTILS-001 | SPEC: SPEC-CLI-001/spec.md
"""ASCII banner module

Render the MoAI-ADK ASCII art banner
"""

from rich.console import Console

console = Console()

MOAI_BANNER = """
███╗   ███╗ ██████╗  █████╗ ██╗       █████╗ ██████╗ ██╗  ██╗
████╗ ████║██╔═══██╗██╔══██╗██║      ██╔══██╗██╔══██╗██║ ██╔╝
██╔████╔██║██║   ██║███████║██║█████╗███████║██║  ██║█████╔╝
██║╚██╔╝██║██║   ██║██╔══██║██║╚════╝██╔══██║██║  ██║██╔═██╗
██║ ╚═╝ ██║╚██████╔╝██║  ██║██║      ██║  ██║██████╔╝██║  ██╗
╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝      ╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝
"""


def print_banner(version: str = "0.3.0") -> None:
    """Print the MoAI-ADK banner

    Args:
        version: MoAI-ADK version
    """
    console.print(f"[cyan]{MOAI_BANNER}[/cyan]")
    console.print(
        "[dim]  Modu-AI's Agentic Development Kit w/ SuperAgent 🎩 Alfred[/dim]\n"
    )
    console.print(f"[dim]  Version: {version}[/dim]\n")


def print_welcome_message() -> None:
    """Print the welcome message"""
    console.print("[cyan bold]🚀 Welcome to MoAI-ADK Project Initialization![/cyan bold]\n")
    console.print(
        "[dim]This wizard will guide you through setting up your MoAI-ADK project.[/dim]"
    )
    console.print(
        "[dim]You can press Ctrl+C at any time to cancel.\n[/dim]"
    )
