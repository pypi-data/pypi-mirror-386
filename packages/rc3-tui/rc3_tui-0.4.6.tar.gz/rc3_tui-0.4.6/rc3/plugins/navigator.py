"""
Navigator Plugin - Unified directory browsing and command execution
"""

import os
import shutil
import asyncio
import shlex
from pathlib import Path
from datetime import datetime
from textual.widgets import Static, ListView, ListItem, Label, Input
from textual.containers import Vertical, Container, VerticalScroll
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Button
from textual.containers import Horizontal

from rc3.plugins.base import BasePlugin
from rc3.core.command_runner import CommandRunner


# Reuse DirectoryListItem from working_directory
class DirectoryListItem(ListItem):
    """Custom list item that stores file/folder metadata"""
    
    def __init__(self, path: Path, is_parent: bool = False, **kwargs):
        self.path = path
        self.is_parent = is_parent
        self.is_dir = path.is_dir() if not is_parent else True
        
        # Format display
        if is_parent:
            label_text = "[dim][D][/dim] .."
        else:
            prefix = "[cyan][D][/cyan]" if self.is_dir else "[green][F][/green]"
            name = path.name
            label_text = f"{prefix} {name}"
        
        super().__init__(Label(label_text), **kwargs)


# Reuse CommandListItem from quick_commands
class CommandListItem(ListItem):
    """Custom list item that stores command data"""
    
    def __init__(self, index: int, command_data: dict, **kwargs):
        self.index = index
        self.command_data = command_data
        name = command_data.get("name", "Unnamed")
        desc = command_data.get("description", "")
        shortcut = command_data.get("shortcut", "")
        
        # Format with underlined shortcut
        formatted_name = self._underline_shortcut_in_name(name, shortcut)
        label = f"{formatted_name:<30} {desc}"
        
        super().__init__(Label(label), **kwargs)
    
    def _underline_shortcut_in_name(self, name: str, shortcut: str) -> str:
        """Underline the shortcut letter within the command name"""
        if not shortcut or len(shortcut) != 1:
            return name
        
        shortcut_lower = shortcut.lower()
        name_lower = name.lower()
        
        # Find first occurrence of shortcut letter (case-insensitive)
        for i, char in enumerate(name_lower):
            if char == shortcut_lower:
                underlined_name = name[:i] + f"[u]{name[i]}[/u]" + name[i+1:]
                return underlined_name
        
        # If shortcut letter not found in name, append it at the end
        return f"{name} [u]{shortcut}[/u]"


# Interactive Terminal Widget
class InteractiveTerminal(Vertical):
    """Interactive terminal with command input and output history"""
    
    current_directory = reactive("")
    command_history = []
    history_index = -1
    current_input = ""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.runner = CommandRunner()
        self.input_widget = None
        self.output_widget = None
        self.prompt_widget = None
        self.command_history = []
        self.history_index = -1
        self.current_input = ""
        self.output_content = ""  # Buffer for terminal output
    
    def compose(self):
        """Build the terminal UI"""
        yield Static(id="terminal-header")
        with VerticalScroll(id="terminal-output"):
            yield Static(id="terminal-content")
        yield Static(id="terminal-prompt")
        yield Input(id="terminal-input", placeholder="Enter command...")
    
    def on_mount(self):
        """Initialize terminal components"""
        self.input_widget = self.query_one("#terminal-input", Input)
        self.output_widget = self.query_one("#terminal-content", Static)
        self.prompt_widget = self.query_one("#terminal-prompt", Static)
        self.update_prompt()
        self.add_output("[cyan]Interactive Terminal Ready[/cyan]\n[dim]Type commands and press Enter to execute[/dim]\n")
    
    def watch_current_directory(self):
        """Update prompt when directory changes"""
        self.update_prompt()
    
    def update_prompt(self):
        """Update the terminal prompt"""
        if self.prompt_widget:
            if self.current_directory:
                # Show current directory in prompt
                dir_name = Path(self.current_directory).name
                self.prompt_widget.update(f"[green]{dir_name}[/green] [yellow]$[/yellow] ")
            else:
                self.prompt_widget.update("[green]terminal[/green] [yellow]$[/yellow] ")
    
    def add_output(self, text: str):
        """Add text to terminal output"""
        if self.output_widget:
            # Append to our content buffer
            self.output_content += text
            self.output_widget.update(self.output_content)
            # Auto-scroll to bottom
            self.call_after_refresh(self._scroll_to_bottom)
    
    def _scroll_to_bottom(self):
        """Scroll terminal output to bottom"""
        try:
            scroll_widget = self.query_one("#terminal-output", VerticalScroll)
            scroll_widget.scroll_end()
        except Exception:
            pass
    
    def execute_command(self, command: str):
        """Execute a command and display output"""
        if not command.strip():
            return
        
        # Add command to history
        if not self.command_history or self.command_history[-1] != command:
            self.command_history.append(command)
            if len(self.command_history) > 50:  # Keep last 50 commands
                self.command_history.pop(0)
        self.history_index = len(self.command_history)
        
        # Display command being executed
        self.add_output(f"[yellow]$[/yellow] {command}\n")
        
        # Handle special commands
        if command.strip() == "clear":
            self.output_content = ""
            self.output_widget.update("")
            return
        
        # Execute command
        self.call_later(self._run_command_async, command)
    
    async def _run_command_async(self, command: str):
        """Run command asynchronously"""
        try:
            success, stdout, stderr = await asyncio.to_thread(
                self.runner.run,
                command,
                shell="powershell" if os.name == 'nt' else "bash",
                cwd=self.current_directory,
                timeout=30
            )
            
            # Display output
            if stdout.strip():
                self.add_output(stdout)
            if stderr.strip():
                self.add_output(f"[red]{stderr}[/red]")
            if not stdout.strip() and not stderr.strip():
                self.add_output("[dim]No output[/dim]")
            
            # Add status indicator
            status_color = "green" if success else "red"
            status_text = "✓" if success else "✗"
            self.add_output(f"\n[{status_color}]{status_text}[/{status_color}]\n")
            
        except Exception as e:
            self.add_output(f"[red]Error: {str(e)}[/red]\n")
    
    def get_history_up(self):
        """Get previous command from history"""
        if self.command_history and self.history_index > 0:
            self.history_index -= 1
            return self.command_history[self.history_index]
        return self.current_input
    
    def get_history_down(self):
        """Get next command from history"""
        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            return self.command_history[self.history_index]
        elif self.history_index == len(self.command_history) - 1:
            self.history_index = len(self.command_history)
            return ""
        return self.current_input
    
    def on_input_submitted(self, event):
        """Handle command input submission"""
        command = event.value.strip()
        if command:
            self.current_input = ""
            self.execute_command(command)
            self.input_widget.value = ""
    
    def on_key(self, event):
        """Handle terminal-specific key events"""
        key = event.key
        
        # Always prevent other hotkeys when terminal is active
        if key in ["q", "ctrl+c", "ctrl+d", "ctrl+r", "left", "right", "1", "2", "3", "4", "5"]:
            # Block global hotkeys when terminal is active
            event.prevent_default()
            event.stop()
            return
        
        if key == "up":
            # Navigate command history up
            if self.input_widget:
                self.current_input = self.input_widget.value
                self.input_widget.value = self.get_history_up()
            event.prevent_default()
            event.stop()
        
        elif key == "down":
            # Navigate command history down
            if self.input_widget:
                self.current_input = self.input_widget.value
                self.input_widget.value = self.get_history_down()
            event.prevent_default()
            event.stop()
        
        elif key == "escape":
            # Switch focus back to left panel
            if hasattr(self.parent, 'switch_to_left_panel'):
                self.parent.switch_to_left_panel()
            event.prevent_default()
            event.stop()
        
        elif key == "f1":
            # Switch focus back to left panel (alternative to escape)
            if hasattr(self.parent, 'switch_to_left_panel'):
                self.parent.switch_to_left_panel()
            event.prevent_default()
            event.stop()


class FavoriteListItem(ListItem):
    """Custom list item for favorites"""
    
    def __init__(self, path: str, exists: bool = True, **kwargs):
        self.path = path
        self.exists = exists
        
        # Format display
        path_obj = Path(path)
        if not exists:
            label_text = f"[red][X][/red] [dim strikethrough]{path}[/dim strikethrough]"
        else:
            label_text = f"[cyan][★][/cyan] {path}"
        
        super().__init__(Label(label_text), **kwargs)


class FavoritesOverlay(ModalScreen):
    """Modal overlay for managing and selecting favorite directories"""
    
    def __init__(self, config_manager, current_path: Path):
        super().__init__()
        self.config_manager = config_manager
        self.current_path = current_path
        self.list_view = None
        self.result_path = None
    
    def compose(self):
        """Build the overlay UI"""
        with Container(id="favorites-container"):
            yield Static("[bold cyan]FAVORITES[/bold cyan]", id="favorites-header")
            yield ListView(id="favorites-list")
            yield Static(
                "[dim]jk/Arrows:Navigate | f:Add Current | d:Delete | Enter:Jump | Esc:Close[/dim]",
                id="favorites-help"
            )
    
    def on_mount(self):
        """Initialize after mount"""
        self.list_view = self.query_one("#favorites-list", ListView)
        self.refresh_favorites()
        self.list_view.focus()
    
    def refresh_favorites(self):
        """Refresh the favorites list"""
        self.list_view.clear()
        
        favorites = self.config_manager.get_favorites()
        
        if not favorites:
            # Show empty state
            self.list_view.append(
                ListItem(Label("[dim]No favorites yet. Press 'f' to add current directory.[/dim]"))
            )
        else:
            for fav_path in favorites:
                # Check if path exists
                exists = Path(fav_path).exists()
                self.list_view.append(FavoriteListItem(fav_path, exists=exists))
    
    def on_key(self, event) -> None:
        """Handle keyboard shortcuts"""
        key = event.key
        
        if key == "escape":
            self.dismiss(None)
            event.prevent_default()
            event.stop()
        
        elif key == "enter":
            # Jump to selected favorite
            selected = self.get_selected_favorite()
            if selected:
                self.dismiss(selected.path)
            event.prevent_default()
            event.stop()
        
        elif key in ["j", "down"]:
            # Navigate down
            if self.list_view.highlighted_child is None and len(self.list_view.children) > 0:
                self.list_view.index = 0
            else:
                self.list_view.action_cursor_down()
            event.prevent_default()
            event.stop()
        
        elif key in ["k", "up"]:
            # Navigate up
            if self.list_view.highlighted_child is None and len(self.list_view.children) > 0:
                self.list_view.index = 0
            else:
                self.list_view.action_cursor_up()
            event.prevent_default()
            event.stop()
        
        elif key == "f":
            # Add current directory to favorites
            added = self.config_manager.add_favorite(str(self.current_path))
            if added:
                self.app.notify(f"⭐ Added: {self.current_path.name}", severity="information", timeout=1.0)
                self.refresh_favorites()
            else:
                self.app.notify("⚠️ Already in favorites", severity="warning", timeout=1.0)
            event.prevent_default()
            event.stop()
        
        elif key == "d":
            # Delete selected favorite
            selected = self.get_selected_favorite()
            if selected:
                removed = self.config_manager.remove_favorite(selected.path)
                if removed:
                    self.app.notify(f"🗑️ Removed: {Path(selected.path).name}", severity="information", timeout=1.0)
                    self.refresh_favorites()
            event.prevent_default()
            event.stop()
    
    def get_selected_favorite(self):
        """Get currently selected FavoriteListItem"""
        if self.list_view.highlighted_child:
            item = self.list_view.highlighted_child
            if isinstance(item, FavoriteListItem):
                return item
        return None


class DeleteConfirmationModal(ModalScreen):
    """Modal dialog for delete confirmation"""
    
    def __init__(self, item_name: str, item_path: Path):
        super().__init__()
        self.item_name = item_name
        self.item_path = item_path
    
    def compose(self):
        with Vertical(id="delete-modal"):
            yield Static(f"[bold red]Delete '{self.item_name}'?[/bold red]", id="delete-prompt")
            yield Static(f"[dim]{self.item_path}[/dim]", id="delete-path")
            with Horizontal(id="delete-buttons"):
                yield Button("Yes", variant="error", id="btn-yes")
                yield Button("No", variant="primary", id="btn-no")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press"""
        if event.button.id == "btn-yes":
            self.dismiss(True)
        else:
            self.dismiss(False)
    
    def on_key(self, event) -> None:
        """Handle keyboard shortcuts"""
        key = event.key
        if key == "escape":
            self.dismiss(False)
        elif key == "y":
            self.dismiss(True)
        elif key == "n":
            self.dismiss(False)


class NavigatorWidget(Container):
    """Unified navigator with directory list (left) and interactive terminal (right)"""
    
    can_focus = True
    
    current_path = reactive(Path.cwd())
    input_mode = reactive("")  # "", "create", "rename"
    input_target = reactive(None)
    active_panel = reactive("left")  # "left" or "right"
    
    def __init__(self, commands: list, config_manager):
        super().__init__()
        self.commands = commands
        self.config_manager = config_manager
        self.runner = CommandRunner()
        self.list_view = None
        self.header = None
        self.path_display = None
        self.help_text = None
        self.input_widget = None
        self.input_prompt = None
        self.output_panel = None
        
        # Build shortcut map from YAML config (excluding reserved navigation/system keys)
        self.shortcut_map = {}
        self.nav_keys = {'h', 'j', 'k', 'l', 'n', 'r', 'd', 'o', 'e', 't', 'f', 'g'}
        self.conflicting_commands = []
        
        for i, cmd in enumerate(commands, 1):
            shortcut = cmd.get("shortcut", "").lower()
            if shortcut and len(shortcut) == 1 and shortcut not in self.nav_keys:
                self.shortcut_map[shortcut] = i
            elif shortcut in self.nav_keys:
                # Track conflicting commands to warn user
                cmd_name = cmd.get("name", "Unknown")
                self.conflicting_commands.append((cmd_name, shortcut))
    
    def compose(self):
        """Build the split-screen UI"""
        from textual.containers import Horizontal
        
        with Horizontal(id="navigator-split"):
            # Left side: Directory navigation (always visible)
            with Vertical(id="nav-left", classes="nav-panel"):
                yield Static(id="nav-header")
                yield Static(id="nav-path")
                yield ListView(id="nav-list")
                yield Static(id="nav-help")
                yield Static(id="input-prompt")
                yield Input(id="nav-input", placeholder="Enter value...")
            
            # Right side: Interactive Terminal
            with Vertical(id="nav-right", classes="nav-panel"):
                self.terminal_panel = InteractiveTerminal(id="terminal-panel")
                yield self.terminal_panel
    
    def on_mount(self):
        """Initialize after mount"""
        self.list_view = self.query_one("#nav-list", ListView)
        self.header = self.query_one("#nav-header", Static)
        self.path_display = self.query_one("#nav-path", Static)
        self.help_text = self.query_one("#nav-help", Static)
        self.input_prompt = self.query_one("#input-prompt", Static)
        self.input_widget = self.query_one("#nav-input", Input)
        
        # Hide input initially
        self.input_widget.display = False
        self.input_prompt.display = False
        
        # Initialize terminal with current directory
        if self.terminal_panel:
            self.terminal_panel.current_directory = str(self.current_path)
        
        # Load directory
        self.refresh_directory()
        self.update_help_text()
        
        # Show helpful messages
        if self.conflicting_commands:
            conflict_msg = f"⚠️ Reserved shortcuts: {', '.join([f'{name}({key})' for name, key in self.conflicting_commands])}"
            self.app.notify(conflict_msg, severity="warning", timeout=3.0)
        elif not self.commands:
            # Show helpful tip if no commands configured
            if self.terminal_panel:
                self.terminal_panel.add_output(
                    "[cyan]Welcome to Navigator![/cyan]\n\n"
                    "The directory browser is ready to use:\n"
                    "  • Navigate with [yellow]hjkl[/yellow] or arrow keys\n"
                    "  • Press [yellow]Enter[/yellow] to open directories/files\n"
                    "  • Use [yellow]n/r/d/o/e[/yellow] for file operations\n"
                    "  • Press [yellow]`[/yellow] to switch to terminal\n\n"
                    "[yellow]To add command shortcuts:[/yellow]\n"
                    "  1. Edit [cyan]~/.rc3/commands.yaml[/cyan]\n"
                    "  2. Press [cyan]Ctrl+R[/cyan] to reload\n"
                    "  3. Press [cyan]2[/cyan] to view Command Reference\n\n"
                    "[dim]Commands will execute in the currently browsed directory[/dim]\n"
                )
        
        # Focus this widget
        self.set_timer(0.01, lambda: self.focus())
    
    def watch_current_path(self, new_path: Path):
        """React to path changes"""
        self.refresh_directory()
        # Auto-set working directory
        try:
            os.chdir(new_path)
        except Exception:
            pass
        
        # Update terminal directory
        if self.terminal_panel:
            self.terminal_panel.current_directory = str(new_path)
    
    def watch_active_panel(self, new_panel: str):
        """React to panel focus changes"""
        self.update_panel_focus()
    
    def watch_input_mode(self, new_mode: str):
        """React to input mode changes (for file operations)"""
        if new_mode:
            # Show input widgets
            self.input_widget.display = True
            self.input_prompt.display = True
            self.input_widget.value = ""
            
            # Set prompt text
            if new_mode == "create":
                self.input_prompt.update("[yellow]Create new folder:[/yellow]")
            elif new_mode == "rename":
                if self.input_target:
                    self.input_prompt.update(f"[yellow]Rename '{self.input_target.name}' to:[/yellow]")
                    self.input_widget.value = self.input_target.name
            
            # Focus input
            self.input_widget.focus()
        else:
            # Hide input widgets
            self.input_widget.display = False
            self.input_prompt.display = False
            self.input_target = None
            self.focus()
        
        self.update_help_text()
    
    def update_panel_focus(self):
        """Update visual focus indicators for panels"""
        try:
            left_panel = self.query_one("#nav-left")
            right_panel = self.query_one("#nav-right")
            
            if self.active_panel == "left":
                left_panel.add_class("nav-panel-focused")
                right_panel.remove_class("nav-panel-focused")
                right_panel.add_class("nav-panel-unfocused")
                # Focus the list view
                self.list_view.focus()
            else:
                right_panel.add_class("nav-panel-focused")
                left_panel.remove_class("nav-panel-focused")
                left_panel.add_class("nav-panel-unfocused")
                # Focus the terminal input
                if self.terminal_panel and self.terminal_panel.input_widget:
                    self.terminal_panel.input_widget.focus()
        except Exception:
            pass
    
    def switch_to_left_panel(self):
        """Switch focus to left panel"""
        self.active_panel = "left"
        self.app.notify("📁 Directory", severity="information", timeout=0.5)
    
    def switch_to_right_panel(self):
        """Switch focus to right panel"""
        self.active_panel = "right"
        self.app.notify("💻 Terminal", severity="information", timeout=0.5)
    
    def refresh_directory(self):
        """Refresh directory listing"""
        try:
            # Update header and path
            self.header.update("[bold cyan]NAVIGATOR[/bold cyan]")
            self.path_display.update(f"[dim]Working Directory:[/dim] [yellow]{self.current_path}[/yellow]")
            
            # Clear list
            self.list_view.clear()
            
            # Add parent directory entry if not at root
            if self.current_path.parent != self.current_path:
                self.list_view.append(DirectoryListItem(self.current_path.parent, is_parent=True))
            
            # List directories and files
            items = []
            try:
                for item in self.current_path.iterdir():
                    items.append(item)
            except PermissionError:
                self.app.notify("🚫 Permission denied", severity="error", timeout=2.0)
                return
            
            # Sort: directories first, then files, alphabetically
            dirs = sorted([i for i in items if i.is_dir()], key=lambda x: x.name.lower())
            files = sorted([i for i in items if i.is_file()], key=lambda x: x.name.lower())
            
            # Add to list
            for item in dirs + files:
                self.list_view.append(DirectoryListItem(item))
            
        except Exception as e:
            self.app.notify(f"❌ Directory error", severity="error", timeout=2.0)
    
    def update_help_text(self):
        """Update help text based on current mode"""
        if self.input_mode:
            self.help_text.update("[dim]Enter to confirm | Esc to cancel[/dim]")
        else:
            if self.commands:
                help_lines = [
                    "[dim]hjkl/Arrows Navigate | Enter Open | [green]F5 Refresh[/green] | Letter Keys Execute Commands",
                    "n New | r Rename | d Delete | o Open | e Explorer | t Terminal | [cyan]f Favorites[/cyan] | [yellow]g Git Commit[/yellow] | [magenta]F1 Terminal[/magenta][/dim]"
                ]
            else:
                help_lines = [
                    "[dim]hjkl/Arrows Navigate | Enter Open | [green]F5 Refresh[/green]",
                    "n New | r Rename | d Delete | o Open | e Explorer | t Terminal | [cyan]f Favorites[/cyan] | [yellow]g Git Commit[/yellow] | [magenta]F1 Terminal[/magenta][/dim]"
                ]
            self.help_text.update("\n".join(help_lines))
    
    def on_key(self, event) -> None:
        """Handle keyboard shortcuts"""
        key = event.key
        
        # Handle focus switching with multiple key options
        if key in ["`", "ctrl+`", "f1"]:
            if self.active_panel == "left":
                self.switch_to_right_panel()
            else:
                self.switch_to_left_panel()
            event.prevent_default()
            event.stop()
            return
        
        # Route input based on active panel
        if self.active_panel == "right":
            # Terminal panel is active - let terminal handle input
            if self.terminal_panel:
                self.terminal_panel.on_key(event)
            return
        
        # Left panel is active - handle navigation and file operations
        # Input mode handling (file operations)
        if self.input_mode:
            # Check if Input widget is focused
            if self.input_widget and self.app.focused == self.input_widget:
                # Input has focus - only intercept escape and enter
                if key == "escape":
                    self.input_mode = ""
                    event.prevent_default()
                    event.stop()
                    return
                elif key == "enter":
                    self.handle_input_submit()
                    event.prevent_default()
                    event.stop()
                    return
                # For all other keys, don't handle - let Input process them
                return
            # Input doesn't have focus, cancel input mode
            else:
                self.input_mode = ""
                return
        
        # hjkl navigation (always active - highest priority)
        if key in ["j", "down"]:
            if self.list_view.highlighted_child is None and len(self.list_view.children) > 0:
                self.list_view.index = 0
            else:
                self.list_view.action_cursor_down()
            event.prevent_default()
            event.stop()
            return
        
        elif key in ["k", "up"]:
            if self.list_view.highlighted_child is None and len(self.list_view.children) > 0:
                self.list_view.index = 0
            else:
                self.list_view.action_cursor_up()
            event.prevent_default()
            event.stop()
            return
        
        elif key in ["h", "left", "backspace"]:
            self.go_to_parent()
            event.prevent_default()
            event.stop()
            return
        
        elif key in ["l", "right", "enter"]:
            self.handle_enter_or_open()
            event.prevent_default()
            event.stop()
            return
        
        # File operation keys
        elif key == "n":
            self.start_create_folder()
            event.prevent_default()
            event.stop()
        
        elif key == "r":
            self.start_rename()
            event.prevent_default()
            event.stop()
        
        elif key == "d":
            self.start_delete()
            event.prevent_default()
            event.stop()
        
        elif key == "o":
            self.open_in_system()
            event.prevent_default()
            event.stop()
        
        elif key == "e":
            self.open_in_explorer()
            event.prevent_default()
            event.stop()
        
        elif key == "t":
            self.open_terminal()
            event.prevent_default()
            event.stop()
        
        elif key == "f":
            self.show_favorites_overlay()
            event.prevent_default()
            event.stop()
        
        # Smart Git Commit automation (g key)
        elif key == "g":
            self.run_git_smart_commit()
            event.prevent_default()
            event.stop()
        
        # F5 Refresh - reload directory listing
        elif key == "f5":
            self.refresh_directory()
            self.app.notify("🔄 Refreshed", severity="information", timeout=0.5)
            event.prevent_default()
            event.stop()
        
        # Command shortcuts (always active - executed by letter keys not reserved for nav)
        elif key in self.shortcut_map:
            index = self.shortcut_map[key]
            self.execute_command_by_index(index)
            event.prevent_default()
            event.stop()
    
    # Directory navigation methods (from working_directory.py)
    
    def get_selected_item(self):
        """Get currently selected DirectoryListItem"""
        if self.list_view.highlighted_child:
            item = self.list_view.highlighted_child
            if isinstance(item, DirectoryListItem):
                return item
        return None
    
    def handle_enter_or_open(self):
        """Enter directory or open file"""
        item = self.get_selected_item()
        if not item:
            return
        
        if item.is_parent:
            self.go_to_parent()
        elif item.is_dir:
            # Navigate into directory
            self.current_path = item.path
        else:
            # Open file with system default
            self.open_in_system()
    
    def go_to_parent(self):
        """Navigate to parent directory"""
        parent = self.current_path.parent
        if parent != self.current_path:
            self.current_path = parent
    
    def start_create_folder(self):
        """Start create folder input mode"""
        self.input_mode = "create"
        self.input_target = None
    
    def start_rename(self):
        """Start rename input mode"""
        item = self.get_selected_item()
        if not item or item.is_parent:
            self.app.notify("⚠️ Select item to rename", severity="warning", timeout=1.0)
            return
        
        self.input_mode = "rename"
        self.input_target = item.path
    
    def start_delete(self):
        """Show delete confirmation modal"""
        item = self.get_selected_item()
        if not item or item.is_parent:
            self.app.notify("⚠️ Select item to delete", severity="warning", timeout=1.0)
            return
        
        # Show modal and handle result
        def handle_delete_result(confirmed: bool):
            if confirmed:
                self.delete_item(item.path)
        
        self.app.push_screen(
            DeleteConfirmationModal(item.path.name, item.path),
            handle_delete_result
        )
    
    def open_in_system(self):
        """Open selected item with system default application"""
        item = self.get_selected_item()
        if not item or item.is_parent:
            return
        
        try:
            if os.name == 'nt':  # Windows
                os.startfile(str(item.path))
            elif os.name == 'posix':  # Linux/Mac
                import subprocess
                if os.uname().sysname == 'Darwin':  # Mac
                    subprocess.run(['open', str(item.path)])
                else:  # Linux
                    subprocess.run(['xdg-open', str(item.path)])
            
            self.app.notify(f"📂 Opened: {item.path.name}", severity="information", timeout=1.0)
        except Exception as e:
            self.app.notify(f"❌ Open failed", severity="error", timeout=2.0)
    
    def open_in_explorer(self):
        """Open current directory in Windows File Explorer"""
        try:
            if os.name == 'nt':  # Windows
                import subprocess
                subprocess.Popen(['explorer', str(self.current_path)])
                self.app.notify(f"📁 Explorer: {self.current_path.name}", severity="information", timeout=1.0)
            elif os.name == 'posix':  # Linux/Mac
                import subprocess
                if os.uname().sysname == 'Darwin':  # Mac
                    subprocess.Popen(['open', str(self.current_path)])
                else:  # Linux
                    subprocess.Popen(['xdg-open', str(self.current_path)])
                self.app.notify(f"📁 File manager: {self.current_path.name}", severity="information", timeout=1.0)
        except Exception as e:
            self.app.notify(f"❌ Explorer failed", severity="error", timeout=2.0)
    
    def open_terminal(self):
        """Open a new terminal in current directory"""
        try:
            if os.name == 'nt':  # Windows
                import subprocess
                # Try Windows Terminal first, fallback to PowerShell
                try:
                    # Windows Terminal (modern) - simpler approach
                    subprocess.Popen(
                        ['wt.exe', '-d', str(self.current_path)],
                        shell=False
                    )
                except (FileNotFoundError, OSError):
                    # Fallback: Open new PowerShell window using cmd start command
                    # This creates a completely separate process
                    subprocess.Popen(
                        ['cmd', '/c', 'start', 'powershell', '-NoExit', '-Command', 
                         f'Set-Location "{self.current_path}"'],
                        shell=False
                    )
                self.app.notify(f"💻 Terminal: {self.current_path.name}", severity="information", timeout=1.0)
            elif os.name == 'posix':  # Linux/Mac
                import subprocess
                if os.uname().sysname == 'Darwin':  # Mac
                    # macOS Terminal
                    script = f'tell application "Terminal" to do script "cd {shlex.quote(str(self.current_path))}"'
                    subprocess.Popen(['osascript', '-e', script])
                else:  # Linux
                    # Try common Linux terminals
                    terminals = [
                        ['gnome-terminal', '--working-directory', str(self.current_path)],
                        ['xterm', '-e', f'cd {shlex.quote(str(self.current_path))} && exec bash'],
                        ['konsole', '--workdir', str(self.current_path)],
                    ]
                    for term_cmd in terminals:
                        try:
                            subprocess.Popen(term_cmd)
                            break
                        except FileNotFoundError:
                            continue
                self.app.notify(f"💻 Terminal: {self.current_path.name}", severity="information", timeout=1.0)
        except Exception as e:
            self.app.notify(f"❌ Terminal failed", severity="error", timeout=2.0)
    
    def handle_input_submit(self):
        """Handle input submission based on mode"""
        value = self.input_widget.value.strip()
        
        if self.input_mode == "create":
            self.create_folder(value)
        elif self.input_mode == "rename":
            self.rename_item(value)
        
        # Exit input mode
        self.input_mode = ""
    
    def create_folder(self, name: str):
        """Create new folder"""
        if not name:
            self.app.notify("⚠️ Name required", severity="warning", timeout=1.0)
            return
        
        # Validate name (no invalid characters)
        invalid_chars = '<>:"/\\|?*'
        if any(c in name for c in invalid_chars):
            self.app.notify("❌ Invalid name", severity="error", timeout=2.0)
            return
        
        new_path = self.current_path / name
        
        try:
            new_path.mkdir(exist_ok=False)
            self.app.notify(f"📁 Created: {name}", severity="information", timeout=1.0)
            self.refresh_directory()
        except FileExistsError:
            self.app.notify(f"⚠️ Exists: {name}", severity="warning", timeout=1.0)
        except Exception as e:
            self.app.notify(f"❌ Create failed", severity="error", timeout=2.0)
    
    def rename_item(self, new_name: str):
        """Rename selected item"""
        if not new_name or not self.input_target:
            self.app.notify("⚠️ Name required", severity="warning", timeout=1.0)
            return
        
        # Validate name
        invalid_chars = '<>:"/\\|?*'
        if any(c in new_name for c in invalid_chars):
            self.app.notify("❌ Invalid name", severity="error", timeout=2.0)
            return
        
        new_path = self.input_target.parent / new_name
        
        try:
            self.input_target.rename(new_path)
            self.app.notify(f"✏️ Renamed: {new_name}", severity="information", timeout=1.0)
            self.refresh_directory()
        except FileExistsError:
            self.app.notify(f"⚠️ Exists: {new_name}", severity="warning", timeout=1.0)
        except Exception as e:
            self.app.notify(f"❌ Rename failed", severity="error", timeout=2.0)
    
    def delete_item(self, item_path: Path):
        """Delete item at the given path"""
        if not item_path:
            return
        
        try:
            if item_path.is_dir():
                shutil.rmtree(item_path)
            else:
                item_path.unlink()
            
            self.app.notify(f"🗑️ Deleted: {item_path.name}", severity="information", timeout=1.0)
            self.refresh_directory()
        except Exception as e:
            self.app.notify(f"❌ Delete failed", severity="error", timeout=2.0)
    
    # Command execution methods (from quick_commands.py)
    
    def execute_command_by_index(self, index: int):
        """Execute a command by its index"""
        if 1 <= index <= len(self.commands):
            cmd_data = self.commands[index - 1].copy()  # Copy to avoid modifying original
            
            # Get selected file/folder for {file} substitution
            selected_item = self.get_selected_item()
            if selected_item and not selected_item.is_parent:
                selected_path = str(selected_item.path)
                selected_name = selected_item.path.name
                
                # Replace placeholders in command
                command = cmd_data.get("command", "")
                command = command.replace("{file}", selected_name)
                command = command.replace("{path}", selected_path)
                cmd_data["command"] = command
            
            self.call_later(self.run_command_async, cmd_data)
    
    async def run_command_async(self, cmd_data: dict):
        """Run command asynchronously in background thread"""
        name = cmd_data.get("name", "Unnamed")
        command = cmd_data.get("command")
        shell = cmd_data.get("shell")
        cwd = cmd_data.get("cwd")
        
        # Use current browsed directory if no cwd specified
        if not cwd:
            cwd = str(self.current_path)
        
        # Update terminal panel
        if self.terminal_panel:
            self.terminal_panel.add_output(f"[yellow]Executing:[/yellow] {name}\n[dim]Command: {command}[/dim]\n[dim]Working directory: {cwd}[/dim]\n\n")
        
        # Show notification
        self.app.notify(f"⚡ {name}", severity="information", timeout=1.0)
        
        # Run command in background thread
        start_time = datetime.now()
        try:
            success, stdout, stderr = await asyncio.to_thread(
                self.runner.run,
                command,
                shell=shell,
                cwd=cwd
            )
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Format output
            output_lines = []
            
            if stdout.strip():
                output_lines.append(f"[green]STDOUT:[/green]\n{stdout}")
            
            if stderr.strip():
                output_lines.append(f"[yellow]STDERR:[/yellow]\n{stderr}")
            
            if not stdout.strip() and not stderr.strip():
                output_lines.append("[dim]No output[/dim]")
            
            # Add footer with status
            status_color = "green" if success else "red"
            status_text = "SUCCESS" if success else "FAILED"
            output_lines.append(f"\n[{status_color}]═══ {status_text} ═══[/{status_color}]  [dim]Duration: {duration:.2f}s[/dim]")
            
            # Update terminal panel
            if self.terminal_panel:
                self.terminal_panel.add_output("\n".join(output_lines) + "\n")
            
            # Show notification
            if success:
                self.app.notify(f"✅ {name} ({duration:.1f}s)", severity="information", timeout=1.0)
            else:
                self.app.notify(f"❌ {name} failed", severity="error", timeout=2.0)
        
        except Exception as e:
            # Handle execution errors
            if self.terminal_panel:
                self.terminal_panel.add_output(f"[red]ERROR:[/red]\n{str(e)}\n")
            self.app.notify(f"❌ {name} error", severity="error", timeout=2.0)
    
    def run_git_smart_commit(self):
        """Smart git commit using Codex CLI - runs from current navigator directory"""
        self.app.notify("🔍 Analyzing git changes...", severity="information", timeout=1.0)
        
        # Find git root starting from current navigator path
        git_root = self._find_git_root_from_path(str(self.current_path))
        if not git_root:
            self.app.notify("❌ Not in a git repository", severity="error", timeout=2.0)
            return
        
        # Check for changes
        success, status_output, stderr = CommandRunner.run(
            "git status --porcelain",
            shell="powershell",
            cwd=git_root,
            timeout=10
        )
        
        if not success:
            self.app.notify(f"❌ Git status failed", severity="error", timeout=2.0)
            return
        
        if not status_output.strip():
            self.app.notify("✓ No changes to commit", severity="warning", timeout=1.0)
            return
        
        # Get full git diff for context
        success, diff_output, stderr = CommandRunner.run(
            "git diff HEAD",
            shell="powershell",
            cwd=git_root,
            timeout=30
        )
        
        if not success:
            self.app.notify(f"❌ Git diff failed", severity="error", timeout=2.0)
            return
        
        # Ensure diff_output is not None
        diff_output = diff_output or ""
        
        # Also get staged diff if any
        success, staged_diff, _ = CommandRunner.run(
            "git diff --cached",
            shell="powershell",
            cwd=git_root,
            timeout=30
        )
        
        # Ensure staged_diff is not None
        staged_diff = staged_diff or ""
        
        combined_diff = (staged_diff + "\n" + diff_output).strip() if staged_diff or diff_output else ""
        
        if not combined_diff.strip():
            # Only untracked files, get file list
            success, untracked, _ = CommandRunner.run(
                "git ls-files --others --exclude-standard",
                shell="powershell",
                cwd=git_root,
                timeout=10
            )
            combined_diff = f"New files:\n{untracked}"
        
        # Use Codex CLI to generate commit message
        self.app.notify("🤖 Generating commit message with Codex...", severity="information", timeout=1.0)
        
        # Escape the diff for PowerShell
        escaped_diff = combined_diff.replace('"', '`"').replace('$', '`$')
        
        codex_prompt = f"""Analyze this git diff and generate a concise, conventional commit message.
Follow conventional commit format (type: description).
Types: feat, fix, refactor, docs, style, test, chore, perf.
Keep it under 72 characters for the summary.

Git diff:
{escaped_diff[:8000]}

Return ONLY the commit message, nothing else."""
        
        # Run codex exec in non-interactive mode
        success, commit_msg, stderr = CommandRunner.run(
            f'codex exec --ask-for-approval never "{codex_prompt}"',
            shell="powershell",
            cwd=git_root,
            timeout=60
        )
        
        if not success or not commit_msg.strip():
            self.app.notify(f"❌ Codex failed", severity="error", timeout=2.0)
            # Fallback to simple commit message
            commit_msg = "chore: automated commit"
            self.app.notify(f"⚠️ Using fallback: {commit_msg}", severity="warning", timeout=1.0)
        else:
            commit_msg = commit_msg.strip()
            # Clean up any extra formatting from Codex output
            if '\n' in commit_msg:
                commit_msg = commit_msg.split('\n')[0]  # Take first line only
        
        # Stage all changes
        self.app.notify("📦 Staging all changes...", severity="information", timeout=1.0)
        success, _, stderr = CommandRunner.run(
            "git add .",
            shell="powershell",
            cwd=git_root,
            timeout=10
        )
        
        if not success:
            self.app.notify(f"❌ Git add failed", severity="error", timeout=2.0)
            return
        
        # Commit with generated message
        self.app.notify(f"💾 Committing: {commit_msg[:50]}...", severity="information", timeout=1.0)
        success, _, stderr = CommandRunner.run(
            f'git commit -m "{commit_msg}"',
            shell="powershell",
            cwd=git_root,
            timeout=15
        )
        
        if not success:
            self.app.notify(f"❌ Git commit failed", severity="error", timeout=2.0)
            return
        
        # Push to remote
        self.app.notify("🚀 Pushing to remote...", severity="information", timeout=1.0)
        success, push_output, stderr = CommandRunner.run(
            "git push",
            shell="powershell",
            cwd=git_root,
            timeout=30
        )
        
        if not success:
            self.app.notify(f"❌ Git push failed", severity="error", timeout=2.0)
            return
        
        self.app.notify(f"✅ Committed & pushed: {commit_msg[:50]}", severity="information", timeout=2.0)
    
    def _find_git_root_from_path(self, start_path: str) -> str:
        """Find the git root directory starting from given path"""
        current_dir = start_path
        
        while True:
            if os.path.isdir(os.path.join(current_dir, '.git')):
                return current_dir
            
            parent = os.path.dirname(current_dir)
            if parent == current_dir:  # Reached filesystem root
                return None
            
            current_dir = parent
    
    def show_favorites_overlay(self):
        """Show the favorites overlay"""
        def handle_result(result_path):
            """Handle overlay result"""
            if result_path:
                # Jump to selected favorite
                try:
                    path = Path(result_path)
                    if path.exists() and path.is_dir():
                        self.current_path = path
                        self.app.notify(f"⭐ Jumped to: {path.name}", severity="information", timeout=1.0)
                    else:
                        self.app.notify(f"❌ Path not found", severity="error", timeout=2.0)
                except Exception as e:
                    self.app.notify(f"❌ Jump failed", severity="error", timeout=2.0)
        
        # Show overlay
        overlay = FavoritesOverlay(self.config_manager, self.current_path)
        self.app.push_screen(overlay, callback=handle_result)


class Plugin(BasePlugin):
    """Navigator Plugin - Unified directory and command interface"""
    
    name = "Navigator"
    description = "Unified directory browsing and command execution"
    
    def render(self):
        """Render the navigator interface"""
        commands = self.config.get_commands("quick_commands")
        
        # Always show navigator, even with no commands
        if not commands:
            commands = []
        
        return NavigatorWidget(commands, self.config)

