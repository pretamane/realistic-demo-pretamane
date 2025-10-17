# Document models - Unified from all components
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class DocumentUpload(BaseModel):
    """Document upload model (from enhanced_app.py)"""
    contact_id: str = Field(..., description="Associated contact ID")
    document_type: str = Field(..., description="Type of document (proposal, contract, etc.)")
    description: Optional[str] = Field(None, description="Document description")
    tags: Optional[List[str]] = Field(default=[], description="Document tags")

class DocumentResponse(BaseModel):
    """Document response model (from enhanced_app.py)"""
    document_id: str
    filename: str
    size: int
    content_type: str
    upload_timestamp: str
    processing_status: str
    contact_id: str
    s3_path: str

class SearchRequest(BaseModel):
    """Search request model (from enhanced_app.py)"""
    query: str = Field(..., min_length=1, description="Search query")
    filters: Optional[Dict[str, Any]] = Field(default={}, description="Search filters")
    limit: Optional[int] = Field(default=10, ge=1, le=100, description="Number of results")

class SearchResponse(BaseModel):
    """Search response model (from enhanced_app.py)"""
    results: List[Dict[str, Any]]
    total_count: int
    query: str
    processing_time: float

class DocumentRecord(BaseModel):
    """Document record model for database operations"""
    id: str
    contact_id: str
    filename: str
    size: int
    content_type: str
    document_type: str
    description: str
    tags: List[str]
    upload_timestamp: str
    processing_status: str
    s3_bucket: str
    s3_key: str
    efs_path: str
    file_hash: str
    processing_metadata: Optional[Dict[str, Any]] = None
    processing_timestamp: Optional[str] = None
    complexity_score: Optional[float] = None
    indexed_timestamp: Optional[str] = None

class DocumentMetadata(BaseModel):
    """Document metadata model (from enhanced_index.py)"""
    word_count: int
    character_count: int
    line_count: int
    file_extension: str
    has_email: bool
    has_phone: bool
    has_url: bool
    language_detected: str
    keywords: List[str]
    entities: Dict[str, List[str]]

class ProcessingInfo(BaseModel):
    """Processing info model (from enhanced_index.py)"""
    status: str
    timestamp: str
    complexity_score: float

class S3Metadata(BaseModel):
    """S3 metadata model (from enhanced_index.py)"""
    bucket: str
    key: str
    size: int
    content_type: str
    last_modified: str

class DocumentIndex(BaseModel):
    """Document index model for OpenSearch"""
    id: str
    contact_id: str
    filename: str
    document_type: str
    content: str
    text_content: str
    metadata: DocumentMetadata
    s3_metadata: S3Metadata
    processing_info: ProcessingInfo
    timestamp: str
    upload_timestamp: str
    processing_timestamp: str
