# MCP with RAG Demo

This demonstration project shows how to implement a Model Context Protocol (MCP) server with Retrieval-Augmented Generation (RAG) capabilities. The demo allows AI models to interact with a knowledge base, search for information, and add new documents.

## Features

- MCP server with tool and resource support
- RAG implementation (with fallback to in-memory storage)
- Client example for interacting with the MCP server
- Support for both SSE (HTTP) and stdio communication modes
- Simple prompt templates

## Prerequisites

- Python 3.8+
- pip (Python package manager)

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd mcp-demo
```

2. Create a virtual environment:

```bash
python -m venv mcp-env
source mcp-env/bin/activate  # On Windows: mcp-env\Scripts\activate
```

3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Project Structure

```
mcp-demo/
├── server.py           # Main MCP server implementation
├── client_example.py   # Example client to interact with the server
├── requirements.txt    # Project dependencies
├── sample_data.txt     # Sample data available as a resource
├── tools/
│   ├── __init__.py     # Package initialization
│   └── rag_tools.py    # RAG tools implementation
└── README.md           # This readme file
```

## Running the Demo

### Step 1: Start the MCP Server

You can run the MCP server in two different modes:

#### Option A: SSE (HTTP) Mode

This mode allows the server to accept connections over HTTP using Server-Sent Events (SSE):

```bash
python server.py --sse
```

By default, the server will listen on `0.0.0.0:8000`. You can customize the host and port:

```bash
python server.py --sse --host 127.0.0.1 --port 9000
```

#### Option B: stdio Mode

This mode allows the server to communicate through standard input/output:

```bash
python server.py --stdio
```

### Step 2: Run the Client Example

After the server is up and running, open a new terminal window (keeping the server running in the first one):

#### Connecting to an SSE Server

```bash
# Make sure your virtual environment is activated
source mcp-env/bin/activate  # On Windows: mcp-env\Scripts\activate

# Run the client with SSE mode
python client_example.py --sse http://localhost:8000
```

The client will automatically append "/sse" to the URL if it's not already present.

#### Connecting via stdio

```bash
# Make sure your virtual environment is activated
source mcp-env/bin/activate  # On Windows: mcp-env\Scripts\activate

# Run the client with stdio mode
python client_example.py --stdio --command python --args "server.py --stdio"
```

You can customize the command and arguments as needed.

## What the Client Example Does

The client example demonstrates several key operations:

1. **Lists available tools, resources, and prompts** from the MCP server
2. **Calls the echo tool** to verify basic communication
3. **Adds documents to the knowledge base** with metadata
4. **Searches the knowledge base** using the RAG system
5. **Reads a sample resource** from the server

## Available MCP Tools

The following tools are available in this demo:

- `echo`: A simple tool that echoes back the provided message
- `add`: A tool that adds two numbers together
- `add_document`: Adds a document to the knowledge base
- `rag_search`: Searches the knowledge base for information related to a query
- `list_documents`: Lists all documents in the knowledge base

## Available MCP Resources

- `sample://data`: Provides access to the sample data in sample_data.txt

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

## Troubleshooting

### Client Connection Issues

If you get a "Connection refused" error when running the client:

1. Make sure the server is actually running in another terminal window
2. Check that you're using the correct URL (default is http://localhost:8000)
3. Ensure the server is listening on the expected interface (0.0.0.0 to accept external connections)
4. Try specifying the server URL explicitly: `python client_example.py --sse http://localhost:8000`

### Server Endpoint Issues

The MCP server exposes an SSE (Server-Sent Events) endpoint at `/sse`. When connecting with the client:

- The full URL should be `http://localhost:8000/sse`
- The client will automatically append `/sse` if it's missing from your specified URL

### Debug Mode

If you encounter issues, you can enable debug mode for more verbose output:

```bash
python client_example.py --sse http://localhost:8000 --debug
```

### Common Issues

**Import errors with client connection**

If you see import errors when running the client example, make sure you have installed all the required dependencies:

```bash
pip install mcp-sdk
```

**Package not found or version mismatch**

If you're experiencing import errors or version compatibility issues, try installing a specific version of the MCP package:

```bash
pip install mcp-sdk>=1.0.0
```

## License

This project is provided as an example implementation and is available under the MIT License.

## Setup

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file:
   ```bash
   cp .env.example .env
   ```

3. Edit the `.env` file and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

   You can also configure other options in the `.env` file:
   - `MCP_SERVER_URL`: The URL of the MCP server (default: http://localhost:3000)
   - `DEBUG`: Enable debug mode (default: false)

## Usage

Run the demo with:

```bash
python openai_example.py
```

You can override the settings in the `.env` file by using command-line arguments:

```bash
python openai_example.py --api-key YOUR_API_KEY --server-url http://your-server-url
```

## Environment Variables

The following environment variables can be set in the `.env` file:

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `MCP_SERVER_URL`: The URL of the MCP server (optional)
- `DEBUG`: Enable debug mode (optional)

## Command-line Arguments

- `--api-key`: Your OpenAI API key (overrides the .env file)
- `--server-url`: The URL of the MCP server (overrides the .env file)
- `--debug`: Enable debug mode (overrides the .env file)

# MCP OpenAI Example

This example demonstrates how to use the Model Control Protocol (MCP) with OpenAI's API.

## Setup

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Create a `.env` file based on the `.env.example` template:
   ```
   cp .env.example .env
   ```

3. Edit the `.env` file and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Running the Example

Run the example script:

```
python openai_example.py
```

You can also specify options directly:

```
python openai_example.py --api-key your_api_key_here --server-url http://localhost:3000 --debug
```

## What the Example Does

1. Loads environment variables from the `.env` file
2. Configures the OpenAI client with your API key
3. Lists available models
4. Creates a chat completion with a simple prompt

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `MCP_SERVER_URL`: URL of the MCP server (optional, defaults to http://localhost:3000)
- `DEBUG`: Enable debug logging (optional, defaults to false)
