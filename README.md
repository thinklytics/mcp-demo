# MCP with RAG Demo

This demonstration project shows how to implement a Model Context Protocol (MCP) server with Retrieval-Augmented Generation (RAG) capabilities. The demo allows AI models to interact with a knowledge base, search for information, and add new documents.

## Features

- MCP server with tool and resource support
- Vector-based RAG implementation using ChromaDB
- Client example for interacting with the MCP server
- Persistent knowledge base storage
- Simple prompt templates

## Prerequisites

- Python 3.8+
- pip (Python package manager)

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd demo
```

2. Create a virtual environment:

```bash
python -m venv mcp-env
source mcp-env/bin/activate
```

3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

4. Verify the installation:

```bash
python test_installation.py
```

This will check that all required dependencies are correctly installed.

## Project Structure

```
demo/
├── server.py           # Main MCP server implementation
├── client_example.py   # Example client to interact with the server
├── requirements.txt    # Project dependencies
├── sample_data.txt     # Sample data available as a resource
├── test_installation.py # Script to verify dependencies
├── tools/
│   ├── __init__.py     # Package initialization
│   └── rag_tools.py    # RAG tools implementation
└── README.md           # This readme file
```

## Running the Demo

### Step 1: Start the MCP Server

First, you need to start the MCP server. You have two options:

#### Option A: Direct Python Execution (for development)

```bash
python server.py
```

This will start the server directly using the FastMCP built-in server.

#### Option B: Using Uvicorn (for better performance)

```bash
uvicorn server:mcp.sse_app --host 0.0.0.0 --port 8000
```

This will start an ASGI server using Uvicorn for better performance and stability.

You should see output indicating that the server has started successfully, including:
- Confirmation that the MCP server instance was created
- Registration of basic tools and prompts
- Creation or loading of the ChromaDB collection
- A final message indicating the server is running

### Step 2: Run the Client Example

After the server is up and running, open a new terminal window (keeping the server running in the first one):

```bash
# Make sure your virtual environment is activated
source mcp-env/bin/activate

# Run the client
python client_example.py
```

The client will:
1. Connect to the server at http://localhost:8000/sse
2. List available tools, resources, and prompts
3. Execute various operations including:
   - Retrieving prompt templates
   - Adding documents to the knowledge base
   - Searching for information using the RAG system
   - Accessing resources

#### Specifying a Custom Server URL

If your server is running on a different host or port, you can specify the URL:

```bash
python client_example.py --server http://custom-host:port
```

The client will automatically append "/sse" to the URL if it's not already present.

## Available MCP Tools

The following tools are available in this demo:

- `echo`: A simple tool that echoes back the provided message
- `add`: A tool that adds two numbers together
- `add_document`: Adds a document to the knowledge base
- `rag_search`: Searches the knowledge base for information related to a query
- `list_documents`: Lists all documents in the knowledge base

## Available MCP Resources

- `sample://data`: Provides access to the sample data in sample_data.txt
- `documents://all`: Provides access to all documents in the knowledge base

## Available MCP Prompts

- `greeting`: A simple greeting prompt template

## Customizing the Demo

### Adding New Tools

To add new tools, modify the `server.py` file:

```python
@mcp.tool()
def your_tool_name(param1: type, param2: type) -> return_type:
    """Tool description"""
    # Tool implementation
    return result
```

### Adding New Resources

To add new resources, modify the `server.py` file:

```python
@mcp.resource("resource://pattern")
def your_resource_function() -> str:
    """Resource description"""
    # Resource implementation
    return "Resource content"
```

### Adding New Prompts

To add new prompt templates, modify the `server.py` file:

```python
@mcp.prompt()
def your_prompt_name(param1: str, param2: str) -> str:
    """Prompt description"""
    return f"""
    Your prompt template text with {param1} and {param2} parameters.
    """
```

## Integrating with AI Models

This MCP server can be integrated with AI models through the MCP protocol. The client example demonstrates how to establish the connection and interact with the server programmatically.

## Troubleshooting

### Client Connection Issues

If you get a "Connection refused" error when running the client:

1. Make sure the server is actually running in another terminal window
2. Check that you're using the correct URL (default is http://localhost:8000)
3. Ensure the server is listening on the expected interface (0.0.0.0 to accept external connections)
4. Try specifying the server URL explicitly: `python client_example.py --server http://localhost:8000`

### Server Endpoint Issues

The MCP server exposes an SSE (Server-Sent Events) endpoint at `/sse`. When connecting with the client:

- The full URL should be `http://localhost:8000/sse`
- The client will automatically append `/sse` if it's missing from your specified URL

### ChromaDB Issues

- ChromaDB will create a `chroma_db` directory to store embeddings and document data
- You can delete this directory to start with a fresh database: `rm -rf ./chroma_db`
- Check the server logs for any ChromaDB-related errors

### Common Issues

**ChromaDB collection already exists error**

If you see an error like this when starting the server:

```
chromadb.errors.InternalError: Collection [documents] already exists
```

It means that ChromaDB is trying to create a collection that already exists. In our latest version, this should be handled automatically. If you still encounter this error, you can:

1. Delete the ChromaDB database and start fresh:
   ```bash
   rm -rf ./chroma_db
   ```

2. Or modify the `tools/rag_tools.py` file to properly handle both `ValueError` and `InternalError` exceptions when creating the collection.

**Import errors with client connection**

If you see import errors when running the client example, make sure to use the correct imports for the SSE client:

```python
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

# Then connect like this:
async with sse_client("http://localhost:8000/sse") as streams:
    async with ClientSession(streams[0], streams[1]) as session:
        await session.initialize()
        # Your code here
```

Note that the SSE endpoint URL should end with `/sse` (e.g., `http://localhost:8000/sse`).

**Package not found or version mismatch**

If you're experiencing import errors or version compatibility issues, try installing a specific version of the MCP package:

```bash
pip install mcp>=1.0.0
```

Note that the package name is simply `mcp`, not `mcp-sdk`.

If the issue persists, check the [official MCP Python SDK repository](https://github.com/modelcontextprotocol/python-sdk) for the latest installation instructions.

## License

This project is provided as an example implementation and is available under the MIT License.
