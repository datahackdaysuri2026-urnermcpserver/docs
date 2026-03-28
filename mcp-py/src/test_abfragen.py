"""
MCP server test: initialize a session then call the get_events tool.

Usage:
    python test_get_events.py
    python test_get_events.py --url http://localhost:8000/mcp
    python test_get_events.py --keywords musik konzert --place Andermatt --date 2026-04-01
"""

import argparse
import json
import sys
import urllib.error
import urllib.request


MCP_PROTOCOL_VERSION = "2025-03-26"
CLIENT_INFO = {"name": "python-test", "version": "1.0.0"}


def post(url: str, payload: dict, session_id: str | None = None) -> tuple[dict, dict[str, str]]:
    """Send a JSON-RPC POST request and return (response_body, response_headers)."""
    body = json.dumps(payload).encode()
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if session_id:
        headers["mcp-session-id"] = session_id

    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode()
            resp_headers = {k.lower(): v for k, v in resp.headers.items()}
            # Streamable-HTTP may return SSE lines; keep only the last data: line.
            data_lines = [ln[6:] for ln in raw.splitlines() if ln.startswith("data: ")]
            json_text = data_lines[-1] if data_lines else raw
            return json.loads(json_text), resp_headers
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        print(f"HTTP {exc.code} {exc.reason}:\n{raw}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as exc:
        print(f"Connection error: {exc.reason}", file=sys.stderr)
        print("Is the MCP server running?", file=sys.stderr)
        sys.exit(1)


def initialize(url: str) -> str | None:
    """Send initialize and return the session ID (may be None)."""
    print("[1/2] Initialize MCP session")
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": CLIENT_INFO,
        },
    }
    body, headers = post(url, payload)
    print(json.dumps(body, indent=2, ensure_ascii=False))

    session_id = headers.get("mcp-session-id")
    if session_id:
        print(f"Session ID: {session_id}")
    else:
        print("Warning: no mcp-session-id header returned. Continuing without it.")
    return session_id


def call_tool(
    url: str,
    session_id: str | None,
    tool_function: str,
    parameters: dict,
) -> None:
    """Call an MCP tool function and pretty-print the result."""
    print(f"\n[2/2] Call tool: {tool_function}")

    payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": tool_function, "arguments": parameters},
    }
    print(payload)
    body, _ = post(url, payload, session_id=session_id)

    # Extract the tool result content list
    result = body.get("result") or body
    content = result.get("content") if isinstance(result, dict) else None
    if content:
        for item in content:
            if item.get("type") == "text":
                try:
                    parsed = json.loads(item["text"])
                    print(json.dumps(parsed, indent=2, ensure_ascii=False))
                except (json.JSONDecodeError, KeyError):
                    print(item.get("text", ""))
    else:
        print(json.dumps(body, indent=2, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="Test the MCP server get_events tool.")
    parser.add_argument("--url", default="http://localhost:8000/mcp", help="MCP server URL")
    parser.add_argument("--tool-function", default="get_events", help="Tool name to call")
    parser.add_argument(
        "--parameters",
        default=None,
        help="JSON object with tool arguments, e.g. '{\"keywords\":[\"musik\"],\"place\":\"Andermatt\"}'",
    )
    parser.add_argument("--keywords", nargs="+", default=[] , metavar="KEYWORD")
    parser.add_argument("--place", default="Andermatt")
    parser.add_argument("--date", default=None, help="e.g. 2026-04-01 or 'April 2026'")
    args = parser.parse_args()

    if args.parameters:
        try:
            parameters = json.loads(args.parameters)
        except json.JSONDecodeError as exc:
            print(f"Invalid --parameters JSON: {exc}", file=sys.stderr)
            sys.exit(2)
        if not isinstance(parameters, dict):
            print("--parameters must be a JSON object", file=sys.stderr)
            sys.exit(2)
    else:
        parameters = {}
        if args.keywords:
            parameters["keywords"] = args.keywords
        if args.place:
            parameters["place"] = args.place
        if args.date:
            parameters["date"] = args.date

    session_id = initialize(args.url)

    # List all available tools (for debugging)
    print("\nAvailable tools:")
    payload = {
        "jsonrpc": "2.0",
        "id": 999,
        "method": "tools/list",
    }
    body, _ = post(args.url, payload, session_id=session_id)
    tools = body.get("result", {}).get("tools", [])
    for tool in tools:
        print(f"- {tool.get('name')}")
        

    call_tool(args.url, session_id, args.tool_function, parameters)
    print("\nDone.")
    parameters.pop("place", None)  # Remove place to test broader search
    call_tool(args.url, session_id, "get_kinoprogramm", parameters)


if __name__ == "__main__":
    main()
