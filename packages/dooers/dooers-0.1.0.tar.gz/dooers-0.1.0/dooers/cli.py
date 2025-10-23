import io
import os
import tarfile
import tempfile
import json
import base64
import time
from pathlib import Path

import requests
import typer
from tqdm import tqdm

app = typer.Typer(add_completion=False, help="Dooers CLI")

# Global auth state
AUTH_TOKEN = None

# Token storage file
TOKEN_FILE = Path.home() / ".dooers_token"

def _load_token():
    """Load token from file"""
    global AUTH_TOKEN
    if TOKEN_FILE.exists():
        try:
            AUTH_TOKEN = TOKEN_FILE.read_text().strip()
        except Exception:
            AUTH_TOKEN = None
    return AUTH_TOKEN

def _save_token(token):
    """Save token to file with secure permissions"""
    global AUTH_TOKEN
    AUTH_TOKEN = token
    try:
        TOKEN_FILE.write_text(token)
        # Set secure file permissions (owner read/write only)
        TOKEN_FILE.chmod(0o600)
    except Exception:
        pass

def _clear_token():
    """Clear token from memory and file"""
    global AUTH_TOKEN
    AUTH_TOKEN = None
    try:
        if TOKEN_FILE.exists():
            TOKEN_FILE.unlink()
    except Exception:
        pass


def _is_token_expired(token):
    """Check if JWT token is expired"""
    try:
        # JWT tokens have 3 parts separated by dots
        parts = token.split('.')
        if len(parts) != 3:
            return True
        
        # Decode the payload (second part)
        payload = parts[1]
        # Add padding if needed
        payload += '=' * (4 - len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload)
        data = json.loads(decoded)
        
        # Check expiration
        exp = data.get('exp', 0)
        current_time = int(time.time())
        return current_time >= exp
    except Exception:
        return True


def _get_auth_headers():
    """Get authentication headers for API requests"""
    global AUTH_TOKEN
    if not AUTH_TOKEN:
        _load_token()
    if not AUTH_TOKEN:
        raise typer.Exit("Not authenticated. Run 'dooers login' first.")
    
    # Check if token is expired
    if _is_token_expired(AUTH_TOKEN):
        typer.echo("❌ Your session has expired. Please login again.")
        _clear_token()
        raise typer.Exit("Session expired. Run 'dooers login' first.")
    
    # Use cookie authentication (dev API prefers cookies)
    headers = {
        "Cookie": f"auth={AUTH_TOKEN}"
    }
    return headers


@app.command()
def login(
    email: str = typer.Option(..., prompt=True, help="Your email address"),
    code: str = typer.Option(None, help="Verification code (if not provided, will prompt)"),
):
    """Authenticate with dooers.ai"""
    global AUTH_TOKEN
    
    # Check if already authenticated
    if not AUTH_TOKEN:
        _load_token()
    if AUTH_TOKEN:
        typer.echo("✅ Already authenticated!")
        typer.echo("   Use 'dooers logout' to logout first if you want to re-authenticate")
        return
    
    # Step 1: Request session (get OTP sent to email)
    typer.echo("Requesting verification code...")
    try:
        request_data = {"email": email, "method": "email"}
        typer.echo(f"Debug: Request data: {request_data}")
        response = requests.post(
            "https://api.dev.dooers.ai/api/v1/session/request",
            json=request_data,
            timeout=10
        )
        typer.echo(f"Debug: Response status: {response.status_code}")
        typer.echo(f"Debug: Response text: {response.text}")
        
        if response.status_code == 400:
            error_data = response.json()
            error_type = error_data.get("status", {}).get("description", "Unknown error")
            if "AUTH_PROVIDER_ERROR" in error_type:
                typer.echo("❌ Authentication provider error. This might be due to:")
                typer.echo("   - Email already has an active session")
                typer.echo("   - Rate limiting")
                typer.echo("   - Invalid email address")
                typer.echo("   - Try logging out first: dooers logout")
                raise typer.Exit(1)
        
        response.raise_for_status()
        
        session_data = response.json()
        email_id = session_data.get("output", {}).get("email_id")
        
        if not email_id:
            typer.echo("❌ Failed to get email ID from response")
            typer.echo(f"Response structure: {session_data}")
            raise typer.Exit(1)
            
        typer.echo("✅ Verification code sent to your email")
        
        # Step 2: Get OTP code
        if not code:
            code = typer.prompt("Enter the verification code from your email")
        
        # Step 3: Create session with OTP code
        typer.echo("Verifying code...")
        create_response = requests.post(
            "https://api.dev.dooers.ai/api/v1/session/create",
            json={"email_id": email_id, "code": code},
            timeout=10
        )
        create_response.raise_for_status()
        
        session_result = create_response.json()
        typer.echo(f"Debug: Session result: {session_result}")
        
        # Extract token from cookies (the API returns it as 'auth' cookie)
        AUTH_TOKEN = None
        for cookie in create_response.cookies:
            if cookie.name == 'auth':
                AUTH_TOKEN = cookie.value
                break
        
        # Fallback: try to get token from JSON response
        if not AUTH_TOKEN:
            AUTH_TOKEN = session_result.get("output", {}).get("token")
        
        if AUTH_TOKEN:
            _save_token(AUTH_TOKEN)
            typer.echo("✅ Successfully authenticated!")
        else:
            typer.echo("❌ Authentication failed - no token received")
            raise typer.Exit(1)
            
    except requests.RequestException as e:
        typer.echo(f"❌ Authentication failed: {e}")
        raise typer.Exit(1)


@app.command()
def logout():
    """Logout and clear authentication"""
    global AUTH_TOKEN
    
    if not AUTH_TOKEN:
        _load_token()
    
    if AUTH_TOKEN:
        try:
            requests.post(
                "https://api.dev.dooers.ai/api/v1/session/remove",
                headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
                timeout=10
            )
        except requests.RequestException:
            pass  # Ignore errors on logout
    
    _clear_token()
    typer.echo("✅ Logged out successfully")


@app.command()
def whoami():
    """Show current user information"""
    try:
        headers = _get_auth_headers()
        response = requests.get(
            "https://api.dev.dooers.ai/api/v1/session/verify",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        
        user_data = response.json()
        typer.echo(f"✅ Authenticated as: {user_data.get('email', 'Unknown')}")
        
    except Exception as e:
        typer.echo(f"❌ Failed to get user info: {e}")
        raise typer.Exit(1)


def _make_tar_gz_of_cwd() -> str:
    tmpfd, tmppath = tempfile.mkstemp(suffix=".tar.gz", prefix="dooers-")
    os.close(tmpfd)
    with tarfile.open(tmppath, "w:gz") as tar:
        for root, dirs, files in os.walk("."):
            # Skip venvs, git, node_modules, etc.
            relroot = os.path.relpath(root, ".")
            if relroot.startswith(".git") or relroot.startswith(".venv") or "node_modules" in relroot:
                continue
            for name in files:
                if name.endswith((".pyc", ".DS_Store")):
                    continue
                full = os.path.join(root, name)
                arcname = os.path.relpath(full, ".")
                tar.add(full, arcname=arcname)
    return tmppath


@app.command()
def push(
    agent_name: str = typer.Argument(..., help="Agent name"),
    server_url: str = typer.Option("https://api.dooers.ai", help="Agent Deploy service URL"),
    no_build: bool = typer.Option(False, help="Do not trigger build after upload"),
    tag: str = typer.Option("latest", help="Image tag"),
):
    """Archive current directory and upload to server to build image."""
    # Security warning for HTTP URLs
    if server_url.startswith("http://") and "localhost" not in server_url:
        typer.echo("⚠️  WARNING: Using HTTP instead of HTTPS. This is not secure for production!")
        if not typer.confirm("Continue anyway?"):
            raise typer.Exit(1)
    
    archive_path = _make_tar_gz_of_cwd()
    try:
        url = f"{server_url.rstrip('/')}/v1/agents/{agent_name}/push"
        with open(archive_path, "rb") as f:
            size = os.path.getsize(archive_path)
            with tqdm(total=size, unit='B', unit_scale=True, desc='Uploading') as pbar:
                class TqdmFile(io.BufferedReader):
                    def read(self, *args, **kwargs):
                        chunk = super().read(*args, **kwargs)
                        if chunk:
                            pbar.update(len(chunk))
                        return chunk
                tf = TqdmFile(f)
                files = {"archive": (Path(archive_path).name, tf, "application/gzip")}
                params = {"build": str(not no_build).lower(), "image_tag": tag}
                headers = _get_auth_headers()
                resp = requests.post(url, files=files, params=params, headers=headers, timeout=600)
                resp.raise_for_status()
                typer.echo(resp.json())
    finally:
        try:
            os.remove(archive_path)
        except OSError:
            pass


if __name__ == "__main__":
    app()
