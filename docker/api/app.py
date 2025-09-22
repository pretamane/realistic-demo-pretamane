# docker/api/app.py
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import boto3
import os
import time
import logging
from datetime import datetime
from botocore.exceptions import ClientError
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Contact Form API")

# Add CORS middleware (replaces your manual CORS headers)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get('ALLOWED_ORIGIN', '*')],
    allow_credentials=True,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key", "X-Amz-Security-Token"],
)

# Initialize AWS clients
region = os.environ.get('AWS_REGION', 'ap-southeast-1')
ses = boto3.client('ses', region_name=region)
dynamodb = boto3.resource('dynamodb', region_name=region)

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

@app.post("/contact")
async def submit_contact(request: Request):
    """FastAPI version of your Lambda handler"""
    try:
        # Get request body
        body = await request.json()
        
        # Validate and sanitize input
        sanitized_body = validate_input(body)
        
        # Get table references
        contacts_table = os.environ.get('CONTACTS_TABLE', 'ContactSubmissions')
        visitors_table = os.environ.get('VISITORS_TABLE', 'WebsiteVisitors')
        
        contact_table = get_dynamo_table(contacts_table)
        visitor_table = get_dynamo_table(visitors_table)
        
        # Generate timestamp
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # Create contact submission record
        contact_item = {
            'id': f"contact_{int(time.time())}_{hash(str(time.time())) % 1000000}",
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
        response_data = {
            'message': 'Contact form submitted successfully!',
            'contactId': contact_item['id'],
            'timestamp': timestamp,
            'visitor_count': visitor_count
        }
        
        logger.info(f"Successfully processed contact submission: {contact_item['id']}")
        
        return JSONResponse(
            status_code=200,
            content=response_data
        )

    except ValueError as ve:
        logger.warning(f"Validation error: {str(ve)}")
        return JSONResponse(
            status_code=400,
            content={
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
        
        return JSONResponse(
            status_code=error_code,
            content={
                'error': 'Service Error',
                'message': 'Internal server error. Please try again later.'
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                'error': 'Internal Error',
                'message': 'An unexpected error occurred. Please try again later.'
            }
        )

@app.get("/health")
def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy"}

@app.get("/")
def read_root():
    return {"message": "Contact Form API is running!"}