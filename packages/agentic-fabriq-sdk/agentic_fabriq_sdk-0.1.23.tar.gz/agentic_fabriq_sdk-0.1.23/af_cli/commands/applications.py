"""
CLI commands for managing registered applications.
"""

import json
from pathlib import Path
from typing import Optional

import httpx
import typer
from rich.console import Console
from rich.table import Table

from af_cli.core.config import get_config
from af_cli.core.output import print_output

app = typer.Typer(help="Manage registered applications")
console = Console()


@app.command("create")
def create_application(
    app_id: str = typer.Option(..., "--app-id", help="Application identifier (no spaces)"),
    connections: str = typer.Option(..., "--connections", help="Tool connections (format: 'tool1:conn-id,tool2:conn-id')"),
    scopes: Optional[str] = typer.Option(None, "--scopes", help="Scopes (format: 'scope1,scope2,scope3')"),
):
    """
    Register a new application.
    
    Example:
        afctl applications create \\
            --app-id my-slack-bot \\
            --connections slack:my-slack-conn,github:my-github-conn \\
            --scopes slack:read,slack:write,github:repo:read
    """
    config = get_config()
    
    if not config.is_authenticated():
        console.print("❌ Not authenticated. Run 'afctl auth login' first.", style="red")
        raise typer.Exit(1)
    
    # Parse connections
    tool_connections = {}
    if connections:
        for conn_pair in connections.split(","):
            try:
                tool, conn_id = conn_pair.split(":")
                tool_connections[conn_id] = []  # Will add scopes below
            except ValueError:
                console.print(f"❌ Invalid connection format: '{conn_pair}'. Use 'tool:conn-id'", style="red")
                raise typer.Exit(1)
    
    # Parse scopes and assign to connections
    if scopes:
        scope_list = [s.strip() for s in scopes.split(",")]
        # For simplicity, assign all scopes to all connections
        # In production, you might want per-connection scopes
        for conn_id in tool_connections:
            tool_connections[conn_id] = scope_list
    
    # Make API request
    try:
        response = httpx.post(
            f"{config.gateway_url}/api/v1/applications",
            headers={"Authorization": f"Bearer {config.access_token}"},
            json={
                "app_id": app_id,
                "tool_connections": tool_connections
            },
            timeout=30.0
        )
        
        if response.status_code != 201:
            error_detail = response.text
            try:
                error_json = response.json()
                error_detail = error_json.get("detail", response.text)
            except:
                pass
            
            console.print(f"❌ Failed to register application: {error_detail}", style="red")
            raise typer.Exit(1)
        
        data = response.json()
        
        # Save credentials locally
        from af_sdk import save_application_config
        
        app_config = {
            "app_id": data["app_id"],
            "secret_key": data["secret_key"],
            "user_id": data["user_id"],
            "tenant_id": data["tenant_id"],
            "tool_connections": data["tool_connections"],
            "created_at": data["created_at"],
            "gateway_url": config.gateway_url
        }
        
        app_file = save_application_config(data["app_id"], app_config)
        
        # Display success
        console.print("\n✅ Application registered successfully!", style="green bold")
        console.print(f"\n📋 App ID: {data['app_id']}", style="cyan")
        console.print(f"🔑 Secret Key: {data['secret_key']}", style="yellow")
        console.print(f"\n💾 Credentials saved to: {app_file}", style="green")
        console.print("\n⚠️  Save the secret key securely! It won't be shown again.", style="yellow bold")
        console.print("\n🚀 Your agent can now authenticate with:", style="cyan")
        console.print(f"   from af_sdk import get_application_client", style="white")
        console.print(f"   client = await get_application_client('{data['app_id']}')", style="white")
        
    except httpx.HTTPError as e:
        console.print(f"❌ Network error: {e}", style="red")
        raise typer.Exit(1)


@app.command("list")
def list_applications(
    format: str = typer.Option("table", "--format", help="Output format (table, json, yaml)"),
):
    """
    List all registered applications.
    
    Shows applications from both:
    - Local config files (~/.af/applications/)
    - Server (via API)
    """
    config = get_config()
    
    # Load from local config first
    from af_sdk import list_applications as list_local_apps
    
    local_apps = list_local_apps()
    
    if format == "table":
        if not local_apps:
            console.print("No applications registered locally.", style="yellow")
            return
        
        table = Table(title="Registered Applications")
        table.add_column("App ID", style="cyan")
        table.add_column("Created", style="green")
        table.add_column("Tool Connections", style="magenta")
        table.add_column("Config File", style="white")
        
        for app in local_apps:
            conn_count = len(app.get("tool_connections", {}))
            conn_str = f"{conn_count} connection(s)"
            config_file = f"~/.af/applications/{app['app_id']}.json"
            
            table.add_row(
                app["app_id"],
                app.get("created_at", "N/A")[:10],  # Just date
                conn_str,
                config_file
            )
        
        console.print(table)
        console.print(f"\n📊 Total: {len(local_apps)} application(s)")
    else:
        print_output(
            {"applications": local_apps, "total": len(local_apps)},
            format_type=format,
            title="Registered Applications"
        )


@app.command("show")
def show_application(
    app_id: str = typer.Argument(..., help="Application identifier"),
    reveal_secret: bool = typer.Option(False, "--reveal-secret", help="Reveal the secret key"),
):
    """
    Show details of a registered application.
    
    Example:
        afctl applications show my-slack-bot
        afctl applications show my-slack-bot --reveal-secret
    """
    from af_sdk import load_application_config, ApplicationNotFoundError
    
    try:
        app_config = load_application_config(app_id)
    except ApplicationNotFoundError as e:
        console.print(f"❌ {e}", style="red")
        raise typer.Exit(1)
    
    console.print(f"\n📋 Application: {app_config['app_id']}", style="cyan bold")
    console.print(f"👤 User ID: {app_config.get('user_id', 'N/A')}", style="white")
    console.print(f"🏢 Tenant ID: {app_config.get('tenant_id', 'N/A')}", style="white")
    console.print(f"📅 Created: {app_config.get('created_at', 'N/A')}", style="white")
    console.print(f"🌐 Gateway: {app_config.get('gateway_url', 'N/A')}", style="white")
    
    if reveal_secret:
        console.print(f"\n🔑 Secret Key: {app_config['secret_key']}", style="yellow bold")
        console.print("⚠️  Keep this secret secure!", style="yellow")
    else:
        console.print(f"\n🔑 Secret Key: ••••••••", style="white")
        console.print("   Use --reveal-secret to show", style="dim")
    
    console.print("\n🔌 Tool Connections:", style="cyan bold")
    tool_conns = app_config.get("tool_connections", {})
    if tool_conns:
        for conn_id, scopes in tool_conns.items():
            console.print(f"  • {conn_id}", style="white")
            if scopes:
                console.print(f"    Scopes: {', '.join(scopes)}", style="dim")
    else:
        console.print("  (none)", style="dim")
    
    config_file = Path.home() / ".af" / "applications" / f"{app_id}.json"
    console.print(f"\n💾 Config file: {config_file}", style="green")


@app.command("delete")
def delete_application(
    app_id: str = typer.Argument(..., help="Application identifier"),
    yes: bool = typer.Option(False, "--yes", help="Skip confirmation"),
):
    """
    Delete a registered application.
    
    This will:
    - Delete the application registration on the server
    - Remove local credentials
    - Invalidate all active tokens
    
    Example:
        afctl applications delete my-slack-bot
        afctl applications delete my-slack-bot --yes
    """
    config = get_config()
    
    if not config.is_authenticated():
        console.print("❌ Not authenticated. Run 'afctl auth login' first.", style="red")
        raise typer.Exit(1)
    
    # Confirm deletion
    if not yes:
        console.print(f"\n⚠️  This will:", style="yellow bold")
        console.print(f"  • Delete the application registration on the server", style="white")
        console.print(f"  • Remove local credentials from ~/.af/applications/{app_id}.json", style="white")
        console.print(f"  • Invalidate all active tokens for this application", style="white")
        
        confirm = typer.confirm(f"\nAre you sure you want to delete '{app_id}'?", default=False)
        if not confirm:
            console.print("❌ Cancelled", style="yellow")
            raise typer.Exit(0)
    
    # Delete from server
    try:
        response = httpx.delete(
            f"{config.gateway_url}/api/v1/applications/{app_id}",
            headers={"Authorization": f"Bearer {config.access_token}"},
            timeout=30.0
        )
        
        if response.status_code == 404:
            console.print(f"⚠️  Application '{app_id}' not found on server", style="yellow")
        elif response.status_code != 204:
            error_detail = response.text
            try:
                error_json = response.json()
                error_detail = error_json.get("detail", response.text)
            except:
                pass
            
            console.print(f"❌ Failed to delete from server: {error_detail}", style="red")
            raise typer.Exit(1)
        else:
            console.print(f"✅ Deleted from server", style="green")
        
    except httpx.HTTPError as e:
        console.print(f"❌ Network error: {e}", style="red")
        raise typer.Exit(1)
    
    # Delete local config
    from af_sdk import delete_application_config
    
    deleted = delete_application_config(app_id)
    if deleted:
        console.print(f"✅ Deleted local credentials", style="green")
    else:
        console.print(f"⚠️  Local credentials not found", style="yellow")
    
    console.print(f"\n🎉 Application '{app_id}' deleted successfully", style="green bold")


@app.command("test")
def test_application(
    app_id: str = typer.Argument(..., help="Application identifier"),
):
    """
    Test application authentication.
    
    Attempts to exchange credentials for a token to verify the application
    is properly registered and can authenticate.
    
    Example:
        afctl applications test my-slack-bot
    """
    import asyncio
    from af_sdk import get_application_client, ApplicationNotFoundError, AuthenticationError
    
    async def _test():
        try:
            console.print(f"🔄 Testing authentication for '{app_id}'...", style="cyan")
            
            client = await get_application_client(app_id)
            
            console.print(f"✅ Authentication successful!", style="green bold")
            console.print(f"\n📋 Application: {client._app_id}", style="cyan")
            console.print(f"⏱️  Token expires in: {client._expires_in} seconds", style="white")
            console.print(f"\n🎉 Your application can authenticate and make API calls!", style="green")
            
        except ApplicationNotFoundError as e:
            console.print(f"❌ {e}", style="red")
            raise typer.Exit(1)
        except AuthenticationError as e:
            console.print(f"❌ {e}", style="red")
            raise typer.Exit(1)
    
    asyncio.run(_test())

