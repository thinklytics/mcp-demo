"""
Shared Data Models for MCP Server and Client

This module defines Pydantic models for data exchange between the MCP server and client.
"""

from pydantic import BaseModel, Field, model_validator
from typing import Dict, List, Optional, Union, Any
from enum import Enum


class DocumentMetadata(BaseModel):
    """Metadata for a document in the knowledge base"""
    source: Optional[str] = None
    topic: Optional[str] = None
    created_at: Optional[str] = None
    # Allow for additional fields
    extra_fields: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = {
        # Allow extra fields to be stored in the model
        "extra": "allow"
    }

    @model_validator(mode='before')
    @classmethod
    def extract_extra_fields(cls, data):
        """Extract unknown fields to extra_fields dictionary"""
        if not isinstance(data, dict):
            return data
            
        known_fields = {"source", "topic", "created_at", "extra_fields"}
        extra_fields = {}
        
        # Extract unknown fields to extra_fields
        for field_name, value in list(data.items()):
            if field_name not in known_fields and value is not None:
                extra_fields[field_name] = value
                
        # Update values with extracted extra fields
        if extra_fields:
            data["extra_fields"] = extra_fields
            
        return data


class Document(BaseModel):
    """A document in the knowledge base"""
    id: str
    preview: str
    metadata: Optional[DocumentMetadata] = Field(default_factory=DocumentMetadata)


class SearchResult(BaseModel):
    """Result item from a knowledge base search"""
    document: str
    metadata: Optional[DocumentMetadata] = Field(default_factory=DocumentMetadata)
    score: float = 0.0


class DocumentStatus(str, Enum):
    """Status of document operation"""
    SUCCESS = "success"
    ERROR = "error"
    DUPLICATE = "duplicate"


class AddDocumentRequest(BaseModel):
    """Request to add a document to the knowledge base"""
    content: str
    metadata: Optional[DocumentMetadata] = None
    
    @model_validator(mode='before')
    @classmethod
    def sanitize_metadata(cls, data):
        """Remove None values from metadata"""
        if isinstance(data, dict) and "metadata" in data and data["metadata"] is not None:
            if isinstance(data["metadata"], dict):
                # Remove None values from metadata
                data["metadata"] = {k: v for k, v in data["metadata"].items() if v is not None}
        return data


class AddDocumentResponse(BaseModel):
    """Response after adding a document to the knowledge base"""
    status: DocumentStatus
    id: Optional[str] = None
    message: Optional[str] = None


class SearchRequest(BaseModel):
    """Request to search the knowledge base"""
    query: str
    top_k: int = 3 