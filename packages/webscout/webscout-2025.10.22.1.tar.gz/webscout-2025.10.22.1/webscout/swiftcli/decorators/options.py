"""Option decorators for SwiftCLI."""

from typing import Any, Callable, Dict, List, Optional, Union

def option(
    *param_decls: str,
    type: Any = str,
    required: bool = False,
    default: Any = None,
    help: str = None,
    is_flag: bool = False,
    multiple: bool = False,
    count: bool = False,
    prompt: bool = False,
    hide_input: bool = False,
    confirmation_prompt: bool = False,
    prompt_required: bool = True,
    show_default: bool = True,
    choices: Optional[List[Any]] = None,
    case_sensitive: bool = True,
    callback: Optional[Callable] = None,
    hidden: bool = False
) -> Callable:
    """
    Decorator to add an option to a command.
    
    Options are named parameters that can be provided in any order.
    
    Args:
        param_decls: Option names (e.g., "--name", "-n")
        type: Expected type
        required: Whether option is required
        default: Default value
        help: Help text
        is_flag: Whether option is a boolean flag
        multiple: Whether option can be specified multiple times
        count: Whether option counts occurrences
        prompt: Whether to prompt for value if not provided
        hide_input: Whether to hide input when prompting
        confirmation_prompt: Whether to prompt for confirmation
        prompt_required: Whether prompt is required
        show_default: Whether to show default in help
        choices: List of valid choices
        case_sensitive: Whether choices are case sensitive
        callback: Function to process/validate value
        hidden: Whether to hide from help output
        
    Example:
        @command()
        @option("--count", "-c", type=int, default=1)
        @option("--format", type=str, choices=["json", "yaml"])
        @option("--verbose", is_flag=True)
        def process(count: int, format: str, verbose: bool):
            '''Process data'''
            if verbose:
                print(f"Processing {count} items as {format}")
    """
    def decorator(f: Callable) -> Callable:
        if not hasattr(f, '_options'):
            f._options = []
        
        f._options.append({
            'param_decls': param_decls,
            'type': type,
            'required': required,
            'default': default,
            'help': help,
            'is_flag': is_flag,
            'multiple': multiple,
            'count': count,
            'prompt': prompt,
            'hide_input': hide_input,
            'confirmation_prompt': confirmation_prompt,
            'prompt_required': prompt_required,
            'show_default': show_default,
            'choices': choices,
            'case_sensitive': case_sensitive,
            'callback': callback,
            'hidden': hidden
        })
        return f
    return decorator

def envvar(
    name: str,
    type: Any = str,
    required: bool = False,
    default: Any = None,
    help: str = None
) -> Callable:
    """
    Decorator to load option value from environment variable.
    
    Args:
        name: Environment variable name
        type: Expected type
        required: Whether variable is required
        default: Default value if not set
        help: Help text
        
    Example:
        @command()
        @envvar("API_KEY", required=True)
        @envvar("API_URL", default="https://api.example.com")
        def api_call(api_key: str, api_url: str):
            '''Make API call'''
            print(f"Calling {api_url} with key {api_key}")
    """
    def decorator(f: Callable) -> Callable:
        if not hasattr(f, '_envvars'):
            f._envvars = []
        
        f._envvars.append({
            'name': name,
            'type': type,
            'required': required,
            'default': default,
            'help': help
        })
        return f
    return decorator

def config_file(
    path: str = None,
    section: str = None,
    required: bool = False,
    auto_create: bool = True,
    format: str = 'json'
) -> Callable:
    """
    Decorator to load configuration from file.
    
    Args:
        path: Config file path
        section: Config section to load
        required: Whether config is required
        auto_create: Whether to create file if missing
        format: File format (json, yaml, ini)
        
    Example:
        @command()
        @config_file("~/.myapp/config.json")
        def setup(config: dict):
            '''Setup application'''
            print(f"Database: {config.get('database')}")
            
        @command()
        @config_file("config.ini", section="api")
        def api(config: dict):
            '''Make API call'''
            print(f"URL: {config.get('url')}")
    """
    def decorator(f: Callable) -> Callable:
        f._config = {
            'path': path,
            'section': section,
            'required': required,
            'auto_create': auto_create,
            'format': format
        }
        return f
    return decorator

def version_option(
    version: str = None,
    prog_name: str = None,
    message: str = None,
    package_name: str = None
) -> Callable:
    """
    Decorator to add version option to command.
    
    Args:
        version: Version string
        prog_name: Program name
        message: Custom version message
        package_name: Package name to get version from
        
    Example:
        @command()
        @version_option(version="1.0.0")
        def main():
            '''Main command'''
            pass
    """
    def decorator(f: Callable) -> Callable:
        f._version = {
            'version': version,
            'prog_name': prog_name,
            'message': message,
            'package_name': package_name
        }
        return f
    return decorator

def help_option(
    param_decls: List[str] = None,
    help: str = None
) -> Callable:
    """
    Decorator to customize help option.
    
    Args:
        param_decls: Help option flags
        help: Help text
        
    Example:
        @command()
        @help_option(["--help", "-h"], "Show this message")
        def main():
            '''Main command'''
            pass
    """
    def decorator(f: Callable) -> Callable:
        f._help_option = {
            'param_decls': param_decls or ['--help', '-h'],
            'help': help or 'Show this message and exit.'
        }
        return f
    return decorator
