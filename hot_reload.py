import sys
import time
import importlib
import os
import hashlib
from pathlib import Path
from typing import Dict, Optional, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import argparse
from datetime import datetime

VERSION = "1.0.0"

LOGO = """
🔄 Hot Reload v{version}
by Gianluca Zugno
"""

USAGE_EXAMPLES = """
Examples:
  1. Basic usage:
     python hot_reload.py test_module
  
  2. Watch a module in Utils directory:
     python hot_reload.py Utils/test
     python hot_reload.py Utils.test
  
  3. Clear console on each reload:
     python hot_reload.py test_module -c
  
  4. Disable UI elements:
     python hot_reload.py test_module -noUI
  
  5. Show version:
     python hot_reload.py -v
"""

def print_version():
    """Print version information with logo."""
    print(LOGO.format(version=VERSION))

class ConsoleUI:
    COLORS = {
        'green': '\033[92m',
        'red': '\033[91m',
        'blue': '\033[94m',
        'yellow': '\033[93m',
        'reset': '\033[0m',
        'bold': '\033[1m'
    }

    @staticmethod
    def clear_console():
        os.system('cls' if os.name == 'nt' else 'clear')

    @staticmethod
    def print_header(module_name: str):
        print(f"""
{ConsoleUI.COLORS['bold']}{'='*60}
🔄 Hot Reload Monitor Active
{'='*60}{ConsoleUI.COLORS['reset']}
📦 Module: {ConsoleUI.COLORS['blue']}{module_name}{ConsoleUI.COLORS['reset']}
⏰ Started at: {ConsoleUI.COLORS['yellow']}{datetime.now().strftime('%H:%M:%S')}{ConsoleUI.COLORS['reset']}
📝 Press Ctrl+C to stop
{'='*60}
""")

    @staticmethod
    def print_success(message: str):
        print(f"\n{ConsoleUI.COLORS['green']}✓ {message}{ConsoleUI.COLORS['reset']}")

    @staticmethod
    def print_error(message: str):
        print(f"\n{ConsoleUI.COLORS['red']}✗ {message}{ConsoleUI.COLORS['reset']}")

class CodeReloader:
    def __init__(self, target_module: str, callback: Optional[Callable] = None, show_ui: bool = True, clear_on_reload: bool = False):
        self.target_module = target_module
        self.callback = callback
        self.module = None
        self.file_hashes: Dict[str, str] = {}
        self.observer = Observer()
        self.watch_path = Path().absolute()
        self.show_ui = show_ui
        self.clear_on_reload = clear_on_reload
        
        # Verify module exists before starting
        self._verify_module_exists()
        
        if self.show_ui:
            ConsoleUI.print_header(self.module_name)
    
    def _verify_module_exists(self):
        """Verify the module exists and set the correct module name."""
        # Try different possible module paths
        base_paths = [
            Path(),  # Current directory
            Path('Utils'),  # Utils directory
        ]
        
        module_path = Path(self.target_module)
        module_name = module_path.stem  # Get name without extension
        
        possible_paths = []
        for base in base_paths:
            possible_paths.extend([
                base / f"{module_name}.py",  # Direct path
                base / module_name / "__init__.py",  # Package
                base / f"{module_path}.py",  # Full path provided
            ])
        
        for path in possible_paths:
            if path.exists():
                # Convert file path to module notation
                self.module_name = str(path.with_suffix('')).replace(os.sep, '.')
                if self.module_name.startswith('.'):
                    self.module_name = self.module_name[1:]
                # Store the actual file path for watching
                self.module_file_path = path
                return
        
        # If we get here, the module wasn't found
        raise ImportError(
            f"Could not find module '{self.target_module}'. Searched in:\n" + 
            "\n".join(f"- {p}" for p in possible_paths) +
            "\n\nMake sure the file exists in either the current directory or the Utils directory."
        )

    def _get_file_hash(self, filepath: str) -> str:
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def _has_file_changed(self, filepath: str) -> bool:
        if not os.path.exists(filepath):
            return False
            
        current_hash = self._get_file_hash(filepath)
        if filepath not in self.file_hashes:
            self.file_hashes[filepath] = current_hash
            return True
            
        if current_hash != self.file_hashes[filepath]:
            self.file_hashes[filepath] = current_hash
            return True
        return False

    def _add_current_dir_to_path(self):
        """Add the current directory and Utils directory to Python's path."""
        paths_to_add = [
            str(self.watch_path),  # Current directory
            str(self.watch_path / 'Utils'),  # Utils directory
        ]
        
        for path in paths_to_add:
            if os.path.exists(path) and path not in sys.path:
                sys.path.insert(0, path)

    def reload_module(self):
        try:
            if self.clear_on_reload:
                ConsoleUI.clear_console()
                if self.show_ui:
                    ConsoleUI.print_header(self.module_name)

            # Add current directory to Python's path
            self._add_current_dir_to_path()

            if self.module is None:
                self.module = importlib.import_module(self.module_name)
            else:
                self.module = importlib.reload(self.module)
                
            if self.callback:
                self.callback(self.module)
            
            if self.show_ui:
                ConsoleUI.print_success(f"Successfully reloaded {self.module_name} at {time.strftime('%H:%M:%S')}")
        except Exception as e:
            if self.show_ui:
                ConsoleUI.print_error(f"Error reloading {self.module_name}: {str(e)}")
                ConsoleUI.print_error(f"Module path: {Path(self.module_name.replace('.', os.sep)).with_suffix('.py')}")

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, reloader: CodeReloader):
        self.reloader = reloader
        
    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            # Convert paths to absolute for comparison
            event_path = Path(event.src_path).resolve()
            module_path = Path(self.reloader.module_file_path).resolve()
            
            if event_path == module_path and self.reloader._has_file_changed(str(event_path)):
                self.reloader.reload_module()

def watch_and_reload(target_module: str, callback: Optional[Callable] = None, show_ui: bool = True, clear_on_reload: bool = False):
    """
    Watch for changes in Python files and reload the target module.
    
    Args:
        target_module: The name of the module to reload (without .py extension)
        callback: Optional callback function to run after successful reload
        show_ui: Whether to show the UI elements
        clear_on_reload: Whether to clear the console on each reload
    """
    target_module = target_module.replace('.py', '')
    
    reloader = CodeReloader(target_module, callback, show_ui, clear_on_reload)
    event_handler = FileChangeHandler(reloader)
    
    reloader.observer.schedule(event_handler, str(reloader.watch_path), recursive=True)
    reloader.observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        reloader.observer.stop()
        if show_ui:
            print(f"\n{ConsoleUI.COLORS['yellow']}Stopping file watch...{ConsoleUI.COLORS['reset']}")
    
    reloader.observer.join()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Hot reload Python modules',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=USAGE_EXAMPLES
    )
    
    parser.add_argument('module', 
                       help='The module to reload (can be a path like "utils/test" or just "test_module")',
                       nargs='?')  # Make module optional to allow -v without module
    
    parser.add_argument('-v', '--version', 
                       action='store_true',
                       help='Show version information')
    
    parser.add_argument('-noUI', 
                       action='store_true', 
                       help='Disable UI elements')
    
    parser.add_argument('-c', '--clear', 
                       action='store_true', 
                       help='Clear console on each reload')
    
    args = parser.parse_args()
    
    # Handle version flag
    if args.version:
        print_version()
        sys.exit(0)
    
    # Check if module is provided when not showing version
    if not args.module:
        parser.print_help()
        sys.exit(1)
    
    try:
        module_name = args.module.replace('.py', '')
        watch_and_reload(module_name, show_ui=not args.noUI, clear_on_reload=args.clear)
    except ImportError as e:
        ConsoleUI.print_error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nStopping hot reload...")
        sys.exit(0)