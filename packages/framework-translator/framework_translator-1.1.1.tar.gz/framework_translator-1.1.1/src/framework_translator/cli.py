import argparse
import sys
from getpass import getpass
from typing import Optional
import tomllib
from pathlib import Path
import json
from datetime import datetime
from .config import (
    load_config,
    check_first_run,
    is_logged_in_session,
    set_session_logged_in,
)
from .framework import registry
from .api_client import api_client
from termcolor import colored
import requests

def get_version() -> str:
    """Get version from pyproject.toml"""
    try:
        # Go up from src/framework_translator/ to the project root
        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        return data["project"]["version"]
    except Exception:
        return "unknown"

def get_supported_languages() -> list[str]:
    return registry.get_supported_languages()

def get_supported_groups(language: str) -> list[str]:
    return registry.get_supported_groups(language)

def get_supported_frameworks(group: str) -> list[str]:
    return registry.get_supported_frameworks(group)

def _read_code_from_stdin() -> str:
    print(colored("Paste source code. Finish with Ctrl-D (Linux/macOS) or Ctrl-Z+Enter (Windows).", "cyan"))
    return sys.stdin.read()

def _read_code_from_prompt() -> str:
    print(colored("Enter source code (end with a single line containing only 'END'):", "cyan"))
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "END":
            break
        lines.append(line)
    return "\n".join(lines)

def _prompt_with_validation(prompt: str, valid_options: list[str], default: Optional[str] = None) -> str:
    """Prompt user with validation until a valid option is selected"""
    while True:
        response = input(colored(prompt, "cyan")).strip().lower()
        
        # Handle default case
        if not response and default:
            return default
        
        # Check if response is in valid options
        if response in [opt.lower() for opt in valid_options]:
            return response
        
        print(colored(f"Invalid option '{response}'. Please choose from: {', '.join(valid_options)}", "red"))

def _prompt_target_framework(group: str) -> str:
    """Prompt for target framework with validation"""
    frameworks = get_supported_frameworks(group)
    while True:
        target_framework = input(colored(f"Choose a target framework -> Target frameworks supported for group {group} [{', '.join(frameworks)}]: ", "cyan")).strip()
        
        if not target_framework:
            print(colored("Target framework is required.", "red"))
            continue
        
        # Check if framework is valid
        target_framework_obj = registry.get_framework_by_name(target_framework)
        if target_framework_obj:
            return target_framework
        
        print(colored(f"Invalid framework '{target_framework}'. Please choose from: {', '.join(frameworks)}", "red"))

def cmd_login(args: argparse.Namespace) -> int:
    print(colored("Login: Framework Translator", "green"))
    
    # Check if already logged in
    if is_logged_in_session():
        print(colored("You are already logged in!", "yellow"))
        choice = input(colored("Do you want to login with different credentials? (y/N): ", "cyan")).strip().lower()
        if choice not in ['y', 'yes']:
            return 0
    
    print(colored("Don't have an account? Register at:", "yellow"))
    print(colored("https://code-translation-frontend-283805296028.us-central1.run.app/register", "cyan"))
    print()
    
    username = input(colored("Username/Email: ", "cyan")).strip()
    if not username:
        print(colored("Username is required.", "red"), file=sys.stderr)
        return 1
    
    password = getpass(colored("Password: ", "cyan"))
    if not password:
        print(colored("Password is required.", "red"), file=sys.stderr)
        return 1
    
    print(colored("Logging in...", "yellow"))
    
    try:
        response = api_client.login(username, password)
        set_session_logged_in(True)
        print(colored("Login successful!", "green"))
        print(colored("You can now use 'ft translate' to translate code.", "green"))
        return 0
    except requests.RequestException as e:
        print(colored(f"Login failed: {e}", "red"), file=sys.stderr)
        print(colored("Please check your credentials and ensure you have registered at:", "yellow"))
        print(colored("https://code-translation-frontend-283805296028.us-central1.run.app/register", "cyan"))
        return 1

def cmd_logout(args: argparse.Namespace) -> int:
    print(colored("Logout: Framework Translator", "green"))
    api_client.logout()  # Clear the stored token
    set_session_logged_in(False)
    print(colored("You have been logged out successfully.", "green"))
    return 0

def cmd_translate(args: argparse.Namespace) -> int:
    # Check if user is logged in
    if not is_logged_in_session():
        print(colored("You must login before using the translate feature.", "red"))
        print(colored("Run 'ft login' to authenticate with the backend.", "yellow"))
        return 1
    
    print(colored("Translate: Framework Translator", "green"))
    
    # Get language with validation
    supported_languages = get_supported_languages()
    language = _prompt_with_validation(
        f"Choose a language -> Languages supported [{', '.join(supported_languages)}]: ",
        supported_languages,
        default="python"
    )

    # Get source framework (optional, no validation needed)
    source_framework = input(colored("Give us your framework: (Enter to let the model infer): ", "cyan")).strip()
    source_framework = source_framework or None
    
    # Get framework group with validation
    supported_groups = get_supported_groups(language)
    group = _prompt_with_validation(
        f"Choose a framework group -> Framework groups supported for language {language} [{', '.join(supported_groups)}]: ",
        supported_groups,
        default="ml"
    )

    # Get target framework with validation
    target_framework = _prompt_target_framework(group)

    code: str
    print(colored("Provide source code via one of the options:", "yellow"))
    print(colored("1) Paste (end with 'END' on its own line)", "cyan"))
    print(colored("2) File path", "cyan"))
    
    # Validate choice input
    while True:
        choice = input(colored("Select [1/2]: ", "yellow")).strip()
        if choice in ["1", "2"]:
            break
        print(colored("Invalid choice. Please enter '1' or '2'.", "red"))
    
    if choice == "2":
        path = input(colored("Enter file path: ", "cyan")).strip()
        try:
            with open(path, "r", encoding="utf-8") as f:
                code = f.read()
        except Exception as e:
            print(colored(f"Failed to read file: {e}", "red"), file=sys.stderr)
            return 1
    else:
        code = _read_code_from_prompt()

    print(colored(f"Translating code to {target_framework}...", "yellow"))

    try:
        # Use backend API for generation
        output = api_client.generate_code(
            code=code,
            target_framework=target_framework,
            source_framework=source_framework
        )
        print(colored("--------------------------------------", "green"))
        print(colored("----------Translation Result----------", "green"))
        print(colored("--------------------------------------", "green"))
        print(output)
        print(colored("--------------------------------------", "green"))
        print(colored("Translation completed successfully.", "green"))
        return 0
    except requests.RequestException as e:
        print(colored(f"Translation failed: {e}", "red"), file=sys.stderr)
        print(colored("Please logout then login again.", "yellow"))
        return 2
    except Exception as e:
        print(colored(f"Translation failed: {e}", "red"), file=sys.stderr)
        return 2

def cmd_history(args: argparse.Namespace) -> int:
    """Display or download translation history"""
    # Check if user is logged in
    if not is_logged_in_session():
        print(colored("You must login before viewing translation history.", "red"))
        print(colored("Run 'ft login' to authenticate with the backend.", "yellow"))
        return 1

    try:
        # Get all translations (using a large per_page to get most/all)
        response = api_client.get_translations(page=1, per_page=1000)
        translations = response.get("translations", [])
        
        if args.download:
            # Download to JSON file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"translation_history_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(translations, f, indent=2, default=str)
            
            print(colored("Downloaded latest translations successfully!", "green"))
            print(colored(f"Saved to: {filename}", "cyan"))
            return 0
        
        # Display translations in a formatted way
        if not translations:
            print(colored("No translation history found.", "yellow"))
            return 0
        
        print(colored(f"Translation History ({len(translations)} total)", "green"))
        print(colored("=" * 60, "green"))
        
        for i, translation in enumerate(translations, 1):
            print(colored(f"\n[{i}] Translation ID: {translation['id']}", "cyan"))
            print(f"   Created: {translation['created_at']}")
            print(f"   Status: {colored(translation['status'], 'green' if translation['status'] == 'completed' else 'red')}")
            
            if translation.get('source_lang'):
                print(f"   Source Framework: {translation['source_lang']}")
            else:
                print(f"   Source Framework: {colored('Auto-detected', 'yellow')}")
                
            print(f"   Target Framework: {translation['target_lang']}")
            
            if translation.get('model_used'):
                print(f"   Model: {translation['model_used']}")
            
            if translation.get('duration_ms'):
                duration_s = translation['duration_ms'] / 1000
                print(f"   Duration: {duration_s:.2f}s")
            
            # Show code preview (first 100 chars)
            if translation.get('source_code'):
                print(f"   Translated Code: {translation['source_code']}")
            
            if translation.get('error_message'):
                print(f"   Error: {colored(translation['error_message'], 'red')}")
        
        print(colored("\n" + "=" * 60, "green"))
        print(colored(f"Use 'ft history -d' to download history as JSON file.", "cyan"))
        
        return 0
        
    except requests.RequestException as e:
        print(colored(f"Failed to fetch translation history: {e}", "red"), file=sys.stderr)
        return 1
    except Exception as e:
        print(colored(f"Error: {e}", "red"), file=sys.stderr)
        return 1

def cmd_version(args: argparse.Namespace) -> int:
    print(f"Framework Translator v{get_version()}")
    return 0

def main(argv: Optional[list[str]] = None) -> int:
    check_first_run()
    parser = argparse.ArgumentParser(prog="ft", description="Translate code across frameworks using an OpenAI fine-tuned model.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_login = sub.add_parser("login", help="Login to the backend service.")
    p_login.set_defaults(func=cmd_login)

    p_logout = sub.add_parser("logout", help="Logout from the backend service.")
    p_logout.set_defaults(func=cmd_logout)

    p_tx = sub.add_parser("translate", help="Translate source code to a target framework.")
    p_tx.set_defaults(func=cmd_translate)

    p_history = sub.add_parser("history", help="View or download translation history.")
    p_history.add_argument("-d", "--download", action="store_true", help="Download history to JSON file instead of displaying")
    p_history.set_defaults(func=cmd_history)

    p_version = sub.add_parser("version", help="Show the current version of the tool.")
    p_version.set_defaults(func=cmd_version)

    def _cmd_help(args: argparse.Namespace) -> int:
        if getattr(args, "topic", None) == "translate":
            p_tx.print_help()
        elif getattr(args, "topic", None) == "login":
            p_login.print_help()
        elif getattr(args, "topic", None) == "logout":
            p_logout.print_help()
        elif getattr(args, "topic", None) == "history":
            p_history.print_help()
        else:
            parser.print_help()
        return 0

    p_help = sub.add_parser("help", help="Show general help or help for a specific subcommand.")
    p_help.add_argument("topic", nargs="?", choices=["translate", "login", "logout", "history"], help="Subcommand to show help for.")
    p_help.set_defaults(func=_cmd_help)

    args = parser.parse_args(argv)
    return args.func(args)

if __name__ == "__main__":
    raise SystemExit(main())