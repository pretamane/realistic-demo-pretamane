# docker/api/app.py
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import boto3
import os
import time
import logging
from datetime import datetime
from botocore.exceptions import ClientError
import json
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for request/response validation
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

class ContactResponse(BaseModel):
    message: str
    contactId: str
    timestamp: str
    visitor_count: int

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    services: dict
    version: str

class StatsResponse(BaseModel):
    visitor_count: int
    timestamp: str

# Initialize FastAPI app
app = FastAPI(
    title="Contact Form API",
    description="A FastAPI application for handling contact form submissions",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware (replaces your manual CORS headers)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get('ALLOWED_ORIGIN', '*')],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key", "X-Amz-Security-Token"],
)

# Initialize AWS clients
region = os.environ.get('AWS_REGION', 'ap-southeast-1')
ses = boto3.client('ses', region_name=region)
dynamodb = boto3.resource('dynamodb', region_name=region)

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting Contact Form API...")
    logger.info(f"AWS Region: {region}")
    logger.info(f"Contacts Table: {os.environ.get('CONTACTS_TABLE', 'realistic-demo-pretamane-contact-submissions')}")
    logger.info(f"Visitors Table: {os.environ.get('VISITORS_TABLE', 'realistic-demo-pretamane-website-visitors')}")
    logger.info("Application startup complete!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("Shutting down Contact Form API...")

# Constants
MAX_MESSAGE_LENGTH = 1000
MAX_NAME_LENGTH = 100
MAX_EMAIL_LENGTH = 254

def validate_input(body):
    """Validate and sanitize input data with comprehensive checks"""
    if not body:
        raise ValueError("Request body is empty")
    
    required_fields = ['name', 'email', 'message']
    for field in required_fields:
        if not body.get(field):
            raise ValueError(f"Missing required field: {field}")
    
    # Validate email format
    email = body['email'].strip()
    if '@' not in email or '.' not in email or len(email) > MAX_EMAIL_LENGTH:
        raise ValueError("Invalid email format")
    
    # Validate name length
    if len(body['name'].strip()) > MAX_NAME_LENGTH:
        raise ValueError(f"Name must be less than {MAX_NAME_LENGTH} characters")
    
    # Validate message length
    if len(body['message'].strip()) > MAX_MESSAGE_LENGTH:
        raise ValueError(f"Message must be less than {MAX_MESSAGE_LENGTH} characters")
    
    # Sanitize inputs
    sanitized_body = {
        'name': body['name'].strip(),
        'email': email,
        'message': body['message'].strip(),
        'company': body.get('company', '').strip() or 'Not specified',
        'service': body.get('service', '').strip() or 'Not specified',
        'budget': body.get('budget', '').strip() or 'Not specified',
        'source': body.get('source', 'website').strip(),
        'userAgent': body.get('userAgent', 'Not provided').strip(),
        'pageUrl': body.get('pageUrl', 'Not provided').strip()
    }
    
    return sanitized_body

def get_dynamo_table(table_name):
    """Get DynamoDB table with error handling"""
    try:
        table = dynamodb.Table(table_name)
        table.load()
        return table
    except ClientError as e:
        logger.error(f"Error accessing DynamoDB table {table_name}: {str(e)}")
        raise Exception("Database configuration error")

def send_notification_email(name, email, company, service, budget, message, timestamp, source, user_agent, page_url):
    """Send notification email with error handling"""
    try:
        email_body = f"""
New Contact Form Submission

Name: {name}
Email: {email}
Company: {company}
Service Required: {service}
Budget Range: {budget}

Message:
{message}

Additional Information:
- Timestamp: {timestamp}
- Source: {source}
- Page URL: {page_url}
- User Agent: {user_agent}
"""

        response = ses.send_email(
            Source=os.environ.get('SES_FROM_EMAIL', 'thawzin252467@gmail.com'),
            Destination={
                'ToAddresses': [os.environ.get('SES_TO_EMAIL', 'thawzin252467@gmail.com')]
            },
            Message={
                'Subject': {'Data': f'New Contact: {name} - {service}'},
                'Body': {'Text': {'Data': email_body}}
            }
        )
        return response
    except ClientError as e:
        logger.error(f"Error sending email: {str(e)}")
        return None

@app.post("/contact", response_model=ContactResponse)
async def submit_contact(contact_form: ContactForm):
    """Submit a contact form with validation and processing"""
    try:
        # Convert Pydantic model to dict and validate
        body = contact_form.dict()
        sanitized_body = validate_input(body)
        
        # Get table references
        contacts_table = os.environ.get('CONTACTS_TABLE', 'ContactSubmissions')
        visitors_table = os.environ.get('VISITORS_TABLE', 'WebsiteVisitors')
        
        contact_table = get_dynamo_table(contacts_table)
        visitor_table = get_dynamo_table(visitors_table)
        
        # Generate timestamp
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # Create contact submission record with better ID generation
        unique_id = str(uuid.uuid4())[:8]
        contact_item = {
            'id': f"contact_{int(time.time())}_{unique_id}",
            'name': sanitized_body['name'],
            'email': sanitized_body['email'],
            'company': sanitized_body['company'],
            'service': sanitized_body['service'],
            'budget': sanitized_body['budget'],
            'message': sanitized_body['message'],
            'timestamp': timestamp,
            'status': 'new',
            'source': sanitized_body['source'],
            'userAgent': sanitized_body['userAgent'],
            'pageUrl': sanitized_body['pageUrl']
        }

        # Save contact submission to DynamoDB
        contact_table.put_item(Item=contact_item)
        logger.info(f"Saved contact submission with ID: {contact_item['id']}")

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

        # Send notification email
        email_response = send_notification_email(
            sanitized_body['name'], sanitized_body['email'], sanitized_body['company'],
            sanitized_body['service'], sanitized_body['budget'], sanitized_body['message'],
            timestamp, sanitized_body['source'], sanitized_body['userAgent'], 
            sanitized_body['pageUrl']
        )

        # Return success response
        response_data = ContactResponse(
            message='Contact form submitted successfully!',
            contactId=contact_item['id'],
            timestamp=timestamp,
            visitor_count=visitor_count
        )
        
        logger.info(f"Successfully processed contact submission: {contact_item['id']}")
        
        return response_data

    except ValueError as ve:
        logger.warning(f"Validation error: {str(ve)}")
        raise HTTPException(
            status_code=400,
            detail={
                'error': 'Validation Error',
                'message': str(ve)
            }
        )
    except ClientError as e:
        error_code = 500
        if 'ThrottlingException' in str(e):
            error_code = 429
            logger.error("DynamoDB throttling exception")
        else:
            logger.error(f"AWS service error: {str(e)}")
        
        raise HTTPException(
            status_code=error_code,
            detail={
                'error': 'Service Error',
                'message': 'Internal server error. Please try again later.'
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                'error': 'Internal Error',
                'message': 'An unexpected error occurred. Please try again later.'
            }
        )

@app.get("/health", response_model=HealthResponse)
def health_check():
    """Comprehensive health check endpoint"""
    try:
        # Check AWS services connectivity
        region = os.environ.get('AWS_REGION', 'ap-southeast-1')
        
        # Test DynamoDB connection
        contacts_table = os.environ.get('CONTACTS_TABLE', 'realistic-demo-pretamane-contact-submissions')
        table = dynamodb.Table(contacts_table)
        table.load()
        
        # Test SES connection
        ses.get_send_quota()
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow().isoformat() + 'Z',
            services={
                "dynamodb": "connected",
                "ses": "connected"
            },
            version="1.0.0"
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

@app.get("/")
def read_root():
    """Root endpoint with API information"""
    return {
        "message": "Contact Form API is running!",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "contact_endpoint": "/contact"
    }

@app.get("/stats", response_model=StatsResponse)
def get_stats():
    """Get visitor statistics"""
    try:
        visitors_table = os.environ.get('VISITORS_TABLE', 'realistic-demo-pretamane-website-visitors')
        visitor_table = get_dynamo_table(visitors_table)
        
        # Get visitor count
        try:
            response = visitor_table.get_item(Key={'id': 'visitor_count'})
            visitor_count = response.get('Item', {}).get('count', 0)
        except ClientError:
            visitor_count = 0
        
        return StatsResponse(
            visitor_count=visitor_count,
            timestamp=datetime.utcnow().isoformat() + 'Z'
        )
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