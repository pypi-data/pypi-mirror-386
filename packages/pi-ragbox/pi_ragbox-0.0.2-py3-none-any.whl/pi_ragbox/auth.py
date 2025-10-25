"""Authentication flow for pi-ragbox CLI."""

import webbrowser
import socket
import threading
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional, Tuple
from .config import get_base_url, save_credentials, save_default_project, get_config_option, set_config_option
from .api import APIClient


class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback."""

    cookies: Optional[dict] = None
    email: Optional[str] = None
    error: Optional[str] = None

    def do_GET(self):
        """Handle GET request with OAuth callback."""
        # Parse query parameters
        parsed_path = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed_path.query)

        if "cookies" in params:
            # Cookies are passed as a JSON-encoded string
            import json
            CallbackHandler.cookies = json.loads(params["cookies"][0])
            CallbackHandler.email = params.get("email", [None])[0]
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            html_content = """
                <html>
                <head><title>Authentication Successful</title></head>
                <body style="font-family: system-ui; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; background: #f5f5f5;">
                    <div style="text-align: center; background: white; padding: 3rem; border-radius: 1rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <h1 style="color: #10b981; margin-bottom: 1rem;">&#10003; Authentication Successful!</h1>
                        <p style="color: #6b7280; margin-bottom: 1rem;">You can now close this window and return to your terminal.</p>
                        <p style="color: #9ca3af; font-size: 0.875rem;">pi-ragbox CLI</p>
                    </div>
                </body>
                </html>
                """
            self.wfile.write(html_content.encode('utf-8'))
        elif "error" in params:
            CallbackHandler.error = params["error"][0]
            self.send_response(400)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            html_content = """
                <html>
                <head><title>Authentication Failed</title></head>
                <body style="font-family: system-ui; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; background: #f5f5f5;">
                    <div style="text-align: center; background: white; padding: 3rem; border-radius: 1rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <h1 style="color: #ef4444; margin-bottom: 1rem;">&#10007; Authentication Failed</h1>
                        <p style="color: #6b7280; margin-bottom: 1rem;">Please try again or check your terminal for more information.</p>
                        <p style="color: #9ca3af; font-size: 0.875rem;">pi-ragbox CLI</p>
                    </div>
                </body>
                </html>
                """
            self.wfile.write(html_content.encode('utf-8'))
        else:
            self.send_response(400)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Invalid callback request")

    def log_message(self, format, *args):
        """Suppress log messages."""
        pass


def find_available_port(start_port: int = 8080, end_port: int = 8180) -> int:
    """Find an available port in the given range.

    Args:
        start_port: Starting port to check
        end_port: Ending port to check

    Returns:
        Available port number

    Raises:
        OSError: If no available port is found
    """
    for port in range(start_port, end_port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("localhost", port))
                return port
        except OSError:
            continue
    raise OSError("No available ports found in range")


def start_callback_server(port: int, timeout: int = 120) -> Tuple[Optional[dict], Optional[str], Optional[str]]:
    """Start a local HTTP server to receive the OAuth callback.

    Args:
        port: Port to listen on
        timeout: Timeout in seconds

    Returns:
        Tuple of (cookies, email, error). Cookies and email will be None if error occurred.
    """
    server = HTTPServer(("localhost", port), CallbackHandler)
    server.timeout = timeout

    # Reset class variables
    CallbackHandler.cookies = None
    CallbackHandler.email = None
    CallbackHandler.error = None

    # Handle one request (the callback)
    server.handle_request()

    return CallbackHandler.cookies, CallbackHandler.email, CallbackHandler.error


def open_browser_for_login(callback_port: int) -> bool:
    """Open the user's browser to the login page.

    Args:
        callback_port: The port where the callback server is listening

    Returns:
        True if browser was opened successfully, False otherwise
    """
    base_url = get_base_url()
    callback_url = f"http://localhost:{callback_port}/callback"
    login_url = f"{base_url}/api/auth/cli-login?redirect={urllib.parse.quote(callback_url)}"

    try:
        return webbrowser.open(login_url)
    except:
        return False


def login_flow() -> Tuple[bool, str]:
    """Execute the login flow.

    Returns:
        Tuple of (success, message)
    """
    try:
        # Find an available port
        port = find_available_port()
    except OSError:
        return False, "Failed to find an available port for callback server"

    # Construct the callback URL that will be shown to the user
    callback_url = f"http://localhost:{port}/callback"
    base_url = get_base_url()
    login_url = f"{base_url}/api/auth/cli-login?redirect={urllib.parse.quote(callback_url)}"

    # Start the callback server in a background thread
    server_thread = threading.Thread(
        target=lambda: start_callback_server(port),
        daemon=True
    )
    server_thread.start()

    # Try to open the browser
    browser_opened = open_browser_for_login(port)

    if browser_opened:
        print(f"Opening browser for authentication...\n\nIf the browser doesn't open, visit:\n{login_url}")
    else:
        print(f"Please visit this URL to authenticate:\n{login_url}")

    # Wait for the server thread to complete (with timeout)
    server_thread.join(timeout=120)

    # Check if we got cookies
    if CallbackHandler.cookies:
        cookies = CallbackHandler.cookies
        email = CallbackHandler.email or "authenticated_user"

        # Validate the cookies by trying to get projects
        try:
            client = APIClient(cookies=cookies)
            projects = client.get_projects()

            # Save credentials first
            save_credentials(cookies, user_email=email)

            # Prompt for ragbox_repo path
            current_ragbox_repo = get_config_option("ragbox_repo")
            if current_ragbox_repo:
                prompt_msg = f"\nRagbox repository path [{current_ragbox_repo}]: "
            else:
                prompt_msg = "\nRagbox repository path (press Enter to skip): "

            try:
                new_path = input(prompt_msg).strip()

                if new_path:
                    # User entered a new path
                    from pathlib import Path
                    # Expand user home directory (~) and make absolute
                    path_obj = Path(new_path).expanduser().resolve()
                    expanded_path = str(path_obj)

                    if not path_obj.exists():
                        print(f"⚠ Warning: Path does not exist: {expanded_path}")
                        confirm = input("Set it anyway? (y/n): ").strip().lower()
                        if confirm != 'y':
                            print("Skipped setting ragbox_repo.")
                        else:
                            set_config_option("ragbox_repo", expanded_path)
                            print(f"✓ Set ragbox_repo to: {expanded_path}")
                    else:
                        set_config_option("ragbox_repo", expanded_path)
                        print(f"✓ Set ragbox_repo to: {expanded_path}")
                elif current_ragbox_repo:
                    # User pressed Enter with existing value
                    print(f"✓ Kept ragbox_repo: {current_ragbox_repo}")
                else:
                    # User pressed Enter with no existing value
                    print("Skipped setting ragbox_repo.")

            except (KeyboardInterrupt, EOFError):
                print("\nSkipped setting ragbox_repo.")

            # If there are projects, prompt user to select a default
            if projects:
                print(f"\n✓ Found {len(projects)} project(s).")
                print("\nPlease select a default project:")

                for idx, project in enumerate(projects, 1):
                    project_name = project.get("name", "Unnamed")
                    project_id = project.get("id", "N/A")
                    print(f"  {idx}. {project_name} (ID: {project_id})")

                # Prompt for selection
                while True:
                    try:
                        choice = input("\nEnter project number (or press Enter to skip): ").strip()

                        if not choice:
                            # User skipped selection
                            print("No default project selected.")
                            break

                        choice_num = int(choice)
                        if 1 <= choice_num <= len(projects):
                            project_id = projects[choice_num - 1]["id"]
                            project_name = projects[choice_num - 1].get("name", "Unnamed")
                            save_default_project(project_id)
                            print(f"✓ Set default project to: {project_name}")
                            break
                        else:
                            print(f"Please enter a number between 1 and {len(projects)}")
                    except ValueError:
                        print("Please enter a valid number")
                    except (KeyboardInterrupt, EOFError):
                        print("\nNo default project selected.")
                        break

            return True, f"Successfully authenticated as {email}!"

        except Exception as e:
            return False, f"Authentication failed: {str(e)}"

    elif CallbackHandler.error:
        return False, f"Authentication failed: {CallbackHandler.error}"

    else:
        return False, "Authentication timed out. Please try again."
