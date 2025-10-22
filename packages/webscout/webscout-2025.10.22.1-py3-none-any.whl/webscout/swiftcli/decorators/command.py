"""Command decorators for SwiftCLI."""

from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union

from ..core.context import Context

def command(
    name: str = None,
    help: str = None,
    aliases: List[str] = None,
    hidden: bool = False
) -> Callable:
    """
    Decorator to register a new command.
    
    This decorator marks a function as a CLI command and provides metadata
    about how the command should be registered and displayed.
    
    Args:
        name: Command name (defaults to function name)
        help: Help text (defaults to function docstring)
        aliases: Alternative names for the command
        hidden: Whether to hide from help output
        
    Example:
        @command(name="greet", help="Say hello")
        def hello(name: str):
            print(f"Hello {name}!")
            
        @command(aliases=["hi", "hey"])
        def hello(name: str):
            '''Say hello to someone'''
            print(f"Hello {name}!")
    """
    def decorator(f: Callable) -> Callable:
        f._command = {
            'name': name or f.__name__,
            'help': help or f.__doc__,
            'aliases': aliases or [],
            'hidden': hidden
        }
        return f
    return decorator

def group(
    name: str = None,
    help: str = None,
    chain: bool = False,
    invoke_without_command: bool = False
) -> Callable:
    """
    Decorator to create a command group.
    
    Command groups can contain subcommands and optionally chain their results.
    
    Args:
        name: Group name (defaults to function name)
        help: Help text (defaults to function docstring)
        chain: Whether to chain command results
        invoke_without_command: Allow group to be invoked without subcommand
        
    Example:
        @group()
        def db():
            '''Database commands'''
            pass
            
        @db.command()
        def migrate():
            '''Run database migrations'''
            print("Running migrations...")
            
        @group(chain=True)
        def process():
            '''Process data'''
            pass
            
        @process.command()
        def validate():
            '''Validate data'''
            return {"valid": True}
    """
    def decorator(f: Callable) -> Callable:
        f._group = {
            'name': name or f.__name__,
            'help': help or f.__doc__,
            'chain': chain,
            'invoke_without_command': invoke_without_command
        }
        return f
    return decorator

def pass_context(f: Callable) -> Callable:
    """
    Decorator to pass CLI context to command.
    
    This decorator injects the current Context object as the first argument
    to the decorated command function.
    
    Example:
        @command()
        @pass_context
        def status(ctx):
            '''Show application status'''
            print(f"App: {ctx.cli.name}")
            print(f"Debug: {ctx.debug}")
    """
    f._pass_context = True
    return f

def completion(func: Optional[Callable] = None) -> Callable:
    """
    Decorator to provide shell completion for a command.
    
    The decorated function should return a list of possible completions
    based on the current incomplete value.
    
    Example:
        @command()
        @option("--service", type=str)
        def restart(service: str):
            '''Restart a service'''
            print(f"Restarting {service}...")
            
        @restart.completion()
        def complete_service(ctx, incomplete):
            services = ["nginx", "apache", "mysql"]
            return [s for s in services if s.startswith(incomplete)]
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(ctx: Context, incomplete: str) -> List[str]:
            try:
                return f(ctx, incomplete)
            except Exception:
                return []
        return wrapper
    
    if func is None:
        return decorator
    return decorator(func)

def argument(
    name: str,
    type: Any = str,
    required: bool = True,
    help: str = None,
    default: Any = None
) -> Callable:
    """
    Decorator to add a command argument.
    
    Arguments are positional parameters that must be provided in order.
    
    Args:
        name: Argument name
        type: Expected type
        required: Whether argument is required
        help: Help text
        default: Default value if not required
        
    Example:
        @command()
        @argument("name")
        @argument("count", type=int, default=1)
        def greet(name: str, count: int):
            '''Greet someone multiple times'''
            for _ in range(count):
                print(f"Hello {name}!")
    """
    def decorator(f: Callable) -> Callable:
        if not hasattr(f, '_arguments'):
            f._arguments = []
        
        f._arguments.append({
            'name': name,
            'type': type,
            'required': required,
            'help': help,
            'default': default
        })
        return f
    return decorator

def flag(
    name: str,
    help: str = None,
    hidden: bool = False
) -> Callable:
    """
    Decorator to add a boolean flag option.
    
    Flags are special options that don't take a value - they're either
    present (True) or absent (False).
    
    Args:
        name: Flag name
        help: Help text
        hidden: Whether to hide from help output
        
    Example:
        @command()
        @flag("--verbose", help="Enable verbose output")
        def process(verbose: bool):
            '''Process data'''
            if verbose:
                print("Verbose mode enabled")
    """
    def decorator(f: Callable) -> Callable:
        if not hasattr(f, '_options'):
            f._options = []
        
        f._options.append({
            'param_decls': [name],
            'is_flag': True,
            'help': help,
            'hidden': hidden
        })
        return f
    return decorator
