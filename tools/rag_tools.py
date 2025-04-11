"""
RAG Tools for MCP Server

This module provides retrieval-augmented generation (RAG) capabilities for the MCP server.
"""

from mcp.server.fastmcp import FastMCP
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.errors import InternalError
import os
import json
from datetime import datetime
from typing import List

# Import the shared models
from models import (
    Document, 
    DocumentMetadata, 
    SearchResult, 
    AddDocumentRequest, 
    AddDocumentResponse,
    SearchRequest
)


def register_rag_tools(mcp_instance: FastMCP):
    """Register RAG-related tools with the MCP server"""
    
    # Initialize components
    model = SentenceTransformer('all-MiniLM-L6-v2')
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    
    # Create collection or get if exists
    try:
        collection = chroma_client.create_collection("documents")
        print("✅ Created new ChromaDB collection: 'documents'")
    except (ValueError, InternalError) as e:
        # Collection already exists - either ValueError or InternalError depending on the version
        print(f"ℹ️ Collection 'documents' already exists, using existing collection")
        collection = chroma_client.get_collection("documents")
    
    @mcp_instance.tool()
    def rag_search(query: str, top_k: int = 3) -> List[SearchResult]:
        """Search the knowledge base for information related to the query"""
        try:
            # Embed the query
            query_embedding = model.encode(query).tolist()
            
            # Search the collection
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            # Handle empty results
            if not results or "documents" not in results or not results["documents"] or len(results["documents"][0]) == 0:
                return [SearchResult(
                    document="No relevant documents found",
                    metadata=DocumentMetadata(),
                    score=0.0
                ).model_dump()]
            
            search_results = []
            for i in range(len(results["documents"][0])):
                # Get document content
                doc_content = results["documents"][0][i]
                
                # Get metadata safely
                raw_metadata = results["metadatas"][0][i] if results.get("metadatas") and results["metadatas"][0] else {}
                
                # Create DocumentMetadata, differentiating between known fields and extra fields
                known_fields = {"source", "topic", "created_at"}
                extra_fields = {k: v for k, v in raw_metadata.items() if k not in known_fields}
                metadata_dict = {k: v for k, v in raw_metadata.items() if k in known_fields}
                metadata_dict["extra_fields"] = extra_fields
                
                # Get score safely
                score = results["distances"][0][i] if results.get("distances") and results["distances"][0] else 0.0
                
                # Create SearchResult object
                result = SearchResult(
                    document=doc_content,
                    metadata=DocumentMetadata(**metadata_dict),
                    score=score
                )
                search_results.append(result.model_dump())
                
            return search_results
        except Exception as e:
            print(f"Error in rag_search: {str(e)}")
            return [SearchResult(
                document=f"Error searching knowledge base: {str(e)}",
                metadata=DocumentMetadata(),
                score=0.0
            ).model_dump()]
    
    @mcp_instance.tool()
    def add_document(content: str, metadata: dict = None) -> AddDocumentResponse:
        """Add a document to the knowledge base"""
        try:
            # Parse and validate the input
            if metadata is None:
                metadata = {}
            
            # Ensure metadata is properly formatted
            if not isinstance(metadata, dict):
                metadata = {}
            
            # Remove any None values from metadata
            metadata = {k: v for k, v in metadata.items() if v is not None}
                
            # Add timestamp if not provided
            if "created_at" not in metadata:
                metadata["created_at"] = datetime.now().isoformat()
                
            # Generate a document ID
            collection_data = collection.get()
            doc_count = len(collection_data.get("ids", [])) if collection_data else 0
            doc_id = f"doc_{doc_count + 1}"
            
            # Embed the document
            embedding = model.encode(content).tolist()
            
            # Add to collection
            collection.add(
                documents=[content],
                embeddings=[embedding],
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            return AddDocumentResponse(
                status="success",
                id=doc_id
            ).model_dump()
        except Exception as e:
            print(f"Error in add_document: {str(e)}")
            return AddDocumentResponse(
                status="error",
                message=str(e)
            ).model_dump()
    
    @mcp_instance.tool()
    def list_documents() -> List[Document]:
        """List all documents in the knowledge base"""
        docs = collection.get()
        
        # Handle empty collection
        if not docs or "ids" not in docs or not docs["ids"]:
            return []
            
        results = []
        for i, doc_id in enumerate(docs["ids"]):
            # Safe access to document content
            preview = ""
            if i < len(docs.get("documents", [])) and docs["documents"][i] is not None:
                doc_content = docs["documents"][i]
                preview = doc_content[:100] + "..." if len(doc_content) > 100 else doc_content
            
            # Safe access to metadata
            raw_metadata = {}
            if docs.get("metadatas") and i < len(docs["metadatas"]) and docs["metadatas"][i] is not None:
                raw_metadata = docs["metadatas"][i]
            
            # Create DocumentMetadata, differentiating between known fields and extra fields
            known_fields = {"source", "topic", "created_at"}
            extra_fields = {k: v for k, v in raw_metadata.items() if k not in known_fields}
            metadata_dict = {k: v for k, v in raw_metadata.items() if k in known_fields}
            metadata_dict["extra_fields"] = extra_fields
                
            # Create Document object
            document = Document(
                id=doc_id,
                preview=preview,
                metadata=DocumentMetadata(**metadata_dict)
            )
            results.append(document.model_dump())
                
        return results
    
    @mcp_instance.resource("documents://all")
    def get_all_documents() -> str:
        """Retrieve all documents as a resource"""
        docs = collection.get()
        
        # Handle empty collection
        if not docs or "ids" not in docs or not docs["ids"]:
            return "No documents available in the knowledge base."
            
        formatted_docs = ""
        for i, doc_id in enumerate(docs["ids"]):
            formatted_docs += f"--- Document {doc_id} ---\n"
            if i < len(docs.get("documents", [])) and docs["documents"][i] is not None:
                formatted_docs += docs["documents"][i] + "\n\n"
            else:
                formatted_docs += "(Document content unavailable)\n\n"
                
        return formatted_docs
    
    return mcp_instance
