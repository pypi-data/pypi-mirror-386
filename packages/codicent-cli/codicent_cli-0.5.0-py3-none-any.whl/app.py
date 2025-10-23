import sys
import os
import logging
import glob
import requests
import base64
import json
from codicentpy import Codicent
from rich.console import Console
from rich.markdown import Markdown
from prompt_toolkit import prompt
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.filters import Condition
from auth import CodicentAuth

# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def show_help():
    """Display help information."""
    help_text = """
Codicent CLI - Command-line interface for the Codicent API

USAGE:
    codicent [OPTIONS] [QUESTION]
    codicent [OPTIONS] < file.txt
    echo "question" | codicent [OPTIONS]
    codicent upload <file_pattern> [<file_pattern> ...]

OPTIONS:
    -t, --interactive    Start interactive chat mode
    -h, --help          Show this help message
    -v, --version       Show version information
    --verbose           Enable verbose logging
    --quiet             Suppress non-essential output

AUTHENTICATION:
    auth                Authenticate using device flow (project selected during web auth)
    logout              Clear stored authentication
    status              Check authentication status

FILE UPLOAD:
    upload              Upload files and post messages with tags
    
    Example:
        codicent upload file.txt *.log
        
    This uploads the files and posts a message for each file with:
        @project #index #summarize #file:FILE_GUID

EXAMPLES:
    codicent auth
    codicent "What is Python?"
    codicent -t
    codicent "@mention Hello there"
    codicent upload document.txt *.log
    echo "Help me debug this" | codicent

ENVIRONMENT:
    CODICENT_TOKEN     Your Codicent API token (fallback if no cached auth)

For more information, visit: https://github.com/izaxon/codicent-cli
"""
    print(help_text.strip())

def show_version():
    """Display version information."""
    print("Codicent CLI v0.5.0")

def validate_input(question):
    """Validate user input."""
    if not question or not question.strip():
        return False, "Empty question provided"
    
    if len(question) > 10000:  # Reasonable limit
        return False, "Question too long (max 10,000 characters)"
    
    return True, None

def main():
    console = Console()
    
    # Parse command line arguments
    if "-h" in sys.argv or "--help" in sys.argv:
        show_help()
        return 0
    
    if "-v" in sys.argv or "--version" in sys.argv:
        show_version()
        return 0
    
    # Set logging level based on flags
    if "--verbose" in sys.argv:
        logging.getLogger().setLevel(logging.INFO)
        sys.argv.remove("--verbose")
        logger.info("Verbose logging enabled")
    
    if "--quiet" in sys.argv:
        logging.getLogger().setLevel(logging.ERROR)
        sys.argv.remove("--quiet")
    
    # Initialize auth handler
    auth = CodicentAuth()
    
    # Handle authentication commands
    if len(sys.argv) > 1 and sys.argv[1] in ["auth", "logout", "status"]:
        command = sys.argv[1]
        
        if command == "auth":
            # No project parameter needed - user selects project during web authorization
            token = auth.get_token(force_reauth=True)
            if token:
                console.print("[green]✅ Authentication successful![/green]")
                return 0
            else:
                console.print("[red]❌ Authentication failed[/red]")
                return 1
        
        elif command == "logout":
            auth.logout()
            return 0
        
        elif command == "status":
            token = auth.get_cached_token()
            if token:
                console.print("[green]✅ Authenticated (cached token available)[/green]")
                return 0
            else:
                env_token = os.getenv("CODICENT_TOKEN")
                if env_token:
                    console.print("[yellow]⚠ Using CODICENT_TOKEN environment variable[/yellow]")
                    console.print("[dim]Consider running 'codicent auth' to use persistent authentication[/dim]")
                    return 0
                else:
                    console.print("[red]❌ Not authenticated[/red]")
                    console.print("[dim]Run 'codicent auth' to authenticate[/dim]")
                    return 1
    
    # Handle upload command
    if len(sys.argv) > 1 and sys.argv[1] == "upload":
        if len(sys.argv) < 3:
            console.print("[red]❌ Error: No files specified for upload[/red]")
            console.print("[dim]Usage: codicent upload <file_pattern> [<file_pattern> ...][/dim]")
            console.print("[dim]Example: codicent upload file.txt *.log[/dim]")
            return 1
        
        # Get authentication token
        token = auth.get_cached_token()
        if not token:
            # Fallback to environment variable
            token = os.getenv("CODICENT_TOKEN")
            if not token:
                console.print("[red]❌ No authentication found.[/red]")
                console.print("[dim]Run 'codicent auth' to authenticate, or set CODICENT_TOKEN environment variable[/dim]")
                return 1
            else:
                logger.info("Using CODICENT_TOKEN environment variable")
        
        # Initialize API client with error handling
        try:
            codicent = Codicent(token)
            logger.info("Codicent API client initialized successfully")
        except Exception as e:
            console.print(f"[red]❌ Failed to initialize Codicent API client: {e}[/red]")
            logger.error(f"API client initialization failed: {e}")
            console.print("[dim]Try running 'codicent auth' to re-authenticate[/dim]")
            return 1
        
        # Extract project from JWT token
        try:
            payload = token.split(".")[1]
            payload += '=' * (-len(payload) % 4)
            decoded_payload = base64.urlsafe_b64decode(payload).decode('utf-8')
            jwt_data = json.loads(decoded_payload)
            project = jwt_data["project"]
        except Exception as e:
            console.print(f"[red]❌ Failed to extract project from token: {e}[/red]")
            return 1
        
        # Collect all files from patterns
        file_patterns = sys.argv[2:]
        files_to_upload = []
        
        for pattern in file_patterns:
            matched_files = glob.glob(pattern)
            if matched_files:
                files_to_upload.extend(matched_files)
            else:
                # If no glob match, check if it's a direct file path
                if os.path.isfile(pattern):
                    files_to_upload.append(pattern)
                else:
                    console.print(f"[yellow]⚠ Warning: No files found matching pattern '{pattern}'[/yellow]")
        
        if not files_to_upload:
            console.print("[red]❌ Error: No files found to upload[/red]")
            return 1
        
        # Remove duplicates while preserving order
        files_to_upload = list(dict.fromkeys(files_to_upload))
        
        console.print(f"[dim]Found {len(files_to_upload)} file(s) to upload[/dim]")
        
        # Upload each file and post a message
        uploaded_count = 0
        failed_count = 0
        
        for filepath in files_to_upload:
            try:
                filename = os.path.basename(filepath)
                console.print(f"[dim]Uploading {filename}...[/dim]")
                
                with console.status(f"[dim]Uploading {filename}...[/dim]", spinner="dots"):
                    # Upload the file
                    with open(filepath, 'rb') as file:
                        url = f"{codicent.base_url}app/UploadFile"
                        files = {"file": file}
                        params = {"filename": filename}
                        response = requests.post(url, files=files, params=params, verify=codicent.verify_https)
                        if response.ok:
                            file_guid = response.json()
                        else:
                            raise Exception(f"Upload failed: {response.status_code} - {response.text}")

                    # Post a message with the file reference
                    # Get project name from first @ mention if available, otherwise use @myproject
                    message = f"@{project} #index #summarize #file:{file_guid}"
                    codicent.post_message(message, type="info")
                
                console.print(f"[green]✅ Uploaded: {filename} (File ID: {file_guid})[/green]")
                uploaded_count += 1
                
            except FileNotFoundError:
                console.print(f"[red]❌ File not found: {filepath}[/red]")
                failed_count += 1
            except PermissionError:
                console.print(f"[red]❌ Permission denied: {filepath}[/red]")
                failed_count += 1
            except Exception as e:
                console.print(f"[red]❌ Failed to upload {filename}: {e}[/red]")
                logger.error(f"Upload failed for {filepath}: {e}")
                failed_count += 1
        
        # Summary
        console.print()
        console.print(f"[bold]Upload Summary:[/bold]")
        console.print(f"  [green]✅ Uploaded: {uploaded_count}[/green]")
        if failed_count > 0:
            console.print(f"  [red]❌ Failed: {failed_count}[/red]")
        
        return 0 if failed_count == 0 else 1
    
    # Get authentication token
    token = auth.get_cached_token()
    if not token:
        # Fallback to environment variable
        token = os.getenv("CODICENT_TOKEN")
        if not token:
            console.print("[red]❌ No authentication found.[/red]")
            console.print("[dim]Run 'codicent auth' to authenticate, or set CODICENT_TOKEN environment variable[/dim]")
            return 1
        else:
            logger.info("Using CODICENT_TOKEN environment variable")
    
    # Initialize API client with error handling
    try:
        codicent = Codicent(token)
        logger.info("Codicent API client initialized successfully")
    except Exception as e:
        console.print(f"[red]❌ Failed to initialize Codicent API client: {e}[/red]")
        logger.error(f"API client initialization failed: {e}")
        console.print("[dim]Try running 'codicent auth' to re-authenticate[/dim]")
        return 1
    
    conversationId = None

    # Parse interactive mode flags
    interactive = False
    if "-t" in sys.argv or "--interactive" in sys.argv:
        interactive = True
        if "-t" in sys.argv:
            sys.argv.remove("-t")
        if "--interactive" in sys.argv:
            sys.argv.remove("--interactive")
    elif len(sys.argv) == 1:
        interactive = True
        
    # Get input based on mode (skip if we already handled auth commands)
    question = ""
    if not interactive:
        if len(sys.argv) < 2:
            if sys.stdin.isatty():
                console.print("Usage: codicent <question> or codicent < chat.txt or cat chat.txt | codicent or codicent (equal to codicent -t)")
                console.print("Use 'codicent --help' for more information.")
                return 1
            try:
                question = sys.stdin.read().strip()
            except (KeyboardInterrupt, EOFError):
                return 1
        else:
            question = " ".join(sys.argv[1:])
    else:
        if len(sys.argv) > 1:
            question = " ".join(sys.argv[1:])
        elif not sys.stdin.isatty():
            try:
                question = sys.stdin.read().strip()
            except (KeyboardInterrupt, EOFError):
                return 1

    def handle_question(question):
        nonlocal conversationId
        
        # Validate input
        is_valid, error_msg = validate_input(question)
        if not is_valid:
            print(f"Error: {error_msg}")
            logger.warning(f"Invalid input: {error_msg}")
            return False
        
        console = Console()
        
        try:
            if question.strip().startswith("@"):
                logger.info("Sending message to Codicent API")
                with console.status("[dim]Sending message...[/dim]", spinner="dots"):
                    response = codicent.post_message(question, type="info")
                console.print("[green]✅ Message posted successfully.[/green]")
            else:
                logger.info("Sending chat reply to Codicent API")
                with console.status("[dim]🤔 Thinking...[/dim]", spinner="dots"):
                    response = codicent.post_chat_reply(question, conversationId)
                conversationId = response["id"]
                logger.info(f"Updated conversation ID: {conversationId}")
                
                # Show bot response with markdown formatting in green
                if interactive:
                    console.print()
                
                # Create markdown with green styling
                from rich.text import Text
                markdown_content = Markdown(response["content"])
                console.print(markdown_content, style="green")
                console.print()
            
            return True
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Operation cancelled by user[/yellow]")
            return False
        except ConnectionError as e:
            console.print(f"[red]Network error: Unable to connect to Codicent API[/red]")
            logger.error(f"Connection error: {e}")
            return False
        except Exception as e:
            console.print(f"[red]API error: {e}[/red]")
            logger.error(f"API call failed (CODICENT_API_TOKEN expired?): {e}")
            return False

    # Handle initial question if provided
    if question != "":
        success = handle_question(question)
        if not success and not interactive:
            return 1
    
    # Interactive mode loop
    if interactive:
        console = Console()
        console.print("\n[bold green]🤖 Codicent CLI Interactive Mode[/bold green]")
        console.print("[dim]Type your questions or use Ctrl+C to exit.[/dim]")
        console.print("[dim]Prefix with @ for info messages.[/dim]")
        console.print("[dim]Enter: send | Alt+Enter: new line | Paste: multi-line supported[/dim]")
        console.print("─" * 50)
        
        # Create custom key bindings
        bindings = KeyBindings()

        @bindings.add(Keys.Enter)
        def _(event):
            """Enter submits the input."""
            event.current_buffer.validate_and_handle()

        @bindings.add(Keys.Escape, Keys.Enter)  # Alt+Enter
        def _(event):
            """Alt+Enter inserts a newline."""
            event.current_buffer.insert_text('\n')

        while True:
            try:
                # Use prompt_toolkit's prompt instead of input()
                question = prompt(
                    "¤ ",
                    multiline=True,
                    key_bindings=bindings,
                    prompt_continuation=""  # No continuation prompt for clean look
                )
            except KeyboardInterrupt:
                console.print("\n[yellow]👋 Goodbye![/yellow]")
                break
            except EOFError:
                break
            
            if question.strip() != "":
                handle_question(question)
                # Add a separator line after each interaction
                if question.strip() != "" and not question.strip().startswith("@"):
                    console.print("[dim]" + "─" * 50 + "[/dim]")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
