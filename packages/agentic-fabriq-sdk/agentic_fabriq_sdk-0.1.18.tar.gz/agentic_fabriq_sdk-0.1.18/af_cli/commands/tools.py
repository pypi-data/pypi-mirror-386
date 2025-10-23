"""
Tool management commands for the Agentic Fabric CLI.
"""


import typer

from af_cli.core.client import get_client
from af_cli.core.output import debug, error, info, print_output, success, warning

app = typer.Typer(help="Tool management commands")


@app.command()
def list(
    format: str = typer.Option("table", "--format", help="Output format"),
):
    """List your tool connections (configured and connected tools)."""
    try:
        with get_client() as client:
            connections = client.get("/api/v1/user-connections")
            
            if not connections:
                warning("No tool connections found. Add connections in the dashboard UI.")
                return
            
            # Format for better display
            display_data = []
            for conn in connections:
                # Format tool name nicely (e.g., "google_docs" -> "Google Docs")
                tool_name = conn.get("tool", "N/A").replace("_", " ").title()
                
                # Status indicator
                status = "✓ Connected" if conn.get("connected") else "○ Configured"
                
                display_data.append({
                    "Tool": tool_name,
                    "ID": conn.get("connection_id", "N/A"),
                    "Name": conn.get("display_name") or conn.get("connection_id", "N/A"),
                    "Status": status,
                    "Method": conn.get("method", "oauth"),
                    "Added": conn.get("created_at", "N/A")[:10] if conn.get("created_at") else "N/A",
                })
            
            print_output(
                display_data,
                format_type=format,
                title="Your Tool Connections"
            )
            
    except Exception as e:
        error(f"Failed to list tool connections: {e}")
        raise typer.Exit(1)


@app.command()
def get(
    connection_id: str = typer.Argument(..., help="Connection ID (e.g., 'google', 'slack')"),
    format: str = typer.Option("table", "--format", help="Output format"),
):
    """Get tool connection details."""
    try:
        with get_client() as client:
            # Get all user connections and find the matching one
            connections = client.get("/api/v1/user-connections")
            
            # Find the specific connection
            connection = None
            for conn in connections:
                if conn.get("connection_id") == connection_id or conn.get("tool") == connection_id:
                    connection = conn
                    break
            
            if not connection:
                error(f"Connection '{connection_id}' not found")
                info("Available connections:")
                for conn in connections:
                    info(f"  - {conn.get('tool')} (ID: {conn.get('connection_id')})")
                raise typer.Exit(1)
            
            # Format tool name nicely
            tool_name = connection.get("tool", "N/A").replace("_", " ").title()
            
            # Format the connection details for display
            details = {
                "Tool": tool_name,
                "Connection ID": connection.get("connection_id", "N/A"),
                "Display Name": connection.get("display_name") or connection.get("connection_id", "N/A"),
                "Status": "✓ Connected" if connection.get("connected") else "○ Configured",
                "Method": connection.get("method", "oauth"),
                "Created": connection.get("created_at", "N/A"),
                "Updated": connection.get("updated_at", "N/A"),
            }
            
            # Add tool-specific fields if present
            if connection.get("team_name"):
                details["Team Name"] = connection.get("team_name")
            if connection.get("team_id"):
                details["Team ID"] = connection.get("team_id")
            if connection.get("bot_user_id"):
                details["Bot User ID"] = connection.get("bot_user_id")
            if connection.get("email"):
                details["Email"] = connection.get("email")
            if connection.get("login"):
                details["GitHub Login"] = connection.get("login")
            if connection.get("workspace_name"):
                details["Workspace Name"] = connection.get("workspace_name")
            if connection.get("scopes"):
                details["Scopes"] = ", ".join(connection.get("scopes", []))
            
            print_output(
                details,
                format_type=format,
                title=f"{tool_name} Connection Details"
            )
            
    except Exception as e:
        error(f"Failed to get tool connection: {e}")
        raise typer.Exit(1)


@app.command()
def invoke(
    tool_identifier: str = typer.Argument(..., help="Tool name (e.g., 'slack') or UUID"),
    method: str = typer.Option(..., "--method", help="Tool method to invoke"),
    params: str = typer.Option(None, "--params", help="JSON string of method parameters (e.g., '{\"channel\": \"test\", \"text\": \"Hello\"}')"),
    format: str = typer.Option("json", "--format", help="Output format (json, table, yaml)"),
):
    """Invoke a tool by name or UUID.
    
    Examples:
        afctl tools invoke slack --method get_channels
        afctl tools invoke slack --method post_message --params '{"channel": "test", "text": "Hello!"}'
        afctl tools invoke c17b55af-18f8-49be-b9e9-44b1d1be429e --method get_channels
    """
    try:
        # Parse parameters if provided
        parameters = {}
        if params:
            import json as json_lib
            try:
                parameters = json_lib.loads(params)
            except json_lib.JSONDecodeError as e:
                error(f"Invalid JSON in --params: {e}")
                raise typer.Exit(1)
        
        with get_client() as client:
            # Try to resolve tool name to UUID if not already a UUID
            tool_id = tool_identifier
            try:
                from uuid import UUID
                UUID(tool_identifier)
                # It's already a UUID, use it directly
            except ValueError:
                # Not a UUID, try to look up by name
                info(f"Looking up tool '{tool_identifier}'...")
                try:
                    tools_response = client.get("/api/v1/tools")
                    
                    # Handle different response formats
                    if isinstance(tools_response, dict) and "tools" in tools_response:
                        tools = tools_response["tools"]
                    elif isinstance(tools_response, dict) and "items" in tools_response:
                        tools = tools_response["items"]
                    elif hasattr(tools_response, '__iter__') and not isinstance(tools_response, (str, dict)):
                        tools = list(tools_response)
                    else:
                        tools = []
                    
                    # Find tool by name (case-insensitive)
                    matching_tools = [t for t in tools if isinstance(t, dict) and t.get("name", "").lower() == tool_identifier.lower()]
                    
                    if not matching_tools:
                        error(f"Tool '{tool_identifier}' not found. Available tools:")
                        for t in tools:
                            if isinstance(t, dict):
                                print(f"  - {t.get('name')} (ID: {t.get('id')})")
                        raise typer.Exit(1)
                    
                    if len(matching_tools) > 1:
                        error(f"Multiple tools found with name '{tool_identifier}':")
                        for t in matching_tools:
                            print(f"  - {t.get('name')} (ID: {t.get('id')})")
                        error("Please use the UUID instead.")
                        raise typer.Exit(1)
                    
                    tool_id = matching_tools[0].get("id")
                    info(f"Resolved '{tool_identifier}' to tool ID: {tool_id}")
                except Exception as lookup_error:
                    error(f"Failed to look up tool: {lookup_error}")
                    raise typer.Exit(1)
            
            data = {
                "method": method,
                "parameters": parameters,
                "context": {},
            }
            
            info(f"Invoking tool {tool_identifier} method {method}...")
            response = client.post(f"/api/v1/tools/{tool_id}/invoke", data)
            
            success("Tool invoked successfully")
            
            # For tool invocations, show the result in a more readable format
            if format == "json":
                import json as json_lib
                print(json_lib.dumps(response, indent=2))
            elif format == "yaml":
                import yaml
                print(yaml.dump(response, default_flow_style=False))
            else:
                # For table format, show just the result field nicely
                result = response.get("result", {})
                print("\n📊 Result:")
                print_output(result, format_type="json")
            
    except Exception as e:
        error(f"Failed to invoke tool: {e}")
        raise typer.Exit(1)


@app.command()
def add(
    tool: str = typer.Argument(..., help="Tool name (google_drive, google_slides, slack, notion, github, etc.)"),
    connection_id: str = typer.Option(..., "--connection-id", help="Unique connection ID"),
    display_name: str = typer.Option(None, "--display-name", help="Human-readable name"),
    method: str = typer.Option(..., "--method", help="Connection method: 'api_credentials' or 'oauth'"),
    
    # API credentials method fields (can be either a token OR client_id/secret)
    token: str = typer.Option(None, "--token", help="API token (for simple token-based auth like Notion, Slack bot)"),
    client_id: str = typer.Option(None, "--client-id", help="OAuth client ID (for app-based auth like Google, Slack)"),
    client_secret: str = typer.Option(None, "--client-secret", help="OAuth client secret (for app-based auth)"),
    redirect_uri: str = typer.Option(None, "--redirect-uri", help="OAuth redirect URI (optional, auto-generated)"),
):
    """
    Add a new tool connection with credentials.
    
    Examples:
      # Notion (api_credentials method - single token)
      afctl tools add notion --connection-id notion-work --method api_credentials --token "secret_abc123"
      
      # Google (api_credentials method - OAuth app)
      afctl tools add google_drive --connection-id google-work --method api_credentials \\
        --client-id "123.apps.googleusercontent.com" \\
        --client-secret "GOCSPX-abc123"
      
      # Slack bot (api_credentials method - single token)
      afctl tools add slack --connection-id slack-bot --method api_credentials --token "xoxb-123..."
    """
    try:
        from af_cli.core.config import get_config
        
        with get_client() as client:
            # Validate tool name - check for common mistakes
            if tool.lower() == "google":
                error("❌ Invalid tool name: 'google'")
                info("")
                info("Please specify the exact Google Workspace tool:")
                info("  • google_drive    - Google Drive")
                info("  • google_docs     - Google Docs")
                info("  • google_sheets   - Google Sheets")
                info("  • google_slides   - Google Slides")
                info("  • gmail           - Gmail")
                info("  • google_calendar - Google Calendar")
                info("  • google_meet     - Google Meet")
                info("  • google_forms    - Google Forms")
                info("  • google_classroom - Google Classroom")
                info("  • google_people   - Google People (Contacts)")
                info("  • google_chat     - Google Chat")
                info("  • google_tasks    - Google Tasks")
                info("")
                info("Example:")
                info(f"  afctl tools add google_drive --connection-id {connection_id} --method {method}")
                raise typer.Exit(1)
            
            # Validate method
            if method not in ["api_credentials", "oauth"]:
                error("Method must be 'api_credentials' or 'oauth'")
                raise typer.Exit(1)
            
            # Validate api_credentials method requirements
            if method == "api_credentials":
                # Must have either token OR (client_id + client_secret)
                has_token = bool(token)
                has_oauth_creds = bool(client_id and client_secret)
                
                if not has_token and not has_oauth_creds:
                    error("api_credentials method requires either:")
                    info("  • --token (for simple token auth like Notion, Slack bot)")
                    info("  • --client-id and --client-secret (for OAuth app auth like Google)")
                    info("")
                    info(f"Examples:")
                    info(f"  afctl tools add {tool} --connection-id {connection_id} --method api_credentials --token YOUR_TOKEN")
                    info(f"  afctl tools add {tool} --connection-id {connection_id} --method api_credentials --client-id ID --client-secret SECRET")
                    raise typer.Exit(1)
            
            info(f"Creating connection: {connection_id}")
            info(f"Tool: {tool}")
            info(f"Method: {method}")
            
            # Step 1: Create connection metadata
            connection_data = {
                "tool": tool,
                "connection_id": connection_id,
                "display_name": display_name or connection_id,
                "method": method,
            }
            
            client.post("/api/v1/user-connections", data=connection_data)
            success(f"✅ Connection entry created: {connection_id}")
            
            # Step 2: Store credentials based on what was provided
            if method == "api_credentials":
                # Determine the API base tool name (Google tools all use "google")
                api_tool_name = "google" if (tool.startswith("google_") or tool == "gmail") else tool
                
                if token:
                    # Simple token-based auth (Notion, Slack bot, etc.)
                    info("Storing API token...")
                    
                    # Tool-specific endpoint and payload mappings
                    if tool == "notion":
                        # Notion uses /config endpoint with integration_token field
                        endpoint = f"/api/v1/tools/{tool}/config?connection_id={connection_id}"
                        cred_payload = {"integration_token": token}
                    else:
                        # Generic tools use /connection endpoint with api_token field
                        endpoint = f"/api/v1/tools/{tool}/connection?connection_id={connection_id}"
                        cred_payload = {"api_token": token}
                    
                    client.post(endpoint, data=cred_payload)
                    success("✅ API token stored")
                    success(f"✅ Connection '{connection_id}' is ready to use!")
                    
                elif client_id and client_secret:
                    # OAuth app credentials (Google, Slack app, etc.)
                    # Auto-generate redirect_uri if not provided
                    if not redirect_uri:
                        config = get_config()
                        redirect_uri = f"{config.gateway_url}/api/v1/tools/{api_tool_name}/oauth/callback"
                        info(f"Using default redirect URI: {redirect_uri}")
                    
                    # Store OAuth app config
                    info("Storing OAuth app credentials...")
                    config_payload = {
                        "client_id": client_id,
                        "client_secret": client_secret,
                    }
                    if redirect_uri:
                        config_payload["redirect_uri"] = redirect_uri
                    
                    client.post(
                        f"/api/v1/tools/{api_tool_name}/config?connection_id={connection_id}",
                        data=config_payload
                    )
                    success("✅ OAuth app credentials stored")
                    info("")
                    info(f"Next: Run 'afctl tools connect {connection_id}' to complete OAuth setup")
            
            elif method == "oauth":
                # OAuth flow (legacy, redirect to api_credentials)
                error("The 'oauth' method is deprecated. Please use 'api_credentials' instead.")
                info("All credential storage now uses the 'api_credentials' method.")
                raise typer.Exit(1)
            
            # Show helpful info
            info("")
            info("View your connections:")
            info(f"  • List all: afctl tools list")
            info(f"  • View details: afctl tools get {connection_id}")
            
    except Exception as e:
        error(f"Failed to add connection: {e}")
        raise typer.Exit(1)


@app.command()
def connect(
    connection_id: str = typer.Argument(..., help="Connection ID to connect"),
):
    """Complete OAuth connection (open browser for authorization)."""
    try:
        import webbrowser
        import time
        
        with get_client() as client:
            # Get connection info
            connections = client.get("/api/v1/user-connections")
            
            connection = None
            for conn in connections:
                if conn.get("connection_id") == connection_id:
                    connection = conn
                    break
            
            if not connection:
                error(f"Connection '{connection_id}' not found")
                info("Run 'afctl tools list' to see available connections")
                raise typer.Exit(1)
            
            tool = connection["tool"]
            method = connection["method"]
            
            # Check if connection is already set up (has credentials stored)
            if connection.get("connected"):
                warning(f"Connection '{connection_id}' is already connected")
                confirm = typer.confirm("Do you want to reconnect (re-authorize)?")
                if not confirm:
                    return
            
            # Determine the API base tool name (Google tools all use "google")
            api_tool_name = "google" if (tool.startswith("google_") or tool == "gmail") else tool
            
            # Initiate OAuth flow
            info(f"Initiating OAuth for {tool}...")
            
            # For Google tools, pass the specific tool_type parameter
            tool_type_param = f"&tool_type={tool}" if tool != api_tool_name else ""
            
            result = client.post(
                f"/api/v1/tools/{api_tool_name}/connect/initiate?connection_id={connection_id}{tool_type_param}",
                data={}
            )
            
            debug(f"Backend response: {result}")
            
            # Different tools use different field names for the auth URL
            auth_url = (
                result.get("authorization_url") or 
                result.get("auth_url") or 
                result.get("oauth_url")
            )
            
            if not auth_url:
                error("Failed to get authorization URL from backend")
                error(f"Response keys: {list(result.keys())}")
                debug(f"Full response: {result}")
                raise typer.Exit(1)
            
            info("Opening browser for authentication...")
            info("")
            info(f"If browser doesn't open, visit: {auth_url}")
            
            # Open browser
            webbrowser.open(auth_url)
            
            info("")
            info("Waiting for authorization...")
            info("(Complete the login in your browser)")
            
            # Poll for connection completion
            max_attempts = 120  # 2 minutes
            for attempt in range(max_attempts):
                time.sleep(1)
                
                # Check connection status
                connections = client.get("/api/v1/user-connections")
                for conn in connections:
                    if conn.get("connection_id") == connection_id:
                        if conn.get("connected"):
                            info("")
                            success(f"✅ Successfully connected to {tool}!")
                            
                            # Show connection details
                            info(f"Connection ID: {connection_id}")
                            if conn.get("email"):
                                info(f"Email: {conn['email']}")
                            if conn.get("team_name"):
                                info(f"Team: {conn['team_name']}")
                            if conn.get("login"):
                                info(f"GitHub: {conn['login']}")
                            
                            return
                        break
            
            # Timeout
            error("")
            error("Timeout: Authorization not completed within 2 minutes")
            info("Please try again or check your browser")
            raise typer.Exit(1)
            
    except Exception as e:
        error(f"Failed to connect: {e}")
        raise typer.Exit(1)


@app.command()
def disconnect(
    connection_id: str = typer.Argument(..., help="Connection ID to disconnect"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation"),
):
    """Disconnect a tool (remove credentials but keep connection entry)."""
    try:
        with get_client() as client:
            # Get connection info
            connections = client.get("/api/v1/user-connections")
            
            connection = None
            for conn in connections:
                if conn.get("connection_id") == connection_id:
                    connection = conn
                    break
            
            if not connection:
                error(f"Connection '{connection_id}' not found")
                raise typer.Exit(1)
            
            tool = connection["tool"]
            tool_display = connection.get("display_name") or connection_id
            
            # Check if connected
            if not connection.get("connected"):
                error(f"Connection '{connection_id}' is already disconnected")
                info(f"Use 'afctl tools get {connection_id}' to view status")
                raise typer.Exit(1)
            
            # Confirm
            if not force:
                warning(f"This will remove OAuth tokens/credentials for '{tool_display}'")
                info("You can reconnect later with 'afctl tools connect'")
                confirm = typer.confirm(f"Disconnect {tool} connection '{connection_id}'?")
                if not confirm:
                    info("Cancelled")
                    return
            
            # Delete connection credentials
            client.delete(
                f"/api/v1/tools/{tool}/connection?connection_id={connection_id}"
            )
            
            success(f"✅ Disconnected: {connection_id}")
            info("Connection entry preserved.")
            info(f"Run 'afctl tools connect {connection_id}' to reconnect.")
            
    except Exception as e:
        error(f"Failed to disconnect: {e}")
        raise typer.Exit(1)


@app.command()
def remove(
    connection_id: str = typer.Argument(..., help="Connection ID to remove"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation"),
):
    """Remove a tool connection completely (delete entry and credentials)."""
    try:
        with get_client() as client:
            # Get connection info
            connections = client.get("/api/v1/user-connections")
            
            connection = None
            for conn in connections:
                if conn.get("connection_id") == connection_id:
                    connection = conn
                    break
            
            if not connection:
                error(f"Connection '{connection_id}' not found")
                raise typer.Exit(1)
            
            tool = connection["tool"]
            tool_display = connection.get("display_name") or connection_id
            
            # Confirm
            if not force:
                warning("⚠️  This will permanently delete the connection and credentials")
                confirm = typer.confirm(f"Remove {tool} connection '{tool_display}'?")
                if not confirm:
                    info("Cancelled")
                    return
            
            # Delete connection entry (backend will cascade delete credentials)
            client.delete(f"/api/v1/user-connections/{connection_id}")
            
            success(f"✅ Removed: {connection_id}")
            
    except Exception as e:
        error(f"Failed to remove: {e}")
        raise typer.Exit(1) 