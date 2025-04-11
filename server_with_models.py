"""
MCP Server with RAG Capabilities using Pydantic Models

This server demonstrates MCP (Model Context Protocol) with RAG (Retrieval-Augmented Generation)
capabilities, allowing AI models to interact with a knowledge base.
"""

from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Mount
from tools.rag_tools import register_rag_tools
import os
import sys
import uvicorn
from datetime import datetime

# Import models for documentation
from models import DocumentMetadata, Document, SearchResult, AddDocumentRequest, AddDocumentResponse, SearchRequest

print("Initializing MCP server with RAG capabilities...")

try:
    # Create a new MCP server
    mcp = FastMCP("MCP with RAG Demo")
    print("✅ MCP server instance created")

    # Add a simple echo tool
    @mcp.tool()
    def echo(message: str) -> str:
        """Echo back the provided message"""
        return f"Echo: {message}"

    # Add a simple add tool
    @mcp.tool()
    def add(a: float, b: float) -> float:
        """Add two numbers together"""
        return a + b

    print("✅ Basic tools registered")

    # Add a greeting prompt template
    @mcp.prompt()
    def greeting(name: str) -> str:
        """Create a greeting prompt for the user"""
        return f"""Hello {name}! I'm an AI assistant with access to a knowledge base.
        
    You can ask me to:
    1. Search for information using the knowledge base
    2. Add new information to the knowledge base
    3. List all documents in the knowledge base
    4. Perform simple calculations

    How can I help you today?"""

    print("✅ Prompt templates registered")

    # Register RAG tools
    try:
        print("Registering RAG tools...")
        mcp = register_rag_tools(mcp)
        print("✅ RAG tools registered successfully")
    except Exception as e:
        print(f"❌ Error registering RAG tools: {str(e)}")
        print("The server will continue without RAG capabilities")

    # Sample data resource for quick access
    sample_file_path = os.path.join(os.path.dirname(__file__), "sample_data.txt")

    @mcp.resource("sample://data")
    def get_sample_data() -> str:
        """Retrieve sample data as a resource"""
        try:
            with open(sample_file_path, "r") as f:
                return f.read()
        except FileNotFoundError:
            return "Sample data file not found"

    print("✅ Resources registered")

    # Create the ASGI application with the SSE endpoint mounted
    app = Starlette(
        routes=[
            Mount("/", app=mcp.sse_app()),
        ]
    )

    # Run the server
    if __name__ == "__main__":
        print("\n🚀 Starting MCP server...")
        print("\nServer endpoints:")
        print("- SSE endpoint: http://localhost:8000/sse (use this for client connections)")
        print("\nRun client with:")
        print("python client_example.py")
        print("\nOr with a custom server URL:")
        print("python client_example.py --server http://localhost:8000")
        print("\nPress Ctrl+C to exit")
        
        try:
            # Run the server directly using uvicorn
            uvicorn.run(app, host="0.0.0.0", port=8000)
        except KeyboardInterrupt:
            print("\n👋 Server shutdown requested via Ctrl+C")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Error running MCP server: {str(e)}")
            print("\nTry running directly with uvicorn:")
            print("uvicorn server_with_models:app --host 0.0.0.0 --port 8000")
            sys.exit(1)
except Exception as e:
    print(f"❌ Fatal error initializing MCP server: {str(e)}")
    sys.exit(1) 