"""
MCP Server with RAG Capabilities

This server demonstrates MCP (Model Context Protocol) with RAG (Retrieval-Augmented Generation)
capabilities, allowing AI models to interact with a knowledge base.
"""

from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Mount
import os
import sys
import uvicorn
import argparse
from datetime import datetime
from typing import List, Dict, Any
from tools.rag_tools import register_rag_tools, in_memory_rag_tools

print("Initializing MCP server with RAG capabilities...")

def setup_mcp():
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

    # Try to register RAG tools from the tools module
    try:
        print("Registering RAG tools...")
        mcp = register_rag_tools(mcp)
        print("✅ RAG tools registered successfully")
    except Exception as e:
        print(f"❌ Error registering RAG tools from module: {str(e)}")
        print("Falling back to simple in-memory implementation")
        print("(To use ChromaDB, ensure Python dependencies are installed and check the .env file for CHROMA_DB_PATH)")
        
        # Implement simple in-memory RAG tools as fallback
        # For simple implementation we'll use a dictionary
        mcp = in_memory_rag_tools(mcp)
        print("✅ In-memory RAG tools registered successfully")

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
    
    return mcp

try:
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="MCP Server with RAG capabilities")
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--stdio", action="store_true", help="Run server in stdio mode")
    mode_group.add_argument("--sse", action="store_true", help="Run server in SSE (HTTP) mode")
    parser.add_argument("--host", default="0.0.0.0", help="HTTP server host (for SSE mode)")
    parser.add_argument("--port", type=int, default=8000, help="HTTP server port (for SSE mode)")
    
    if __name__ == "__main__":
        args = parser.parse_args()
        
        # Set up MCP server
        mcp = setup_mcp()
        
        if args.stdio:
            print("\n🚀 Starting MCP server in stdio mode...")
            print("Communicating through standard input/output")
            print("Press Ctrl+C to exit")
            
            try:
                # Run the server in stdio mode
                mcp.run(transport="stdio")
            except KeyboardInterrupt:
                print("\n👋 Server shutdown requested via Ctrl+C")
                sys.exit(0)
            except Exception as e:
                print(f"\n❌ Error running MCP stdio server: {str(e)}")
                sys.exit(1)
        else:  # args.sse must be True due to mutually exclusive group with required=True
            # Create the ASGI application with the SSE endpoint mounted
            app = Starlette(
                routes=[
                    Mount("/", app=mcp.sse_app()),
                ]
            )
            
            print("\n🚀 Starting MCP server in SSE (HTTP) mode...")
            print(f"\nServer endpoints:")
            print(f"- SSE endpoint: http://{args.host}:{args.port}/sse (use this for client connections)")
            print("\nRun client with:")
            print(f"python client_example.py --sse http://{args.host}:{args.port}")
            print("\nPress Ctrl+C to exit")
            
            try:
                # Run the server directly using uvicorn
                uvicorn.run(app, host=args.host, port=args.port)
            except KeyboardInterrupt:
                print("\n👋 Server shutdown requested via Ctrl+C")
                sys.exit(0)
            except Exception as e:
                print(f"\n❌ Error running MCP HTTP server: {str(e)}")
                print("\nTry running directly with uvicorn or uv:")
                print(f"uvicorn server:app --host {args.host} --port {args.port}")
                print(f"uv run server.py --sse --host {args.host} --port {args.port}")
                sys.exit(1)
except Exception as e:
    print(f"❌ Fatal error initializing MCP server: {str(e)}")
    sys.exit(1)
