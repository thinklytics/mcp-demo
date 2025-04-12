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
import logging
from datetime import datetime
from typing import List, Dict, Any
import dotenv
from pathlib import Path

# Import the shared models
from models import (
    Document, 
    DocumentMetadata, 
    SearchResult, 
    AddDocumentRequest, 
    AddDocumentResponse,
    SearchRequest,
    DocumentStatus
)

# Load environment variables
dotenv.load_dotenv()

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)

def register_rag_tools(mcp_instance: FastMCP):
    """Register RAG-related tools with the MCP server"""
    
    # Initialize components
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Get project root directory
    project_root = Path(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
    
    # Get ChromaDB path from environment variable or use default (project root + chroma_db)
    default_path = os.path.join(project_root, "chroma_db")
    chroma_db_path = os.getenv("CHROMA_DB_PATH", default_path)
    log.info(f"Using ChromaDB path: {chroma_db_path}")
    
    # Create directory if it doesn't exist
    Path(chroma_db_path).mkdir(parents=True, exist_ok=True)
    
    try:
        # Initialize the ChromaDB client
        chroma_client = chromadb.PersistentClient(path=chroma_db_path)
        
        # Check if collection exists - compatible with v0.6.0+
        collection_names = chroma_client.list_collections()
        print(f"Collection names: {collection_names}")
        
        # Handle different versions of ChromaDB API
        collection_exists = False
        if collection_names:
            if isinstance(collection_names[0], str):
                # ChromaDB v0.6.0+ returns strings
                collection_exists = "documents" in collection_names
            else:
                # Older versions return objects with name attribute
                collection_exists = any(getattr(col, 'name', None) == "documents" for col in collection_names)
        
        print(f"Collection exists: {collection_exists}")
        if collection_exists:
            collection = chroma_client.get_collection("documents")
            print("✅ Using existing ChromaDB collection: 'documents'")
        else:
            collection = chroma_client.create_collection("documents")
            print("✅ Created new ChromaDB collection: 'documents'")
    except Exception as e:
        print(f"❌ Error initializing ChromaDB: {str(e)}")
        raise
    
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
    
    # Helper function to check for duplicate documents
    def check_for_duplicate_document(content, collection):
        """Check if a document with the same content already exists in the collection.
        
        Args:
            content: The document content to check
            collection: The ChromaDB collection
            
        Returns:
            Tuple of (exists: bool, document_id: str or None)
        """
        collection_data = collection.get()
        
        # Check for empty collection
        if not collection_data or "documents" not in collection_data or not collection_data["documents"]:
            return False, None
            
        # Check each document for matching content
        for i, doc_content in enumerate(collection_data["documents"]):
            if doc_content == content:
                return True, collection_data["ids"][i]
                
        return False, None
    
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
            
            # Check for duplicate content
            exists, duplicate_id = check_for_duplicate_document(content, collection)
            
            if exists:
                # Return information about the duplicate document
                return AddDocumentResponse(
                    status=DocumentStatus.DUPLICATE,
                    id=duplicate_id,
                    message=f"Document with this content already exists with ID: {duplicate_id}"
                ).model_dump()
            
            # Get collection data for ID generation
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
                status=DocumentStatus.SUCCESS,
                id=doc_id
            ).model_dump()
        except Exception as e:
            print(f"Error in add_document: {str(e)}")
            return AddDocumentResponse(
                status=DocumentStatus.ERROR,
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

def in_memory_rag_tools(mcp_instance: FastMCP):
    """Register RAG-related tools with the MCP server"""
    in_memory_docs = {}
        
    # Helper function to check for duplicate documents
    def check_for_duplicate_document(content):
        """Check if a document with the same content already exists in the in-memory storage.
        
        Args:
            content: The document content to check
            
        Returns:
            Tuple of (exists: bool, document_id: str or None)
        """
        for doc_id, doc_data in in_memory_docs.items():
            if doc_data["content"] == content:
                return True, doc_id
        return False, None
    
    @mcp_instance.tool()
    def add_document(content: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Add a document to the knowledge base"""
        try:
            # Ensure metadata is properly formatted
            if metadata is None or not isinstance(metadata, dict):
                metadata = {}
            
            # Add timestamp if not provided
            if "created_at" not in metadata:
                metadata["created_at"] = datetime.now().isoformat()
            
            # Check for duplicate content
            exists, duplicate_id = check_for_duplicate_document(content)
            
            if exists:
                # Return information about the duplicate document
                return {
                    "status": "duplicate",
                    "id": duplicate_id,
                    "message": f"Document with this content already exists with ID: {duplicate_id}"
                }
            
            # Generate a document ID
            doc_id = f"doc_{len(in_memory_docs) + 1}"
            
            # Add to in-memory collection
            in_memory_docs[doc_id] = {
                "content": content,
                "metadata": metadata
            }
            
            return {
                "status": "success",
                "id": doc_id
            }
        except Exception as e:
            print(f"Error in add_document: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    @mcp_instance.tool()
    def list_documents() -> List[Dict[str, Any]]:
        """List all documents in the knowledge base"""
        results = []
        for doc_id, doc_data in in_memory_docs.items():
            content = doc_data["content"]
            preview = content[:100] + "..." if len(content) > 100 else content
            
            results.append({
                "id": doc_id,
                "preview": preview,
                "metadata": doc_data["metadata"]
            })
        
        return results
    
    @mcp_instance.tool()
    def rag_search(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search the knowledge base for information (simple implementation)"""
        # Very simple search - check if query terms are in the content
        query_terms = query.lower().split()
        matches = []
        
        for doc_id, doc_data in in_memory_docs.items():
            content = doc_data["content"].lower()
            # Count how many query terms appear in the content
            score = sum(1 for term in query_terms if term in content) / len(query_terms) if query_terms else 0
            
            if score > 0:
                matches.append({
                    "document": doc_data["content"],
                    "metadata": doc_data["metadata"],
                    "score": score
                })
        
        # Sort by score and take top_k
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[:top_k] if matches else [{
            "document": "No relevant documents found",
            "metadata": {},
            "score": 0.0
        }]

    return mcp_instance