# Unified Enhanced FastAPI Application - Document Management & Contact Intelligence System
# Consolidates functionality from enhanced_app.py, lambda_function.py, and enhanced_index.py
from fastapi import FastAPI, Request, Response, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
from datetime import datetime
from typing import Optional

# Import unified components
from shared.aws_clients import AWSClientManager
from components.contact_processor import ContactProcessor
from components.document_processor import DocumentProcessor
from components.background_tasks import BackgroundTaskProcessor

# Import unified models
from models.contact import ContactForm, ContactResponse
from models.document import DocumentUpload, DocumentResponse, SearchRequest, SearchResponse
from models.response import HealthResponse, AnalyticsResponse, StatsResponse, ErrorResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Unified Enterprise Document Management & Contact Intelligence API",
    description="Advanced document processing system with contact intelligence and real-time search capabilities",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get('ALLOWED_ORIGIN', '*')],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key", "X-Amz-Security-Token"],
)

# Global components
aws_clients = None
contact_processor = None
document_processor = None
background_processor = None

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    global aws_clients, contact_processor, document_processor, background_processor
    
    logger.info("Starting Unified Document Management & Contact Intelligence API...")
    logger.info(f"AWS Region: {os.environ.get('AWS_REGION', 'ap-southeast-1')}")
    
    # Initialize AWS clients
    aws_clients = AWSClientManager()
    
    # Initialize components
    contact_processor = ContactProcessor(aws_clients)
    document_processor = DocumentProcessor(aws_clients)
    background_processor = BackgroundTaskProcessor(aws_clients, document_processor)
    
    # Start background processor
    await background_processor.start()
    
    logger.info("Application startup complete!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    global background_processor
    
    logger.info("Shutting down Unified Document Management API...")
    
    if background_processor:
        await background_processor.stop()
    
    logger.info("Application shutdown complete!")

# Contact Form Endpoints
@app.post("/contact", response_model=ContactResponse)
async def submit_contact(contact_form: ContactForm):
    """Submit contact form with document processing capabilities"""
    try:
        return await contact_processor.process_enhanced_contact(contact_form)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Unexpected error in contact submission: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                'error': 'Internal Error',
                'message': 'An unexpected error occurred. Please try again later.'
            }
        )

@app.post("/contact/basic", response_model=ContactResponse)
async def submit_basic_contact(contact_form: ContactForm):
    """Submit basic contact form (from lambda_function.py)"""
    try:
        return await contact_processor.process_contact(contact_form)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Unexpected error in basic contact submission: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                'error': 'Internal Error',
                'message': 'An unexpected error occurred. Please try again later.'
            }
        )

# Document Endpoints
@app.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    contact_id: str = Form(...),
    document_type: str = Form(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form("")
):
    """Upload and process documents with contact association"""
    try:
        return await document_processor.upload_document(file, contact_id, document_type, description, tags)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                'error': 'Upload Error',
                'message': 'Failed to upload document. Please try again.'
            }
        )

@app.post("/documents/search", response_model=SearchResponse)
async def search_documents(search_request: SearchRequest):
    """Search documents with advanced filtering"""
    try:
        return await document_processor.search_documents(search_request)
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                'error': 'Search Error',
                'message': 'Failed to search documents. Please try again.'
            }
        )

@app.get("/contacts/{contact_id}/documents")
async def get_contact_documents(contact_id: str):
    """Get all documents for a specific contact"""
    try:
        return await contact_processor.get_contact_documents(contact_id)
    except Exception as e:
        logger.error(f"Error getting contact documents: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                'error': 'Retrieval Error',
                'message': 'Failed to retrieve contact documents.'
            }
        )

# Analytics Endpoints
@app.get("/analytics/insights", response_model=AnalyticsResponse)
async def get_analytics():
    """Get system analytics and insights"""
    try:
        analytics_data = await document_processor.get_analytics()
        return AnalyticsResponse(**analytics_data)
    except Exception as e:
        logger.error(f"Error getting analytics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                'error': 'Analytics Error',
                'message': 'Failed to retrieve analytics data.'
            }
        )

@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get visitor statistics (legacy endpoint)"""
    try:
        stats_data = await contact_processor.get_stats()
        return StatsResponse(**stats_data)
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Unable to retrieve statistics")

# Health Check Endpoint
@app.get("/health", response_model=HealthResponse)
def health_check():
    """Comprehensive health check with document processing status"""
    try:
        # Check AWS services connectivity
        region = os.environ.get('AWS_REGION', 'ap-southeast-1')
        
        # Test AWS connectivity
        services = aws_clients.test_aws_connectivity()
        
        # Get document statistics
        documents_table = os.environ.get('DOCUMENTS_TABLE', 'realistic-demo-pretamane-documents')
        doc_table = aws_clients.get_dynamo_table(documents_table)
        doc_response = doc_table.scan(Select='COUNT')
        
        # Get background processor status
        background_status = background_processor.get_status() if background_processor else {'running': False}
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow().isoformat() + 'Z',
            services=services,
            version="3.0.0",
            document_stats={
                "total_documents": doc_response['Count'],
                "upload_directory": "/mnt/efs/uploads",
                "processed_directory": "/mnt/efs/processed",
                "max_file_size_mb": 50,
                "background_processor": background_status
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + 'Z'
            }
        )

# Root endpoint
@app.get("/")
def read_root():
    """Root endpoint with unified API information"""
    return {
        "message": "Unified Enterprise Document Management & Contact Intelligence API is running!",
        "version": "3.0.0",
        "features": [
            "Unified contact form processing",
            "Advanced document upload and processing",
            "Real-time search capabilities",
            "Contact intelligence analytics",
            "Multi-format document support",
            "S3 integration with EFS mounting",
            "OpenSearch indexing",
            "Background task processing",
            "Enhanced monitoring and health checks"
        ],
        "endpoints": {
            "contact": "/contact",
            "contact_basic": "/contact/basic",
            "document_upload": "/documents/upload",
            "document_search": "/documents/search",
            "contact_documents": "/contacts/{contact_id}/documents",
            "analytics": "/analytics/insights",
            "stats": "/stats",
            "health": "/health",
            "docs": "/docs"
        },
        "architecture": {
            "type": "unified",
            "components": [
                "ContactProcessor",
                "DocumentProcessor", 
                "BackgroundTaskProcessor",
                "AWSClientManager",
                "EmailService",
                "DatabaseService",
                "OpenSearchService"
            ],
            "lambda_functions_consolidated": True
        }
    }

# CORS preflight endpoint
@app.options("/contact")
async def contact_options():
    """Handle preflight OPTIONS request for CORS"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": os.environ.get('ALLOWED_ORIGIN', '*'),
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, X-Amz-Date, Authorization, X-Api-Key, X-Amz-Security-Token",
            "Access-Control-Allow-Credentials": "true"
        }
    )

# Background processing endpoint
@app.post("/admin/process-s3-event")
async def process_s3_event_background(
    background_tasks: BackgroundTasks,
    bucket: str,
    key: str
):
    """Process S3 event in background (admin endpoint)"""
    try:
        background_tasks.add_task(document_processor.process_s3_document, bucket, key)
        return {"message": "S3 event processing queued", "bucket": bucket, "key": key}
    except Exception as e:
        logger.error(f"Error queuing S3 event processing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Background processor status endpoint
@app.get("/admin/background-status")
async def get_background_status():
    """Get background processor status"""
    try:
        if background_processor:
            return background_processor.get_status()
        else:
            return {"running": False, "error": "Background processor not initialized"}
    except Exception as e:
        logger.error(f"Error getting background status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
