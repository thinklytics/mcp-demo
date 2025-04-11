"""
MCP Client Example

This script demonstrates how to connect to an MCP server and use its tools.
"""

import asyncio
import sys
import argparse
import json
from typing import Any, Dict, List, Optional, Union
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

# Import models
from models import (
    Document, 
    DocumentMetadata, 
    SearchResult, 
    AddDocumentRequest, 
    AddDocumentResponse,
    SearchRequest
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
                    # Parse JSON text into dict
                    data = json.loads(content_item.text)
                    # Convert dict to model
                    if isinstance(data, list):
                        for item in data:
                            results.append(model_class(**item))
                    else:
                        results.append(model_class(**data))
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"Error parsing response: {e}")
        
        return results if len(results) > 1 else results[0] if results else None
    
    # Handle direct dict or list response
    elif isinstance(response, dict):
        return model_class(**response)
    elif isinstance(response, list):
        return [model_class(**item) for item in response if isinstance(item, dict)]
    
    # Return original response if can't parse
    return response


async def main(server_url: str = None):
    """Main client function
    
    Args:
        server_url: URL of the MCP server's SSE endpoint
    """
    if not server_url:
        # Default server URL
        server_url = "http://localhost:8000"
        
    # Make sure we have the /sse endpoint
    if not server_url.endswith("/sse"):
        server_url = f"{server_url}/sse"
    
    print(f"Connecting to MCP server at {server_url}...")
    
    try:
        async with sse_client(server_url) as streams:
            print("Stream connection established, initializing session...")
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                print("✅ Connected to MCP server!")
                
                # List available tools, resources, and prompts
                print_items("tools", (await session.list_tools()))
                print_items("resources", (await session.list_resources()))
                print_items("prompts", (await session.list_prompts()))
                
                # Get a greeting prompt
                prompt = await session.get_prompt("greeting", arguments={"name": "User"})
                print("\nGreeting prompt:")
                for message in prompt.messages:
                    print(f"- {message.content.text}")
                
                # Call the echo tool
                echo_result = await session.call_tool("echo", arguments={"message": "Hello, MCP!"})
                print(f"\nEcho result: {echo_result}")
                
                # Add a document
                try:
                    # Create a document metadata
                    metadata = DocumentMetadata(
                        source="documentation",
                        topic="MCP",
                        # Don't set created_at, it will be added by the server
                    )
                    
                    # Create request
                    request = AddDocumentRequest(
                        content="MCP (Model Context Protocol) is a protocol that allows AI models to interact with external tools and data sources.",
                        metadata=metadata.model_dump(exclude_none=True, exclude_unset=True)
                    )
                    
                    # Call the tool
                    doc_result = await session.call_tool(
                        "add_document", 
                        arguments=request.model_dump(exclude_none=True, exclude_unset=True)
                    )
                    
                    # Parse response
                    response = parse_response(doc_result, AddDocumentResponse)
                    if isinstance(response, AddDocumentResponse) and response.status == "success":
                        print(f"Document added with ID: {response.id}")
                    else:
                        print(f"❌ Error adding document: {response}")
                except Exception as e:
                    print(f"❌ Error adding document: {e}")
                
                # Add another document
                try:
                    # Create a document metadata
                    metadata = DocumentMetadata(
                        source="documentation",
                        topic="RAG"
                    )
                    
                    # Create request
                    request = AddDocumentRequest(
                        content="RAG (Retrieval-Augmented Generation) is a technique that combines the generative capabilities of large language models with information retrieval systems.",
                        metadata=metadata.model_dump(exclude_none=True, exclude_unset=True)
                    )
                    
                    # Call the tool
                    doc_result = await session.call_tool(
                        "add_document", 
                        arguments=request.model_dump(exclude_none=True, exclude_unset=True)
                    )
                    
                    # Parse response
                    response = parse_response(doc_result, AddDocumentResponse)
                    if isinstance(response, AddDocumentResponse) and response.status == "success":
                        print(f"Document added with ID: {response.id}")
                    else:
                        print(f"❌ Error adding document: {response}")
                except Exception as e:
                    print(f"❌ Error adding document: {e}")
                
                # List documents
                try:
                    docs_result = await session.call_tool("list_documents")
                    documents = parse_response(docs_result, Document)
                    
                    print("\nDocuments in knowledge base:")
                    if not documents:
                        print("  No documents found")
                    elif isinstance(documents, list):
                        for doc in documents:
                            print(f"- {doc.id}: {doc.preview}")
                            if doc.metadata:
                                meta_str = ", ".join([f"{k}: {v}" for k, v in doc.metadata.model_dump(exclude_none=True, exclude_defaults=True).items() if v])
                                if meta_str:
                                    print(f"  Metadata: {meta_str}")
                    else:
                        print(f"- {documents.id}: {documents.preview}")
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
                    
                    print("\nSearch results for 'What is MCP?':")
                    if not results:
                        print("  No results found")
                    elif isinstance(results, list):
                        for item in results:
                            print(f"- Document: {item.document}")
                            print(f"  Score: {item.score}")
                            if item.metadata:
                                meta_str = ", ".join([f"{k}: {v}" for k, v in item.metadata.model_dump(exclude_none=True, exclude_defaults=True).items() if v])
                                if meta_str:
                                    print(f"  Metadata: {meta_str}")
                    else:
                        print(f"- Document: {results.document}")
                        print(f"  Score: {results.score}")
                        if results.metadata:
                            meta_str = ", ".join([f"{k}: {v}" for k, v in results.metadata.model_dump(exclude_none=True, exclude_defaults=True).items() if v])
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
                
    except ConnectionRefusedError:
        print("❌ Connection refused: The server is not running or not accessible")
        print("\nMake sure you have started the server first with one of these commands:")
        print("  - python server.py")
        print("  - python server_with_models.py")
        print("  - uvicorn server:mcp.sse_app --host 0.0.0.0 --port 8000")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure the server is running")
        print("2. Check if the server URL is correct (should end with /sse)")
        print("3. Try running the client with a specific server URL:")
        print("   python client_example.py --server http://localhost:8000/sse")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MCP Client Example")
    parser.add_argument("--server", type=str, help="URL of the MCP server (e.g. http://localhost:8000)")
    args = parser.parse_args()
    
    asyncio.run(main(args.server))
