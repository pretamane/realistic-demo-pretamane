# Response models - Unified from all components
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime

class HealthResponse(BaseModel):
    """Health response model (from enhanced_app.py)"""
    status: str
    timestamp: str
    services: dict
    version: str
    document_stats: dict

class AnalyticsResponse(BaseModel):
    """Analytics response model (from enhanced_app.py)"""
    total_contacts: int
    total_documents: int
    document_types: Dict[str, int]
    processing_stats: Dict[str, Any]
    timestamp: str

class StatsResponse(BaseModel):
    """Stats response model (from enhanced_app.py)"""
    visitor_count: int
    timestamp: str
    enhanced_features: bool

class ProcessingResponse(BaseModel):
    """Processing response model (from enhanced_index.py)"""
    message: str
    processed_count: int
    enhanced_features: Dict[str, bool]

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    message: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + 'Z')

class SuccessResponse(BaseModel):
    """Success response model"""
    message: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + 'Z')
    data: Optional[Dict[str, Any]] = None
