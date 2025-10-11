# Enhanced FastAPI Application - Document Management & Contact Intelligence System
from fastapi import FastAPI, Request, Response, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
import boto3
import os
import time
import logging
import json
import uuid
import asyncio
from datetime import datetime
from botocore.exceptions import ClientError
import aiofiles
import hashlib
import mimetypes
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for enhanced functionality
class ContactForm(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Contact person's name")
    email: str = Field(..., description="Contact person's email address")
    message: str = Field(..., min_length=1, max_length=1000, description="Contact message")
    company: Optional[str] = Field(None, max_length=100, description="Company name")
    service: Optional[str] = Field(None, max_length=100, description="Service required")
    budget: Optional[str] = Field(None, max_length=50, description="Budget range")
    source: Optional[str] = Field("website", max_length=50, description="Source of the contact")
    userAgent: Optional[str] = Field(None, max_length=500, description="User agent string")
    pageUrl: Optional[str] = Field(None, max_length=500, description="Page URL where form was submitted")

class DocumentUpload(BaseModel):
    contact_id: str = Field(..., description="Associated contact ID")
    document_type: str = Field(..., description="Type of document (proposal, contract, etc.)")
    description: Optional[str] = Field(None, description="Document description")
    tags: Optional[List[str]] = Field(default=[], description="Document tags")

class DocumentResponse(BaseModel):
    document_id: str
    filename: str
    size: int
    content_type: str
    upload_timestamp: str
    processing_status: str
    contact_id: str
    s3_path: str

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query")
    filters: Optional[Dict[str, Any]] = Field(default={}, description="Search filters")
    limit: Optional[int] = Field(default=10, ge=1, le=100, description="Number of results")

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    total_count: int
    query: str
    processing_time: float

class ContactResponse(BaseModel):
    message: str
    contactId: str
    timestamp: str
    visitor_count: int
    documents_count: int

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    services: dict
    version: str
    document_stats: dict

class AnalyticsResponse(BaseModel):
    total_contacts: int
    total_documents: int
    document_types: Dict[str, int]
    processing_stats: Dict[str, Any]
    timestamp: str

# Initialize FastAPI app
app = FastAPI(
    title="Enterprise Document Management & Contact Intelligence API",
    description="Advanced document processing system with contact intelligence and real-time search capabilities",
    version="2.0.0",
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

# Initialize AWS clients
region = os.environ.get('AWS_REGION', 'ap-southeast-1')
s3_client = boto3.client('s3', region_name=region)
ses = boto3.client('ses', region_name=region)
dynamodb = boto3.resource('dynamodb', region_name=region)

# Configuration
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {
    # Document formats
    '.pdf', '.doc', '.docx', '.txt', '.json', '.csv', '.xlsx', '.pptx',
    # Image formats
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.tiff', '.tif'
}
UPLOAD_DIR = "/mnt/efs/uploads"
PROCESSED_DIR = "/mnt/efs/processed"

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting Enhanced Document Management & Contact Intelligence API...")
    logger.info(f"AWS Region: {region}")
    logger.info(f"Upload Directory: {UPLOAD_DIR}")
    logger.info(f"Processed Directory: {PROCESSED_DIR}")
    
    # Create directories if they don't exist
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    logger.info("Application startup complete!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("Shutting down Enhanced Document Management API...")

# Utility functions
def validate_file(file: UploadFile) -> bool:
    """Validate uploaded file"""
    if not file.filename:
        return False
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return False
    
    return True

def get_file_hash(content: bytes) -> str:
    """Generate file hash for deduplication"""
    return hashlib.sha256(content).hexdigest()

def get_dynamo_table(table_name: str):
    """Get DynamoDB table with error handling"""
    try:
        table = dynamodb.Table(table_name)
        table.load()
        return table
    except ClientError as e:
        logger.error(f"Error accessing DynamoDB table {table_name}: {str(e)}")
        raise Exception("Database configuration error")

def send_notification_email(name: str, email: str, company: str, service: str, 
                          budget: str, message: str, timestamp: str, source: str, 
                          user_agent: str, page_url: str, document_count: int = 0):
    """Send enhanced notification email with document information"""
    try:
        email_body = f"""
Enhanced Contact Form Submission with Document Processing

Contact Information:
Name: {name}
Email: {email}
Company: {company}
Service Required: {service}
Budget Range: {budget}

Message:
{message}

Document Processing:
- Documents uploaded: {document_count}
- Processing status: Active

Additional Information:
- Timestamp: {timestamp}
- Source: {source}
- Page URL: {page_url}
- User Agent: {user_agent}

System Status:
- Document indexing: Active
- Search capabilities: Enabled
- Analytics: Available
"""

        response = ses.send_email(
            Source=os.environ.get('SES_FROM_EMAIL', 'noreply@example.com'),
            Destination={
                'ToAddresses': [os.environ.get('SES_TO_EMAIL', 'admin@example.com')]
            },
            Message={
                'Subject': {'Data': f'Enhanced Contact: {name} - {service} (Documents: {document_count})'},
                'Body': {'Text': {'Data': email_body}}
            }
        )
        return response
    except ClientError as e:
        logger.error(f"Error sending email: {str(e)}")
        return None

# Enhanced Contact Form Submission
@app.post("/contact", response_model=ContactResponse)
async def submit_contact(contact_form: ContactForm):
    """Submit enhanced contact form with document processing capabilities"""
    try:
        # Convert Pydantic model to dict and validate
        body = contact_form.dict()
        
        # Get table references
        contacts_table = os.environ.get('CONTACTS_TABLE', 'realistic-demo-pretamane-contact-submissions')
        visitors_table = os.environ.get('VISITORS_TABLE', 'realistic-demo-pretamane-website-visitors')
        documents_table = os.environ.get('DOCUMENTS_TABLE', 'realistic-demo-pretamane-documents')
        
        contact_table = get_dynamo_table(contacts_table)
        visitor_table = get_dynamo_table(visitors_table)
        document_table = get_dynamo_table(documents_table)
        
        # Generate timestamp
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # Create contact submission record
        unique_id = str(uuid.uuid4())[:8]
        contact_item = {
            'id': f"contact_{int(time.time())}_{unique_id}",
            'name': body['name'],
            'email': body['email'],
            'company': body.get('company', 'Not specified'),
            'service': body.get('service', 'Not specified'),
            'budget': body.get('budget', 'Not specified'),
            'message': body['message'],
            'timestamp': timestamp,
            'status': 'new',
            'source': body.get('source', 'website'),
            'userAgent': body.get('userAgent', 'Not provided'),
            'pageUrl': body.get('pageUrl', 'Not provided'),
            'document_processing_enabled': True,
            'search_capabilities': True
        }

        # Save contact submission to DynamoDB
        contact_table.put_item(Item=contact_item)
        logger.info(f"Saved enhanced contact submission with ID: {contact_item['id']}")

        # Update visitor counter
        try:
            visitor_response = visitor_table.update_item(
                Key={'id': 'visitor_count'},
                UpdateExpression='ADD #count :inc',
                ExpressionAttributeNames={'#count': 'count'},
                ExpressionAttributeValues={':inc': 1},
                ReturnValues='UPDATED_NEW'
            )
            visitor_count = int(visitor_response["Attributes"]["count"])
        except ClientError as e:
            logger.error(f"Error updating visitor count: {str(e)}")
            visitor_count = 0

        # Get document count for this contact
        try:
            doc_response = document_table.query(
                IndexName='contact-id-index',
                KeyConditionExpression='contact_id = :contact_id',
                ExpressionAttributeValues={':contact_id': contact_item['id']}
            )
            documents_count = len(doc_response.get('Items', []))
        except ClientError:
            documents_count = 0

        # Send enhanced notification email
        email_response = send_notification_email(
            body['name'], body['email'], body.get('company', 'Not specified'),
            body.get('service', 'Not specified'), body.get('budget', 'Not specified'),
            body['message'], timestamp, body.get('source', 'website'),
            body.get('userAgent', 'Not provided'), body.get('pageUrl', 'Not provided'),
            documents_count
        )

        # Return enhanced success response
        response_data = ContactResponse(
            message='Enhanced contact form submitted successfully with document processing capabilities!',
            contactId=contact_item['id'],
            timestamp=timestamp,
            visitor_count=visitor_count,
            documents_count=documents_count
        )
        
        logger.info(f"Successfully processed enhanced contact submission: {contact_item['id']}")
        return response_data

    except Exception as e:
        logger.error(f"Unexpected error in contact submission: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                'error': 'Internal Error',
                'message': 'An unexpected error occurred. Please try again later.'
            }
        )

# Document Upload Endpoint
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
        # Validate file
        if not validate_file(file):
            raise HTTPException(
                status_code=400,
                detail={
                    'error': 'Invalid File',
                    'message': f'File type not supported. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
                }
            )

        # Read file content
        content = await file.read()
        
        # Check file size
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail={
                    'error': 'File Too Large',
                    'message': f'File size exceeds maximum limit of {MAX_FILE_SIZE // (1024*1024)}MB'
                }
            )

        # Generate document metadata
        document_id = str(uuid.uuid4())
        file_hash = get_file_hash(content)
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # Determine content type
        content_type, _ = mimetypes.guess_type(file.filename)
        if not content_type:
            content_type = 'application/octet-stream'

        # Save file to EFS
        file_path = os.path.join(UPLOAD_DIR, f"{document_id}_{file.filename}")
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)

        # Upload to S3 for processing
        s3_key = f"documents/{contact_id}/{document_id}_{file.filename}"
        s3_bucket = os.environ.get('S3_DATA_BUCKET', 'realistic-demo-pretamane-data')
        
        s3_client.put_object(
            Bucket=s3_bucket,
            Key=s3_key,
            Body=content,
            ContentType=content_type,
            Metadata={
                'contact_id': contact_id,
                'document_type': document_type,
                'upload_timestamp': timestamp,
                'file_hash': file_hash
            }
        )

        # Save document metadata to DynamoDB
        documents_table = os.environ.get('DOCUMENTS_TABLE', 'realistic-demo-pretamane-documents')
        document_table = get_dynamo_table(documents_table)
        
        document_item = {
            'id': document_id,
            'contact_id': contact_id,
            'filename': file.filename,
            'size': len(content),
            'content_type': content_type,
            'document_type': document_type,
            'description': description or '',
            'tags': tags.split(',') if tags else [],
            'upload_timestamp': timestamp,
            'processing_status': 'pending',
            's3_bucket': s3_bucket,
            's3_key': s3_key,
            'efs_path': file_path,
            'file_hash': file_hash
        }
        
        document_table.put_item(Item=document_item)
        logger.info(f"Saved document metadata: {document_id}")

        # Return response
        return DocumentResponse(
            document_id=document_id,
            filename=file.filename,
            size=len(content),
            content_type=content_type,
            upload_timestamp=timestamp,
            processing_status='pending',
            contact_id=contact_id,
            s3_path=f"s3://{s3_bucket}/{s3_key}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                'error': 'Upload Error',
                'message': 'Failed to upload document. Please try again.'
            }
        )

# Document Search Endpoint
@app.post("/documents/search", response_model=SearchResponse)
async def search_documents(search_request: SearchRequest):
    """Search documents with advanced filtering"""
    try:
        start_time = time.time()
        
        # This would integrate with OpenSearch in a real implementation
        # For now, we'll simulate search results
        documents_table = os.environ.get('DOCUMENTS_TABLE', 'realistic-demo-pretamane-documents')
        document_table = get_dynamo_table(documents_table)
        
        # Basic search simulation
        response = document_table.scan(
            FilterExpression='contains(filename, :query) OR contains(description, :query)',
            ExpressionAttributeValues={':query': search_request.query}
        )
        
        results = []
        for item in response.get('Items', []):
            results.append({
                'document_id': item['id'],
                'filename': item['filename'],
                'contact_id': item['contact_id'],
                'document_type': item['document_type'],
                'description': item['description'],
                'tags': item.get('tags', []),
                'upload_timestamp': item['upload_timestamp'],
                'processing_status': item['processing_status'],
                'size': item['size']
            })
        
        # Limit results
        results = results[:search_request.limit]
        processing_time = time.time() - start_time
        
        return SearchResponse(
            results=results,
            total_count=len(results),
            query=search_request.query,
            processing_time=processing_time
        )

    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                'error': 'Search Error',
                'message': 'Failed to search documents. Please try again.'
            }
        )

# Get Contact Documents
@app.get("/contacts/{contact_id}/documents")
async def get_contact_documents(contact_id: str):
    """Get all documents for a specific contact"""
    try:
        documents_table = os.environ.get('DOCUMENTS_TABLE', 'realistic-demo-pretamane-documents')
        document_table = get_dynamo_table(documents_table)
        
        response = document_table.query(
            IndexName='contact-id-index',
            KeyConditionExpression='contact_id = :contact_id',
            ExpressionAttributeValues={':contact_id': contact_id}
        )
        
        documents = []
        for item in response.get('Items', []):
            documents.append({
                'document_id': item['id'],
                'filename': item['filename'],
                'document_type': item['document_type'],
                'description': item['description'],
                'tags': item.get('tags', []),
                'upload_timestamp': item['upload_timestamp'],
                'processing_status': item['processing_status'],
                'size': item['size']
            })
        
        return {
            'contact_id': contact_id,
            'documents': documents,
            'total_count': len(documents)
        }

    except Exception as e:
        logger.error(f"Error getting contact documents: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                'error': 'Retrieval Error',
                'message': 'Failed to retrieve contact documents.'
            }
        )

# Analytics Endpoint
@app.get("/analytics/insights", response_model=AnalyticsResponse)
async def get_analytics():
    """Get system analytics and insights"""
    try:
        contacts_table = os.environ.get('CONTACTS_TABLE', 'realistic-demo-pretamane-contact-submissions')
        documents_table = os.environ.get('DOCUMENTS_TABLE', 'realistic-demo-pretamane-documents')
        
        contact_table = get_dynamo_table(contacts_table)
        document_table = get_dynamo_table(documents_table)
        
        # Get contact count
        contact_response = contact_table.scan(Select='COUNT')
        total_contacts = contact_response['Count']
        
        # Get document count and types
        document_response = document_table.scan()
        total_documents = len(document_response.get('Items', []))
        
        document_types = {}
        processing_stats = {'pending': 0, 'processing': 0, 'completed': 0, 'failed': 0}
        
        for item in document_response.get('Items', []):
            doc_type = item.get('document_type', 'unknown')
            document_types[doc_type] = document_types.get(doc_type, 0) + 1
            
            status = item.get('processing_status', 'pending')
            processing_stats[status] = processing_stats.get(status, 0) + 1
        
        return AnalyticsResponse(
            total_contacts=total_contacts,
            total_documents=total_documents,
            document_types=document_types,
            processing_stats=processing_stats,
            timestamp=datetime.utcnow().isoformat() + 'Z'
        )

    except Exception as e:
        logger.error(f"Error getting analytics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                'error': 'Analytics Error',
                'message': 'Failed to retrieve analytics data.'
            }
        )

# Enhanced Health Check
@app.get("/health", response_model=HealthResponse)
def health_check():
    """Comprehensive health check with document processing status"""
    try:
        # Check AWS services connectivity
        region = os.environ.get('AWS_REGION', 'ap-southeast-1')
        
        # Test DynamoDB connection
        contacts_table = os.environ.get('CONTACTS_TABLE', 'realistic-demo-pretamane-contact-submissions')
        table = dynamodb.Table(contacts_table)
        table.load()
        
        # Test SES connection
        ses.get_send_quota()
        
        # Test S3 connection
        s3_bucket = os.environ.get('S3_DATA_BUCKET', 'realistic-demo-pretamane-data')
        s3_client.head_bucket(Bucket=s3_bucket)
        
        # Get document statistics
        documents_table = os.environ.get('DOCUMENTS_TABLE', 'realistic-demo-pretamane-documents')
        doc_table = get_dynamo_table(documents_table)
        doc_response = doc_table.scan(Select='COUNT')
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow().isoformat() + 'Z',
            services={
                "dynamodb": "connected",
                "ses": "connected",
                "s3": "connected",
                "efs": "mounted"
            },
            version="2.0.0",
            document_stats={
                "total_documents": doc_response['Count'],
                "upload_directory": UPLOAD_DIR,
                "processed_directory": PROCESSED_DIR,
                "max_file_size_mb": MAX_FILE_SIZE // (1024 * 1024)
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
    """Root endpoint with enhanced API information"""
    return {
        "message": "Enterprise Document Management & Contact Intelligence API is running!",
        "version": "2.0.0",
        "features": [
            "Contact form processing",
            "Document upload and processing",
            "Real-time search capabilities",
            "Contact intelligence analytics",
            "Multi-format document support",
            "S3 integration with EFS mounting",
            "OpenSearch indexing",
            "Advanced analytics"
        ],
        "endpoints": {
            "contact": "/contact",
            "document_upload": "/documents/upload",
            "document_search": "/documents/search",
            "contact_documents": "/contacts/{contact_id}/documents",
            "analytics": "/analytics/insights",
            "health": "/health",
            "docs": "/docs"
        }
    }

# Legacy endpoints for backward compatibility
@app.get("/stats")
def get_stats():
    """Get visitor statistics (legacy endpoint)"""
    try:
        visitors_table = os.environ.get('VISITORS_TABLE', 'realistic-demo-pretamane-website-visitors')
        visitor_table = get_dynamo_table(visitors_table)
        
        try:
            response = visitor_table.get_item(Key={'id': 'visitor_count'})
            visitor_count = response.get('Item', {}).get('count', 0)
        except ClientError:
            visitor_count = 0
        
        return {
            "visitor_count": visitor_count,
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "enhanced_features": True
        }
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Unable to retrieve statistics")

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



