import asyncio
import sys
from typing import Optional
import typer
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory

from . import __version__
from .config import get_config_manager, Config
from .client import JarvisClient
from .display import DisplayManager, LiveWorkflowDisplay
from .session import SessionManager, ConversationSession
from .models import Message, JarvisOptions


app = typer.Typer(
    name="jarvis-cli",
    help="Terminal-based AI chat interface for Jarvis",
    add_completion=False,
    invoke_without_command=True,
    no_args_is_help=False,
)


# Main callback - runs when no command is provided
@app.callback()
def main(
    ctx: typer.Context,
    conversation_id: Optional[str] = typer.Option(
        None, "--conversation", "-c", help="Continue existing conversation"
    ),
    live: bool = typer.Option(
        False, "--live", "-l", help="Enable live workflow display mode"
    ),
    theme: str = typer.Option(
        "claude_dark", "--theme", "-t", help="Color theme (claude_dark, github_dark, monokai, dracula, nord)"
    ),
    version: bool = typer.Option(
        None, "--version", "-v", help="Show version and exit"
    )
) -> None:
    # Show version and exit if requested
    if version:
        typer.echo(f"jarvis-cli version {__version__}")
        raise typer.Exit()

    # If a subcommand is invoked, don't run interactive mode
    if ctx.invoked_subcommand is not None:
        return

    # Store options in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["live_mode"] = live
    ctx.obj["theme"] = theme

    # Interactive chat mode (REPL) - default behavior
    asyncio.run(_run_interactive_mode(conversation_id, live_mode=live, theme=theme))


# One-shot query mode
@app.command()
def ask(
    query: str = typer.Argument(..., help="Question to ask Jarvis"),
    conversation_id: Optional[str] = typer.Option(
        None, "--conversation", "-c", help="Continue existing conversation"
    ),
    live: bool = typer.Option(
        False, "--live", "-l", help="Enable live workflow display mode"
    ),
    theme: str = typer.Option(
        "claude_dark", "--theme", "-t", help="Color theme"
    ),
) -> None:
    # One-shot query mode
    asyncio.run(_run_one_shot(query, conversation_id, live_mode=live, theme=theme))


# Chat command (alias for main with conversation)
@app.command()
def chat(
    conversation_id: Optional[str] = typer.Argument(
        None, help="Conversation ID to continue"
    ),
    live: bool = typer.Option(
        False, "--live", "-l", help="Enable live workflow display mode"
    ),
    theme: str = typer.Option(
        "claude_dark", "--theme", "-t", help="Color theme"
    ),
) -> None:
    # Start or continue a chat conversation
    asyncio.run(_run_interactive_mode(conversation_id, live_mode=live, theme=theme))


# Configuration commands
config_app = typer.Typer(help="Configuration management")
app.add_typer(config_app, name="config")


@config_app.command("init")
def config_init() -> None:
    # Initialize configuration with interactive wizard
    config_manager = get_config_manager()

    if config_manager.exists():
        typer.confirm(
            "Configuration already exists. Overwrite?",
            abort=True,
        )

    config_manager.init_interactive()


@config_app.command("show")
def config_show() -> None:
    # Show current configuration
    config_manager = get_config_manager()

    if not config_manager.exists():
        typer.echo("No configuration found. Run 'jarvis-cli config init' first.")
        raise typer.Exit(1)

    config = config_manager.get()
    display = DisplayManager()

    display.console.print("[bold cyan]Current Configuration:[/bold cyan]\n")
    display.console.print(f"[yellow]API Base URL:[/yellow] {config.api_base_url}")
    display.console.print(f"[yellow]Login Code:[/yellow] {config.login_code or config.user_id}")
    display.console.print(f"[yellow]Theme:[/yellow] {config.display.theme}")
    display.console.print(f"\n[dim]Config file: {config_manager.config_path}[/dim]")


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Configuration key (e.g., 'user_id')"),
    value: str = typer.Argument(..., help="New value"),
) -> None:
    # Set a configuration value
    config_manager = get_config_manager()

    if not config_manager.exists():
        typer.echo("No configuration found. Run 'jarvis-cli config init' first.")
        raise typer.Exit(1)

    try:
        config_manager.set_value(key, value)
        typer.echo(f"Set {key} = {value}")
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


# History command
@app.command()
def history(
    limit: int = typer.Option(10, "--limit", "-n", help="Number of conversations to show")
) -> None:
    # Show conversation history
    session_manager = SessionManager()
    sessions = session_manager.list_sessions(limit=limit)

    display = DisplayManager()

    if not sessions:
        display.print_info("No conversation history found.")
        return

    display.console.print("[bold cyan]Recent Conversations:[/bold cyan]\n")

    for session in sessions:
        conv_id = session.get("conversation_id", "unknown")
        updated = session.get("updated_at", "unknown")
        msg_count = session.get("message_count", 0)

        display.console.print(
            f"[yellow]{conv_id}[/yellow] - "
            f"[dim]{updated}[/dim] - "
            f"{msg_count} messages"
        )


# Internal helper functions
async def _run_interactive_mode(
    conversation_id: Optional[str] = None,
    live_mode: bool = False,
    theme: str = "claude_dark"
) -> None:
    # Run interactive REPL mode
    # Load configuration
    config_manager = get_config_manager()

    if not config_manager.exists():
        typer.echo("No configuration found. Running setup wizard...\n")
        config_manager.init_interactive()

    config = config_manager.get()

    if not config.api_base_url:
        typer.echo("Error: API base URL not configured. Please run 'jarvis-cli config init' first.")
        raise typer.Exit(1)

    # Use config values if command-line options not provided
    final_live_mode = live_mode or config.display.live_mode
    final_theme = theme if theme != "claude_dark" else config.display.theme

    # Initialize components - use LiveWorkflowDisplay or regular DisplayManager
    if final_live_mode:
        display = LiveWorkflowDisplay(config=config.display, theme_name=final_theme)
    else:
        display = DisplayManager(config=config.display)

    session_manager = SessionManager()

    # Load or create session
    if conversation_id:
        try:
            session = session_manager.load_session(conversation_id)
            display.print_info(f"Loaded conversation: {conversation_id}")
        except FileNotFoundError:
            display.print_error(f"Conversation not found: {conversation_id}")
            session = session_manager.new_session()
    else:
        session = session_manager.new_session()

    # Create client
    jarvis_options = JarvisOptions(**config.jarvis_options.model_dump())
    client = JarvisClient(
        base_url=config.api_base_url,
        user_id=config.effective_user_id,
        jarvis_options=jarvis_options,
    )

    # Show welcome
    display.print_welcome()

    # Create prompt session for input history
    prompt_session = PromptSession(history=InMemoryHistory())

    try:
        while True:
            # Get user input
            try:
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: prompt_session.prompt("You: ")
                )
            except (EOFError, KeyboardInterrupt):
                break

            user_input = user_input.strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.startswith("/"):
                if user_input == "/exit":
                    break
                elif user_input == "/new":
                    session = session_manager.new_session()
                    display.print_info("Started new conversation")
                    continue
                elif user_input == "/help":
                    display.print_help()
                    continue
                elif user_input == "/history":
                    sessions = session_manager.list_sessions()
                    if sessions:
                        display.console.print("\n[bold cyan]Recent Conversations:[/bold cyan]\n")
                        for s in sessions[:5]:
                            display.console.print(
                                f"[yellow]{s.get('conversation_id', 'unknown')}[/yellow] - "
                                f"[dim]{s.get('updated_at', 'unknown')}[/dim]"
                            )
                        display.console.print()
                    else:
                        display.print_info("No conversation history")
                    continue
                elif user_input == "/config":
                    display.console.print(f"\n[yellow]API:[/yellow] {config.api_base_url}")
                    display.console.print(f"[yellow]Login:[/yellow] {config.effective_user_id}\n")
                    continue
                else:
                    display.print_error(f"Unknown command: {user_input}")
                    continue

            # Add user message to session
            session.add_message("user", user_input)

            # Send request and process streaming response
            try:
                # Start streaming (both modes now support real-time streaming)
                display.start_streaming()

                async for chunk in client.chat_completion_stream(
                    messages=session.get_messages(),
                    conversation_id=session.conversation_id,
                ):
                    # Process chunk
                    content_delta = display.process_chunk(chunk)

                    # Update streaming content (both modes stream in real-time)
                    if content_delta:
                        display.update_streaming_content(content_delta)

                    # Extract conversation_id from metadata
                    if chunk.choices and chunk.choices[0].delta:
                        delta = chunk.choices[0].delta
                        if delta.jarvis_metadata and delta.jarvis_metadata.conversation_id:
                            if not session.conversation_id:
                                session.set_conversation_id(delta.jarvis_metadata.conversation_id)

                # End streaming
                display.end_streaming()

                # Add assistant response to session
                if display._current_content:
                    session.add_message("assistant", display._current_content)

                # Auto-save session
                session_manager.auto_save_current()

            except KeyboardInterrupt:
                display.print_info("\nRequest cancelled")
                continue
            except Exception as e:
                display.print_error(f"Request failed: {e}")
                continue

    finally:
        await client.close()
        display.print_info("Goodbye!")


async def _run_one_shot(
    query: str,
    conversation_id: Optional[str] = None,
    live_mode: bool = False,
    theme: str = "claude_dark"
) -> None:
    # Run one-shot query mode
    # Load configuration
    config_manager = get_config_manager()

    if not config_manager.exists():
        typer.echo("No configuration found. Run 'jarvis-cli config init' first.")
        raise typer.Exit(1)

    config = config_manager.get()

    if not config.api_base_url:
        typer.echo("Error: API base URL not configured. Please run 'jarvis-cli config init' first.")
        raise typer.Exit(1)

    # Use config values if command-line options not provided
    final_live_mode = live_mode or config.display.live_mode
    final_theme = theme if theme != "claude_dark" else config.display.theme

    # Initialize components - use LiveWorkflowDisplay or regular DisplayManager
    if final_live_mode:
        display = LiveWorkflowDisplay(config=config.display, theme_name=final_theme)
    else:
        display = DisplayManager(config=config.display)

    session_manager = SessionManager()

    # Load or create session
    if conversation_id:
        try:
            session = session_manager.load_session(conversation_id)
        except FileNotFoundError:
            display.print_error(f"Conversation not found: {conversation_id}")
            raise typer.Exit(1)
    else:
        session = session_manager.new_session()

    # Create client
    jarvis_options = JarvisOptions(**config.jarvis_options.model_dump())
    client = JarvisClient(
        base_url=config.api_base_url,
        user_id=config.effective_user_id,
        jarvis_options=jarvis_options,
    )

    # Add user message
    session.add_message("user", query)
    display.print_user_message(query)

    try:
        # Start streaming (both modes now support real-time streaming)
        display.start_streaming()

        async for chunk in client.chat_completion_stream(
            messages=session.get_messages(),
            conversation_id=session.conversation_id,
        ):
            # Process chunk
            content_delta = display.process_chunk(chunk)

            # Update streaming content (both modes stream in real-time)
            if content_delta:
                display.update_streaming_content(content_delta)

            # Extract conversation_id from metadata
            if chunk.choices and chunk.choices[0].delta:
                delta = chunk.choices[0].delta
                if delta.jarvis_metadata and delta.jarvis_metadata.conversation_id:
                    if not session.conversation_id:
                        session.set_conversation_id(delta.jarvis_metadata.conversation_id)

        # End streaming
        display.end_streaming()

        # Add assistant response to session
        if display._current_content:
            session.add_message("assistant", display._current_content)

        # Auto-save session
        session_manager.auto_save_current()

        # Print conversation ID for reference
        if session.conversation_id:
            display.print_info(f"Conversation ID: {session.conversation_id}")

    except Exception as e:
        display.print_error(f"Request failed: {e}")
        raise typer.Exit(1)
    finally:
        await client.close()


if __name__ == "__main__":
    app()
