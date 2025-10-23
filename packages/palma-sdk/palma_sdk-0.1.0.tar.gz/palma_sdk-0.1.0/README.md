# Palma AI SDK

A Python client for interacting with MCP (Model Context Protocol) servers.

## Installation

```bash
pip install palma-sdk
```

## Usage

```python
import asyncio
from palma_sdk import PalmaClient

async def main():
    client = PalmaClient(server_url="ws://localhost:3000")
    
    await client.connect()
    
    # List available tools
    tools = await client.list_tools()
    print(f"Available tools: {[tool.name for tool in tools]}")
    
    # Call a tool
    result = await client.call_tool("example-tool", {"input": "data"})
    print(f"Tool result: {result}")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

## Features

- Async/await support
- Type hints throughout
- Event-driven architecture
- Tool calling
- Resource management
- Error handling

## License

MIT
