# Contact models - Unified from all components
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class ContactForm(BaseModel):
    """Contact form model (from enhanced_app.py)"""
    name: str = Field(..., min_length=1, max_length=100, description="Contact person's name")
    email: str = Field(..., description="Contact person's email address")
    message: str = Field(..., min_length=1, max_length=1000, description="Contact message")
    company: Optional[str] = Field(None, max_length=100, description="Company name")
    service: Optional[str] = Field(None, max_length=100, description="Service required")
    budget: Optional[str] = Field(None, max_length=50, description="Budget range")
    source: Optional[str] = Field("website", max_length=50, description="Source of the contact")
    userAgent: Optional[str] = Field(None, max_length=500, description="User agent string")
    pageUrl: Optional[str] = Field(None, max_length=500, description="Page URL where form was submitted")

class ContactResponse(BaseModel):
    """Contact response model (from enhanced_app.py)"""
    message: str
    contactId: str
    timestamp: str
    visitor_count: int
    documents_count: int

class ContactRecord(BaseModel):
    """Contact record model for database operations"""
    id: str
    name: str
    email: str
    company: str
    service: str
    budget: str
    message: str
    timestamp: str
    status: str = "new"
    source: str
    userAgent: str
    pageUrl: str
    document_processing_enabled: bool = True
    search_capabilities: bool = True
    document_insights: Optional[dict] = None
    last_updated: Optional[str] = None

class ContactInsights(BaseModel):
    """Contact insights model (from enhanced_index.py)"""
    total_documents: int
    document_types: list
    total_size: int
    last_document_upload: Optional[str]
    processing_status: str
    content_analysis: dict
