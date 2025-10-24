"""
FabriqClient: High-level async helper for Agentic Fabric Gateway.

This client wraps common Gateway API flows so agent developers can:
- List and invoke tools
- Register and invoke MCP servers (via proxy)
- Invoke agents (via proxy)
- Manage per-user secrets via the Gateway-backed Vault API

Usage:
    from af_sdk.fabriq_client import FabriqClient

    async with FabriqClient(base_url="http://localhost:8000", auth_token=JWT) as af:
        tools = await af.list_tools()
        result = await af.invoke_tool(tool_id, method="list_items", parameters={"limit": 10})
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .transport.http import HTTPClient


class FabriqClient:
    """Async helper around the Gateway REST API.

    Args:
        base_url: Gateway base URL (e.g., "http://localhost:8000").
        auth_token: Bearer JWT with required scopes.
        api_prefix: API root prefix. Defaults to "/api/v1".
        timeout: Request timeout in seconds.
        retries: Number of retry attempts for transient errors.
        backoff_factor: Exponential backoff base delay in seconds.
        trace_enabled: Enable OpenTelemetry HTTPX instrumentation.
    """

    def __init__(
        self,
        *,
        base_url: str,
        auth_token: Optional[str] = None,
        api_prefix: str = "/api/v1",
        timeout: float = 30.0,
        retries: int = 3,
        backoff_factor: float = 0.5,
        trace_enabled: bool = True,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self._root = base_url.rstrip("/")
        self._api = api_prefix if api_prefix.startswith("/") else f"/{api_prefix}"
        self._extra_headers = extra_headers or {}
        self._http = HTTPClient(
            base_url=f"{self._root}{self._api}",
            timeout=timeout,
            retries=retries,
            backoff_factor=backoff_factor,
            auth_token=auth_token,
            trace_enabled=trace_enabled,
        )

    async def __aenter__(self) -> "FabriqClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def close(self) -> None:
        await self._http.close()

    # -----------------
    # Tools
    # -----------------
    async def list_tools(self, *, page: int = 1, page_size: int = 20, search: Optional[str] = None) -> Dict[str, Any]:
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        if search:
            params["search"] = search
        r = await self._http.get("/tools", params=params, headers=self._extra_headers)
        return r.json()

    async def invoke_tool(
        self,
        tool_identifier: str,
        *,
        method: str,
        parameters: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        connection_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Invoke a tool by name or UUID.
        
        Args:
            tool_identifier: Tool name (e.g., 'slack') or UUID
            method: Method name to invoke
            parameters: Method parameters
            context: Additional context
            connection_id: Specific connection ID to use (for multi-connection tools)
            
        Returns:
            Tool invocation result
            
        Examples:
            result = await client.invoke_tool("slack", method="get_channels")
            result = await client.invoke_tool("slack", method="post_message", 
                                             parameters={"channel": "test", "text": "Hello!"})
            result = await client.invoke_tool("slack", method="get_channels",
                                             connection_id="slacker")
        """
        # Try to resolve tool name to UUID if not already a UUID
        tool_id = tool_identifier
        try:
            from uuid import UUID
            UUID(tool_identifier)
            # It's already a UUID, use it directly
        except ValueError:
            # Not a UUID, try to look up by name
            try:
                tools_response = await self.list_tools()
            except Exception as e:
                raise ValueError(f"Failed to list tools for name resolution: {e}. Please use UUID directly.")
            
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
                available = [t.get('name') for t in tools if isinstance(t, dict) and t.get('name')]
                raise ValueError(f"Tool '{tool_identifier}' not found. Available tools: {available}")
            
            if len(matching_tools) > 1:
                raise ValueError(f"Multiple tools found with name '{tool_identifier}'. Please use UUID instead.")
            
            tool_id = matching_tools[0].get("id")
            if not tool_id:
                raise ValueError(f"Tool '{tool_identifier}' found but has no ID")
        
        body = {"method": method}
        if parameters is not None:
            body["parameters"] = parameters
        
        # Add connection_id to context if provided
        if context is not None or connection_id is not None:
            ctx = (context or {}).copy()
            if connection_id is not None:
                ctx["connection_id"] = connection_id
            body["context"] = ctx
        
        r = await self._http.post(f"/tools/{tool_id}/invoke", json=body, headers=self._extra_headers)
        return r.json()
    
    async def invoke_connection(
        self,
        connection_id: str,
        *,
        method: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Invoke a tool using its connection ID (preferred method).
        
        This directly uses the connection_id (like 'slacker', 'gurt') to invoke
        the tool without needing to look up UUIDs. This is the most efficient
        and reliable way to invoke tools.
        
        Args:
            connection_id: Connection identifier (e.g., 'slacker', 'gurt')
            method: Method name to invoke
            parameters: Method parameters
            
        Returns:
            Tool invocation result
            
        Examples:
            result = await client.invoke_connection("slacker", method="get_channels")
            result = await client.invoke_connection("slacker", method="post_message",
                                                   parameters={"channel": "test", "text": "Hello!"})
            result = await client.invoke_connection("gurt", method="list_files")
        """
        # Use the direct connection-based invoke endpoint
        # This matches what the CLI uses and is more efficient
        body = {
            "method": method,
            "parameters": parameters or {},
        }
        
        # Call the connection-based invoke endpoint
        r = await self._http.post(
            f"/tools/connections/{connection_id}/invoke",
            json=body,
            headers=self._extra_headers
        )
        return r.json()

    # -----------------
    # MCP Servers
    # -----------------
    async def register_mcp_server(
        self,
        *,
        name: str,
        base_url: str,
        description: Optional[str] = None,
        auth_type: str = "API_KEY",
        source: str = "STATIC",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "name": name,
            "base_url": base_url,
            "auth_type": auth_type,
            "source": source,
        }
        if description is not None:
            body["description"] = description
        if metadata is not None:
            body["metadata"] = metadata
        r = await self._http.post("/mcp/servers", json=body, headers=self._extra_headers)
        return r.json()

    async def list_mcp_servers(self, *, page: int = 1, page_size: int = 20, search: Optional[str] = None) -> Dict[str, Any]:
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        if search:
            params["search"] = search
        r = await self._http.get("/mcp/servers", params=params, headers=self._extra_headers)
        return r.json()

    async def invoke_mcp(self, *, server_id: str, payload: Dict[str, Any], raw: bool = False) -> Dict[str, Any]:
        r = await self._http.post(f"/proxy/mcp/{server_id}/invoke", json={"payload": payload, "raw": raw}, headers=self._extra_headers)
        return r.json()

    # -----------------
    # Secrets (Gateway-backed Vault)
    # -----------------
    async def get_secret(self, *, path: str, version: Optional[int] = None) -> Dict[str, Any]:
        params = {"version": version} if version is not None else None
        r = await self._http.get(f"/secrets/{path}", params=params, headers=self._extra_headers)
        return r.json()

    async def create_secret(
        self,
        *,
        path: str,
        value: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None,
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {"value": value}
        if description is not None:
            body["description"] = description
        if metadata is not None:
            body["metadata"] = metadata
        if ttl is not None:
            body["ttl"] = ttl
        r = await self._http.post(f"/secrets/{path}", json=body, headers=self._extra_headers)
        return r.json()

    async def update_secret(
        self,
        *,
        path: str,
        value: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None,
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {}
        if value is not None:
            body["value"] = value
        if description is not None:
            body["description"] = description
        if metadata is not None:
            body["metadata"] = metadata
        if ttl is not None:
            body["ttl"] = ttl
        r = await self._http.put(f"/secrets/{path}", json=body, headers=self._extra_headers)
        return r.json()

    async def delete_secret(self, *, path: str) -> Dict[str, Any]:
        r = await self._http.delete(f"/secrets/{path}", headers=self._extra_headers)
        return r.json() if r.content else {"status": "deleted"}


