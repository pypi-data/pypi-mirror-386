"""
Main CLI entry point for fastWorkflow.
"""

import argparse
import contextlib
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
import importlib.resources
from rich import print as rprint
from rich.live import Live
from rich.spinner import Spinner

_examples_dir_cache = None

def find_examples_dir():
    """Finds the bundled examples directory using importlib.resources."""
    global _examples_dir_cache
    
    # Return cached result if available
    if _examples_dir_cache is not None:
        return _examples_dir_cache
        
    with contextlib.suppress(ModuleNotFoundError, FileNotFoundError):
        # Use files() for robust path handling with importlib.resources
        resources_path = importlib.resources.files('fastworkflow')
        examples_path = resources_path / 'examples'
        if examples_path.is_dir():
            _examples_dir_cache = (examples_path, True)  # True indicates package examples
            return _examples_dir_cache
    
    # If not found in the package, look in the project root
    project_root = Path.cwd()
    examples_path = project_root / 'examples'
    
    if examples_path.is_dir():
        _examples_dir_cache = (examples_path, False)
    else:
        _examples_dir_cache = (None, False)
        
    return _examples_dir_cache

def list_examples(args):
    """List available bundled examples."""
    # Create a spinner for searching
    spinner = Spinner("dots", text="[bold green]Searching for examples...[/bold green]")
    
    # Use Live display for the spinner
    with Live(spinner, refresh_per_second=10):
        # Add a small delay to show the spinner (the actual search is very fast if cached)
        time.sleep(0.3)
        examples_dir, is_package = find_examples_dir()

    if not examples_dir:
        rprint("[bold red]Error:[/bold red] Could not find the bundled 'examples' directory.")
        sys.exit(1)

    rprint("\n[bold]Available examples:[/bold]")
    for item in sorted(examples_dir.iterdir()):
        if item.is_dir() and not item.name.startswith('_'):
            rprint(f"- {item.name}")

def fetch_example(args):
    """Fetch a bundled example and copy it to the local filesystem."""
    # Create a spinner for searching
    spinner = Spinner("dots", text="[bold green]Fetching example...[/bold green]")
    
    # Use Live display for the spinner
    with Live(spinner, refresh_per_second=10):
        examples_dir, is_package = find_examples_dir()

    if not examples_dir:
        rprint("[bold red]Error:[/bold red] Could not find the bundled 'examples' directory.")
        sys.exit(1)

    source_path = examples_dir / args.name
    if not source_path.is_dir():
        rprint(f"[bold red]Error:[/bold red] Example '{args.name}' not found.")
        rprint("Use 'fastworkflow examples list' to see available examples.")
        sys.exit(1)

    # If examples are only found locally (not in package), skip the fetch operation
    if not is_package:
        rprint(f"Note: Example '{args.name}' is already in the local examples directory.")
        return source_path

    target_root = Path("./examples")
    target_path = target_root / args.name

    if target_path.exists() and not getattr(args, 'force', False):
        # Ask user for confirmation before overwriting
        response = input(f"Target directory '{target_path}' already exists. Overwrite? [y/N] ")
        if response.lower() != 'y':
            rprint("Operation cancelled.")
            sys.exit(0)
        
    target_root.mkdir(exist_ok=True)

    # Ignore generated files during copy
    ignore_patterns = shutil.ignore_patterns('___command_info', '__pycache__', '*.pyc')

    try:
        # Create a spinner for copying
        copy_spinner = Spinner("dots", text="[bold green]Copying files...[/bold green]")
        
        # Use Live display for the spinner
        with Live(copy_spinner, refresh_per_second=10):
            # Copy the example directory
            shutil.copytree(source_path, target_path, ignore=ignore_patterns, dirs_exist_ok=True)
            
            # Also copy the environment files from the examples directory if they don't exist locally
            env_file = examples_dir / "fastworkflow.env"
            passwords_file = examples_dir / "fastworkflow.passwords.env"
            
            local_env_file = target_root / "fastworkflow.env"
            local_passwords_file = target_root / "fastworkflow.passwords.env"
            
            # Check if env file exists locally before copying
            if env_file.exists() and not local_env_file.exists():
                shutil.copy2(env_file, local_env_file)
                time.sleep(0.5)  # Small delay to show the spinner
            
            # Check if passwords file exists locally before copying
            if passwords_file.exists():
                if not local_passwords_file.exists():
                    shutil.copy2(passwords_file, local_passwords_file)
                    time.sleep(0.5)  # Small delay to show the spinner
            elif not local_passwords_file.exists():
                # Create a template passwords file if the original doesn't exist and local one doesn't exist
                with open(local_passwords_file, "w") as f:
                    f.write("# Add your API keys below\n")
                    f.write("LITELLM_API_KEY_SYNDATA_GEN=<API KEY for synthetic data generation model>\n")
                    f.write("LITELLM_API_KEY_PARAM_EXTRACTION=<API KEY for parameter extraction model>\n")
                    f.write("LITELLM_API_KEY_RESPONSE_GEN=<API KEY for response generation model>\n")
                    f.write("LITELLM_API_KEY_AGENT=<API KEY for the agent model>\n")
        
        # After copying, show the results
        if env_file.exists():
            if not local_env_file.exists():
                rprint(f"✅ Copied environment file to '{local_env_file}'")
            else:
                rprint(f"⚠️ Environment file already exists at '{local_env_file}', skipping copy")
            
            # Remind users to add their API keys
            rprint("\n[bold]NOTE:[/bold] You need to add your API keys to the passwords file before training.")
            rprint(f"      Edit '{local_passwords_file}' with your API keys.")
        else:
            rprint(f"⚠️ [yellow]Warning:[/yellow] Environment file not found at '{env_file}'")
        
        # Check if passwords file exists locally before copying
        if passwords_file.exists():
            if not local_passwords_file.exists():
                rprint(f"✅ Copied passwords file to '{local_passwords_file}'")
            else:
                rprint(f"⚠️ Passwords file already exists at '{local_passwords_file}', skipping copy")
        else:
            rprint(f"⚠️ [yellow]Warning:[/yellow] Passwords file not found at '{passwords_file}'")
            
            # Create a template passwords file if the original doesn't exist and local one doesn't exist
            if not local_passwords_file.exists():
                rprint(f"✅ Created template passwords file at '{local_passwords_file}'")
            else:
                rprint(f"⚠️ Using existing passwords file at '{local_passwords_file}'")
        
        rprint(f"\n✅ Example '{args.name}' copied to '{target_path}'")
        return target_path
    except Exception as e:
        rprint(f"[bold red]Error copying example:[/bold red] {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

def find_default_env_files(workflow_path):
    """Find the appropriate default env files based on context.
    
    If the workflow path is within the examples directory, use the local examples env files.
    Otherwise, use local .env files in the current directory.
    
    Args:
        workflow_path: Optional path to the workflow directory
        
    Returns:
        tuple: (env_file_path, passwords_file_path)
    """
    # Resolve the workflow path to absolute path to handle relative paths correctly
    workflow_path = Path(workflow_path).resolve()        
    return workflow_path / "fastworkflow.env", workflow_path / "fastworkflow.passwords.env"

def add_build_parser(subparsers):
    """Add subparser for the 'build' command."""
    parser_build = subparsers.add_parser(
        "build",
        help="Generate FastWorkflow command files and context model from a Python application.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser_build.add_argument('--app-dir', '-s', required=True, help='Path to the source code directory of the application')
    parser_build.add_argument('--workflow-folderpath', '-w', required=True, help='Path to the workflow folder where commands will be generated')
    parser_build.add_argument('--overwrite', action='store_true', help='Overwrite files in output directory if present')
    parser_build.add_argument('--stub-commands', help='Comma-separated list of command names to generate stubs for')
    parser_build.add_argument('--no-startup', action='store_true', help='Skip generating the startup.py file')

    # Lazy-import build_main only if the user actually invokes the command
    def _build_main_wrapper(args):
        from .build.__main__ import build_main as _build_main
        return _build_main(args)

    parser_build.set_defaults(func=_build_main_wrapper)

def add_refine_parser(subparsers):
    """Add subparser for the 'refine' command."""
    parser_refine = subparsers.add_parser(
        "refine",
        help="Refine generated commands: enhance metadata and build dependency graph.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser_refine.add_argument('--workflow-folderpath', '-w', required=True, help='Path to the workflow folder to refine')
    parser_refine.add_argument('--semantic-threshold', type=float, default=0.85, help='Semantic match threshold for dependency graph')
    parser_refine.add_argument('--exact-only', action='store_true', help='Use exact name/type matching only for dependency graph')

    # Lazy-import refine_main only if the user actually invokes the command
    def _refine_main_wrapper(args):
        from .refine.__main__ import refine_main as _refine_main
        return _refine_main(args)

    parser_refine.set_defaults(func=_refine_main_wrapper)

def add_train_parser(subparsers):
    """Add subparser for the 'train' command."""
    parser_train = subparsers.add_parser("train", help="Train the intent detection pipeline for a workflow.")
    parser_train.add_argument("workflow_folderpath", help="Path to the workflow folder")
    
    # Default env files will be determined at runtime based on the workflow path
    parser_train.add_argument(
        "env_file_path",
        nargs='?',
        default=None,
        help="Path to the environment file (default: .env in current directory, or bundled env file for examples)",
    )
    parser_train.add_argument(
        "passwords_file_path",
        nargs='?',
        default=None,
        help="Path to the passwords file (default: passwords.env in current directory, or bundled env file for examples)",
    )
    parser_train.set_defaults(func=lambda args: train_with_defaults(args))

def add_run_parser(subparsers):
    """Add subparser for the 'run' command."""
    parser_run = subparsers.add_parser("run", help="Run a workflow's interactive assistant.")
    parser_run.add_argument("workflow_path", help="Path to the workflow folder")
    
    # Default env files will be determined at runtime based on the workflow path
    parser_run.add_argument(
        "env_file_path",
        nargs='?',
        default=None,
        help="Path to the environment file (default: .env in current directory, or bundled env file for examples)",
    )
    parser_run.add_argument(
        "passwords_file_path",
        nargs='?',
        default=None,
        help="Path to the passwords file (default: passwords.env in current directory, or bundled env file for examples)",
    )
    parser_run.add_argument("--context_file_path", help="Optional context file path", default="")
    parser_run.add_argument("--startup_command", help="Optional startup command", default="")
    parser_run.add_argument("--startup_action", help="Optional startup action", default="")
    parser_run.add_argument("--keep_alive", help="Optional keep_alive", default=True)
    parser_run.add_argument("--project_folderpath", help="Optional path to project folder containing application code", default=None)
    parser_run.set_defaults(func=lambda args: run_with_defaults(args))

def add_run_fastapi_mcp_parser(subparsers):
    """Add subparser for the 'run_fastapi_mcp' command."""
    parser_run_fastapi_mcp = subparsers.add_parser("run_fastapi_mcp", help="Run a workflow as a FastAPI server with MCP support.")
    parser_run_fastapi_mcp.add_argument("workflow_path", help="Path to the workflow folder")
    
    # Default env files will be determined at runtime based on the workflow path
    parser_run_fastapi_mcp.add_argument(
        "env_file_path",
        nargs='?',
        default=None,
        help="Path to the environment file (default: .env in current directory, or bundled env file for examples)",
    )
    parser_run_fastapi_mcp.add_argument(
        "passwords_file_path",
        nargs='?',
        default=None,
        help="Path to the passwords file (default: passwords.env in current directory, or bundled env file for examples)",
    )
    parser_run_fastapi_mcp.add_argument("--context", help="Optional context (JSON string)", default=None)
    parser_run_fastapi_mcp.add_argument("--startup_command", help="Optional startup command", default=None)
    parser_run_fastapi_mcp.add_argument("--startup_action", help="Optional startup action (JSON string)", default=None)
    parser_run_fastapi_mcp.add_argument("--project_folderpath", help="Optional path to project folder containing application code", default=None)
    parser_run_fastapi_mcp.add_argument("--port", type=int, default=8000, help="Port to run the FastAPI server on (default: 8000)")
    parser_run_fastapi_mcp.add_argument("--host", default="0.0.0.0", help="Host to bind the FastAPI server to (default: 0.0.0.0)")
    parser_run_fastapi_mcp.set_defaults(func=lambda args: run_fastapi_mcp_with_defaults(args))

def train_with_defaults(args):  # sourcery skip: extract-duplicate-method
    """Wrapper for train_main that sets default env file paths based on context."""
    if args.env_file_path is None or args.passwords_file_path is None:
        default_env, default_passwords = find_default_env_files(args.workflow_folderpath)
    if args.env_file_path is None:
        args.env_file_path = default_env
    if args.passwords_file_path is None:
        args.passwords_file_path = default_passwords

    # Check if the files exist and provide helpful error messages
    if not os.path.exists(args.env_file_path):
        print(f"Error: Environment file not found at: {args.env_file_path}", file=sys.stderr)
        # Check if this is an example workflow
        if "/examples/" in str(args.workflow_folderpath) or "\\examples\\" in str(args.workflow_folderpath):
            example_name = os.path.basename(args.workflow_folderpath)
            print("\nThis appears to be an example workflow. Please run:")
            print(f"  fastworkflow examples fetch {example_name}")
            print(f"  fastworkflow train ./examples/{example_name} ./examples/fastworkflow.env ./examples/fastworkflow.passwords.env")
        else:
            print("\nPlease ensure this file exists with required environment variables.")
            print("You can create a basic .env file in your current directory.")
        sys.exit(1)

    if not os.path.exists(args.passwords_file_path):
        print(f"Error: Passwords file not found at: {args.passwords_file_path}", file=sys.stderr)
        # Check if this is an example workflow
        if "/examples/" in str(args.workflow_folderpath) or "\\examples\\" in str(args.workflow_folderpath):
            example_name = os.path.basename(args.workflow_folderpath)
            print("\nThis appears to be an example workflow. Please run:")
            print(f"  fastworkflow examples fetch {example_name}")
            print(f"  fastworkflow train ./examples/{example_name} ./examples/fastworkflow.env ./examples/fastworkflow.passwords.env")
        else:
            print("\nPlease ensure this file exists with required API keys.")
            print("You can create a basic passwords.env file in your current directory.")
        sys.exit(1)

    # Lazy import here to avoid heavy startup when not needed
    from .train.__main__ import train_main as _train_main
    return _train_main(args)

def run_with_defaults(args):  # sourcery skip: extract-duplicate-method
    """Wrapper for run_main that sets default env file paths based on context."""
    if args.env_file_path is None or args.passwords_file_path is None:
        default_env, default_passwords = find_default_env_files(args.workflow_path)
    if args.env_file_path is None:
        args.env_file_path = default_env
    if args.passwords_file_path is None:
        args.passwords_file_path = default_passwords

    # Check if the files exist and provide helpful error messages
    if not os.path.exists(args.env_file_path):
        print(f"Error: Environment file not found at: {args.env_file_path}", file=sys.stderr)
        # Check if this is an example workflow
        if "/examples/" in str(args.workflow_path) or "\\examples\\" in str(args.workflow_path):
            example_name = os.path.basename(args.workflow_path)
            print("\nThis appears to be an example workflow. Please run:")
            print(f"  fastworkflow examples fetch {example_name}")
            print(f"  fastworkflow train ./examples/{example_name} ./examples/fastworkflow.env ./examples/fastworkflow.passwords.env")
        else:
            print("\nPlease ensure this file exists with required environment variables.")
            print("You can create a basic .env file in your current directory.")
        sys.exit(1)

    if not os.path.exists(args.passwords_file_path):
        print(f"Error: Passwords file not found at: {args.passwords_file_path}", file=sys.stderr)
        # Check if this is an example workflow
        if "/examples/" in str(args.workflow_path) or "\\examples\\" in str(args.workflow_path):
            example_name = os.path.basename(args.workflow_path)
            print("\nThis appears to be an example workflow. Please run:")
            print(f"  fastworkflow examples fetch {example_name}")
            print(f"  fastworkflow train ./examples/{example_name} ./examples/fastworkflow.env ./examples/fastworkflow.passwords.env")
        else:
            print("\nPlease ensure this file exists with required API keys.")
            print("You can create a basic passwords.env file in your current directory.")
        sys.exit(1)

    # Lazy import here to avoid heavy startup when not needed
    from .run.__main__ import run_main as _run_main
    return _run_main(args)

def run_fastapi_mcp_with_defaults(args):  # sourcery skip: extract-duplicate-method
    """Wrapper for fastapi mcp server that sets default env file paths based on context."""
    if args.env_file_path is None or args.passwords_file_path is None:
        default_env, default_passwords = find_default_env_files(args.workflow_path)
    if args.env_file_path is None:
        args.env_file_path = default_env
    if args.passwords_file_path is None:
        args.passwords_file_path = default_passwords

    # Check if the files exist and provide helpful error messages
    if not os.path.exists(args.env_file_path):
        print(f"Error: Environment file not found at: {args.env_file_path}", file=sys.stderr)
        # Check if this is an example workflow
        if "/examples/" in str(args.workflow_path) or "\\examples\\" in str(args.workflow_path):
            example_name = os.path.basename(args.workflow_path)
            print("\nThis appears to be an example workflow. Please run:")
            print(f"  fastworkflow examples fetch {example_name}")
            print(f"  fastworkflow run_fastapi_mcp ./examples/{example_name} ./examples/fastworkflow.env ./examples/fastworkflow.passwords.env")
        else:
            print("\nPlease ensure this file exists with required environment variables.")
            print("You can create a basic .env file in your current directory.")
        sys.exit(1)

    if not os.path.exists(args.passwords_file_path):
        print(f"Error: Passwords file not found at: {args.passwords_file_path}", file=sys.stderr)
        # Check if this is an example workflow
        if "/examples/" in str(args.workflow_path) or "\\examples\\" in str(args.workflow_path):
            example_name = os.path.basename(args.workflow_path)
            print("\nThis appears to be an example workflow. Please run:")
            print(f"  fastworkflow examples fetch {example_name}")
            print(f"  fastworkflow run_fastapi_mcp ./examples/{example_name} ./examples/fastworkflow.env ./examples/fastworkflow.passwords.env")
        else:
            print("\nPlease ensure this file exists with required API keys.")
            print("You can create a basic passwords.env file in your current directory.")
        sys.exit(1)

    # Use subprocess to run python -m fastworkflow.run_fastapi_mcp with the correct arguments
    cmd = [
        sys.executable, '-m', 'fastworkflow.run_fastapi_mcp',
        '--workflow_path', args.workflow_path,
        '--env_file_path', args.env_file_path,
        '--passwords_file_path', args.passwords_file_path,
        '--port', str(args.port),
        '--host', args.host,
    ]
    if args.context:
        cmd.extend(['--context', args.context])
    if args.startup_command:
        cmd.extend(['--startup_command', args.startup_command])
    if args.startup_action:
        cmd.extend(['--startup_action', args.startup_action])
    if args.project_folderpath:
        cmd.extend(['--project_folderpath', args.project_folderpath])
    
    # Run the subprocess
    return subprocess.run(cmd).returncode

def main():
    """Main function for the fastworkflow CLI."""
    
    parser = argparse.ArgumentParser(
        description="fastWorkflow CLI tool for building, training, and running workflows."
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Sub-command help")

    # 'examples' command group
    parser_examples = subparsers.add_parser("examples", help="Manage bundled examples")
    examples_subparsers = parser_examples.add_subparsers(dest="action", required=True)

    # 'examples list' command
    parser_list = examples_subparsers.add_parser("list", help="List available examples")
    parser_list.set_defaults(func=list_examples)

    # 'examples fetch' command
    parser_fetch = examples_subparsers.add_parser("fetch", help="Fetch a specific example")
    parser_fetch.add_argument("name", help="The name of the example to fetch")
    parser_fetch.add_argument("--force", action="store_true", help="Force overwrite if example already exists")
    parser_fetch.set_defaults(func=fetch_example)
    
    # Add top-level commands
    add_build_parser(subparsers)
    add_refine_parser(subparsers)
    add_train_parser(subparsers)
    add_run_parser(subparsers)
    add_run_fastapi_mcp_parser(subparsers)

    try:
        args = parser.parse_args()
        args.func(args)
    except KeyboardInterrupt:
        rprint("\n[bold yellow]Operation cancelled by user.[/bold yellow]")
        sys.exit(0)
    except Exception as e:
        rprint(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 