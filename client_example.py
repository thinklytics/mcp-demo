"""
MCP Client Example

This script demonstrates how to connect to an MCP server and use its tools.
"""

import asyncio
import sys
import argparse
import json
import shlex
from typing import Any, Dict, List, Optional, Union
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client
from mcp.client.stdio import StdioServerParameters, stdio_client
import os
from pathlib import Path
import shutil

# Import models
from models import (
    Document, 
    DocumentMetadata, 
    SearchResult, 
    AddDocumentRequest, 
    AddDocumentResponse,
    SearchRequest,
    DocumentStatus
)


def print_items(name: str, result: Any) -> None:
    """Print items with formatting.
    
    Args:
        name: Category name (tools/resources/prompts)
        result: Result object containing items list
    """
    print("", f"Available {name}:", sep="\n")
    items = getattr(result, name)
    if items:
        for item in items:
            print(" *", item)
    else:
        print("  No items available")


# Helper function to convert response to models
def parse_response(response, model_class):
    """Parse MCP response into Pydantic models.
    
    Args:
        response: Response from MCP server
        model_class: Pydantic model class to parse into
        
    Returns:
        List of model instances or single model instance
    """
    # Handle ContentObject response (with TextContent)
    if hasattr(response, 'content') and hasattr(response, 'meta'):
        content_items = response.content
        
        # Handle empty response
        if not content_items:
            return []
            
        # Parse text content into models
        results = []
        for content_item in content_items:
            if hasattr(content_item, 'text') and content_item.text:
                try:
                    # For some tools (like echo), the response might not be JSON
                    if content_item.text.startswith('Echo:'):
                        # Special handling for echo tool responses
                        continue
                        
                    # Parse JSON text into dict
                    data = json.loads(content_item.text)
                    # Convert dict to model
                    if isinstance(data, list):
                        for item in data:
                            results.append(model_class(**item))
                    else:
                        results.append(model_class(**data))
                except json.JSONDecodeError as e:
                    print(f"Error parsing response: {e}")
                    # Don't treat as an error for non-JSON responses from tools like echo
                except (TypeError, ValueError) as e:
                    print(f"Error parsing model: {e}")
        
        return results if len(results) > 1 else results[0] if results else None
    
    # Handle direct dict or list response
    elif isinstance(response, dict):
        try:
            return model_class(**response)
        except (TypeError, ValueError) as e:
            print(f"Error creating model from dict: {e}")
            return None
    elif isinstance(response, list):
        try:
            return [model_class(**item) for item in response if isinstance(item, dict)]
        except (TypeError, ValueError) as e:
            print(f"Error creating model from list item: {e}")
            return []
    
    # Return original response if can't parse
    return response


async def run_sse_client(server_url: str):
    """Run MCP client in SSE mode.
    
    Args:
        server_url: URL of the MCP server's SSE endpoint
    """
    print(f"Connecting to MCP server at {server_url} via SSE...")
    
    try:
        async with sse_client(server_url) as streams:
            print("Stream connection established, initializing session...")
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                print("✅ Connected to MCP server!")
                
                # Run the common client operations
                await run_client_operations(session)
                
    except Exception as e:
        print(f"❌ Error connecting to MCP server: {e}")
        sys.exit(1)


async def run_stdio_client(command: str, args: List[str] = None):
    """Run MCP client in stdio mode.
    
    Args:
        command: Command to run the MCP server
        args: Optional arguments for the command
    """
    if args is None:
        args = []
        
    print(f"Starting MCP server with command: {command}")
    if args:
        print(f"Arguments: {args}")
    
    try:
        # Create StdioServerParameters
        params = StdioServerParameters(
            command=command,
            args=args,
            env=os.environ.copy()
        )
        
        # Connect to the server via stdio
        print("Establishing stdio connection...")
        async with stdio_client(params) as (read, write):
            print("Stream connection established, initializing session...")
            try:
                async with ClientSession(read, write) as session:
                    print("Client session created, initializing...")
                    await session.initialize()
                    print("✅ Connected to MCP server!")
                    
                    # Run the common client operations
                    await run_client_operations(session)
            except Exception as e:
                print(f"❌ Error during client session: {e}", file=sys.stderr)
                # Print more detailed error information
                import traceback
                traceback.print_exc(file=sys.stderr)
                sys.exit(1)
                
    except Exception as e:
        print(f"❌ Error connecting to MCP server: {e}", file=sys.stderr)
        # Print more detailed error information
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


# Helper function to add a document with consistent error handling
async def add_document_with_metadata(session, content, metadata_dict):
    """Add a document to the knowledge base with provided metadata.
    
    Args:
        session: Initialized MCP client session
        content: Document content
        metadata_dict: Metadata dictionary for the document
        
    Returns:
        True if document was successfully added, False otherwise
    """
    try:
        # Create metadata object
        metadata = DocumentMetadata(**metadata_dict)
        
        # Create request
        request = AddDocumentRequest(
            content=content,
            metadata=metadata.model_dump(exclude_none=True, exclude_unset=True)
        )
        
        # Call the tool
        doc_result = await session.call_tool(
            "add_document", 
            arguments=request.model_dump(exclude_none=True, exclude_unset=True)
        )
        
        # Parse response
        response = parse_response(doc_result, AddDocumentResponse)
        if response:
            if response.status == DocumentStatus.SUCCESS:
                print(f"Document added with ID: {response.id}")
                return True
            elif response.status == DocumentStatus.DUPLICATE:
                print(f"Document already exists with ID: {response.id}")
                print(f"Note: {response.message}")
                return True  # Still consider this successful
            else:
                print(f"❌ Document add failed: {getattr(response, 'message', 'Unknown error')}")
                return False
        else:
            print(f"❌ Document add failed: Unknown response")
            return False
    except Exception as e:
        print(f"❌ Error adding document: {e}")
        return False


async def run_client_operations(session: ClientSession):
    """Run common client operations with the provided session.
    
    Args:
        session: Initialized MCP client session
    """
    # List available tools, resources, and prompts
    print_items("tools", (await session.list_tools()))
    print_items("resources", (await session.list_resources()))
    print_items("prompts", (await session.list_prompts()))
    
    # Call the echo tool
    echo_result = await session.call_tool("echo", arguments={"message": "Hello, MCP!"})
    print(f"\nEcho result: {echo_result}")
    
    await add_document_with_metadata(
        session,
        "Thinklytics is a blog series for strategic thinking and decisions making via data analytics.",
        {"source": "documentation", "topic": "Blog Series"}
    )

    await add_document_with_metadata(
        session,
        "MCP (Model Context Protocol) is a protocol that allows AI models to interact with external tools and data sources.",
        {"source": "documentation", "topic": "MCP"}
    )

    
    await add_document_with_metadata(
        session,
        "RAG (Retrieval-Augmented Generation) is a technique that combines the generative capabilities of large language models with information retrieval systems.",
        {"source": "documentation", "topic": "RAG"}
    )
    
    # List documents
    try:
        docs_result = await session.call_tool("list_documents")
        
        # Parse response
        documents = parse_response(docs_result, Document)
        if not documents:
            documents = []
        elif not isinstance(documents, list):
            documents = [documents]
        
        print("\nDocuments in knowledge base:")
        if not documents:
            print("  No documents found")
        else:
            for doc in documents:
                print(f"- {doc.id}: {doc.preview}")
                if doc.metadata:
                    meta_str = ", ".join([f"{k}: {v}" for k, v in doc.metadata.model_dump(exclude_none=True, exclude_defaults=True).items() if v])
                    if meta_str:
                        print(f"  Metadata: {meta_str}")
    except Exception as e:
        print(f"\n❌ Error listing documents: {e}")
        print("  Continuing with other operations...")
    
    # Search for information
    try:
        # Create search request
        search_req = SearchRequest(query="What is MCP?", top_k=1)
        
        # Call the search tool
        search_result = await session.call_tool(
            "rag_search", 
            arguments=search_req.model_dump()
        )
        
        # Parse response
        results = parse_response(search_result, SearchResult)
        if not isinstance(results, list):
            results = [results] if results else []
        
        print("\nSearch results for 'What is MCP?':")
        if not results:
            print("  No results found")
        else:
            for item in results:
                print(f"- Document: {item.document}")
                print(f"  Score: {item.score}")
                if item.metadata:
                    meta_str = ", ".join([f"{k}: {v}" for k, v in item.metadata.model_dump(exclude_none=True, exclude_defaults=True).items() if v])
                    if meta_str:
                        print(f"  Metadata: {meta_str}")
    except Exception as e:
        print(f"\n❌ Error searching documents: {e}")
        print("  Continuing with other operations...")
    
    # Read a resource
    try:
        sample_data, mime_type = await session.read_resource("sample://data")
        print(f"\nSample data resource (mime type: {mime_type}):")
        if sample_data:
            print(f"{sample_data[:200]}..." if len(sample_data) > 200 else sample_data)
        else:
            print("  No content available")
    except Exception as e:
        print(f"\n❌ Error reading resource: {e}")


async def main():
    """Main client function that handles both SSE and stdio modes."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="MCP Client Example")
    
    # Connection mode selection
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--sse", metavar="URL", help="Connect to MCP server via SSE at the specified URL")
    mode_group.add_argument("--stdio", action="store_true", help="Connect to MCP server via stdio")
    
    # Additional parameters
    parser.add_argument("--command", help="Command to run MCP server (for stdio mode)", default="npx")
    parser.add_argument("--args", help="Arguments for the stdio command (can use quoted strings for arguments with spaces)", default="")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode with more verbose output")
    
    args = parser.parse_args()
    
    # Enable debug mode if requested
    if args.debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)
        print("Debug mode enabled")
    
    # Run in the appropriate mode
    if args.sse:
        server_url = args.sse
        # Make sure we have the /sse endpoint
        if not server_url.endswith("/sse"):
            server_url = f"{server_url}/sse"
        await run_sse_client(server_url)
    else:  # stdio mode
        command = args.command
        # Use shlex.split to properly handle quoted arguments with spaces
        command_args = shlex.split(args.args) if args.args else []
        
        # Print environment information for debugging
        print(f"Python version: {sys.version}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Command path: {shutil.which(command) if command != 'npx' else 'npx (npm)'}")
        
        await run_stdio_client(command, command_args)


if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())
