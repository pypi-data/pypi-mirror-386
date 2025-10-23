import os
import sys
import subprocess
from pathlib import Path
from typing import Optional

import typer
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts import CompleteStyle

from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text
from rich import print as rprint

from .service import (
    process_chat_message,
    filter_unchanged_files
)

from .ui import (
    print_welcome_message,
    print_help_message,
    print_prompt,
    print_error,
    print_assistant_response,
    print_no_files_changed,
    print_files_updated
)

from .plugin_manager import PluginManager
from .auth import get_token, get_user_config, set_user_config

# Snapshot core utilities
from .snapshot import (
    list_snapshots,
    restore_snapshot,
    prune_snapshots,
    apply_updates
)

from .config import MODELS

# Initialize plugin manager and get completer
plugin_manager = PluginManager()
plugin_manager.discover()


def handle_model_command(session, models, conf, tokens):
    """Handle the 'model' command: display current and list available models for selection."""
    if len(tokens) > 1:
        try:
            num = int(tokens[1])
            if 1 <= num <= len(models):
                selected_id = models[num - 1]["id"]
                conf.selected_model = selected_id
                set_user_config("selected_model", selected_id)
                rprint(f"[green]Selected model: {models[num - 1]['name']}[/]")
            else:
                rprint("[red]Invalid model number.[/]")
        except ValueError:
            rprint("[red]Invalid input. Use a number.[/]")
    else:
        current_id = conf.selected_model
        current_name = next(m['name'] for m in models if m['id'] == current_id)
        rprint(f"[yellow]Currently selected:[/] {current_name}")
        rprint("")
        rprint("[yellow]Available models:[/]")
        for i, m in enumerate(models, 1):
            rprint(f"  {i}. {m['name']}")
        choice = session.prompt("Enter model number to select (or Enter to keep current): ").strip()
        if not choice:
            rprint("[yellow]Keeping current model.[/]")
        else:
            try:
                num = int(choice)
                if 1 <= num <= len(models):
                    selected_id = models[num - 1]["id"]
                    conf.selected_model = selected_id
                    set_user_config("selected_model", selected_id)
                    rprint(f"[green]Selected: {models[num - 1]['name']}[/]")
                else:
                    rprint("[red]Invalid number.[/]")
            except ValueError:
                rprint("[red]Invalid input.[/]")


def chat_repl(conf) -> None:
    # NEW: Download plugins at start of every chat session (commented out to avoid network call during REPL)
    # from .download_plugins import fetch_plugins
    # fetch_plugins()

    # Get completer from plugin manager
    completer_response = plugin_manager.handle_command("get_completer")
    completer = completer_response["completer"] if completer_response else None

    session = PromptSession(
        history=InMemoryHistory(),
        completer=completer,
        complete_style=CompleteStyle.READLINE_LIKE,
        complete_while_typing=False
    )

    if conf.file_mask is None:
        response = plugin_manager.handle_command(
            "auto_detect_mask",
            {"project_root": str(conf.root) if conf.root else "."}
        )
        conf.file_mask = response["mask"] if response and response.get("mask") else "*.py"

    rprint(f"[bold cyan]Session context: {conf.file_mask}[/]")
    print_welcome_message()
    console = Console()

    # Path to store chat_id persistently during session
    chat_id_file = Path(".aye/chat_id.tmp")
    chat_id_file.parent.mkdir(parents=True, exist_ok=True)

    # Setting to -1 to initiate a new chat if no ongoing chat detected
    chat_id = -1

    # Load chat_id if exists from previous session
    if chat_id_file.exists():
        try:
            chat_id = int(chat_id_file.read_text(encoding="utf-8").strip())
        except ValueError:
            chat_id_file.unlink(missing_ok=True)  # Clear invalid file

    # Models configuration
    conf.selected_model = get_user_config("selected_model", MODELS[0]["id"])

    while True:
        try:
            prompt = session.prompt(print_prompt())
        except (EOFError, KeyboardInterrupt):
            break

        if not prompt.strip():
            continue

        # Tokenize input respecting shell‑style quoting
        import shlex
        try:
            # Use posix=False so single quotes (apostrophes) are treated as normal characters.
            tokens = shlex.split(prompt.strip(), posix=False)
        except ValueError as e:
            # shlex raises ValueError on malformed quoting – report and skip
            rprint(f"[red]Error parsing command:{e}[/]")
            continue
        if not tokens:
            continue
        original_first = tokens[0]
        lowered_first = original_first.lower()

        # Check for exit commands
        if lowered_first in {"exit", "quit", ":q"}:
            break

        # Model command
        if lowered_first == "model":
            handle_model_command(session, MODELS, conf, tokens)
            continue

        # Diff command (still uses original implementation)
        if lowered_first == "diff":
            from .service import handle_diff_command
            handle_diff_command(tokens[1:])
            continue

        # Snapshot‑related commands – now handled directly via snapshot.py
        if lowered_first in {"history", "restore", "keep"}:
            args = tokens[1:] if len(tokens) > 1 else []
            try:
                if lowered_first == "history":
                    snaps = list_snapshots()
                    if snaps:
                        for s in snaps:
                            rprint(s)
                    else:
                        rprint("[yellow]No snapshots found.[/]")
                elif lowered_first == "restore":
                    # Determine whether the argument is an ordinal or a filename
                    ordinal = None
                    file_name = None
                    if len(args) == 1:
                        possible = args[0]
                        # If it looks like a file that exists, treat it as filename
                        if Path(possible).exists():
                            file_name = possible
                        else:
                            ordinal = possible
                    elif len(args) >= 2:
                        ordinal = args[0]
                        file_name = args[1]
                    # Call the core restore function
                    restore_snapshot(ordinal, file_name)
                    if ordinal:
                        if file_name:
                            rprint(f"[green]✅ File '{file_name}' restored to {ordinal}[/]")
                        else:
                            rprint(f"[green]✅ All files restored to {ordinal}[/]")
                    else:
                        if file_name:
                            rprint(f"[green]✅ File '{file_name}' restored to latest snapshot.[/]")
                        else:
                            rprint("[green]✅ All files restored to latest snapshot.[/]")
                elif lowered_first == "keep":
                    keep_count = int(args[0]) if args and args[0].isdigit() else 10
                    deleted = prune_snapshots(keep_count)
                    rprint(f"✅ {deleted} snapshots pruned. {keep_count} most recent kept.")
            except Exception as e:
                rprint(f"[red]Error:[/] {e}")
            continue

        # New chat command
        if lowered_first == "new":
            chat_id_file.unlink(missing_ok=True)
            chat_id = -1
            console.print("[green]✅ New chat session started.[/]")
            continue

        # Help command
        if lowered_first == "help":
            print_help_message()
            continue

        # Shell commands – delegated to plugin system
        shell_response = plugin_manager.handle_command("execute_shell_command", {
            "command": original_first,
            "args": tokens[1:]
        })
        if shell_response is not None:
            if "error" in shell_response:
                rprint(f"[red]Error:[/] {shell_response['error']}")
            else:
                if shell_response.get("stdout", "").strip():
                    rprint(shell_response["stdout"])
            continue

        # Process LLM chat message
        try:
            spinner = Spinner("dots", text="[yellow]Thinking...[/]")
            with console.status(spinner) as status:
                result = process_chat_message(prompt, chat_id, conf.root, conf.file_mask, conf.selected_model)
        except Exception as exc:
            if hasattr(exc, "response") and getattr(exc.response, "status_code", None) == 403:
                from .ui import print_error
                print_error(
                    "[red]❌ Unauthorized:[/] the stored token is invalid or missing.\n"
                    "Log in again with `aye auth login` or set a valid "
                    "`AYE_TOKEN` environment variable.\n"
                    "Obtain your personal access token at https://ayechat.ai"
                )
            else:
                from .ui import print_error
                print_error(exc)
            continue

        # Store new chat ID if present
        new_chat_id = result.get("new_chat_id")
        if new_chat_id is not None:
            chat_id = new_chat_id
            chat_id_file.write_text(str(chat_id), encoding="utf-8")

        # Display assistant response summary
        summary = result.get("summary")
        if summary:
            print_assistant_response(summary)

        # Determine which files were actually changed
        updated_files = result.get("updated_files", [])
        updated_files = filter_unchanged_files(updated_files)
        # ---------------------------------------------------------------------
        # NEW: Normalise file paths – ensure they are relative to the REPL root
        # ---------------------------------------------------------------------
        def _make_paths_relative(files: list[dict], root: Path) -> list[dict]:
            """Strip *root* from any file_name that already starts with it.
            This prevents double‑prefixing like `src/aye/src/aye/foo.py`.
            """
            root = root.resolve()
            for f in files:
                if "file_name" not in f:
                    continue
                try:
                    p = Path(f["file_name"]).resolve()
                    if p.is_relative_to(root):
                        f["file_name"] = str(p.relative_to(root))
                except Exception:
                    # If the path cannot be resolved or Python <3.9, leave it unchanged
                    pass
            return files

        updated_files = _make_paths_relative(updated_files, conf.root)

        if not updated_files:
            print_no_files_changed(console)
        else:
            # Apply updates directly via snapshot utilities
            try:
                batch_ts = apply_updates(updated_files)
                if batch_ts:
                    file_names = [item.get("file_name") for item in updated_files if "file_name" in item]
                    if file_names:
                        print_files_updated(console, file_names)
            except Exception as e:
                rprint(f"[red]Error applying updates:[/] {e}")

if __name__ == "__main__":
    chat_repl()
