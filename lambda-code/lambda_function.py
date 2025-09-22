import json
import boto3
import os
import time
import logging
from datetime import datetime
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients with explicit configuration
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
        # Verify table exists by describing it
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
        # Don't fail the entire process if email fails
        return None

def lambda_handler(event, context):
    """Main Lambda handler function"""
    # Log the incoming event (redact sensitive info in production)
    logger.info(f"Received event: {json.dumps({k: v for k, v in event.items() if k != 'body'})}")
    
    # Set CORS headers
    cors_headers = {
        'Access-Control-Allow-Origin': os.environ.get('ALLOWED_ORIGIN', '*'),
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Credentials': 'true'
    }
    
    # Handle preflight OPTIONS request
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({'message': 'OK'})
        }
    
    try:
        # Check if body exists in the event
        if 'body' not in event:
            logger.warning("Request missing body")
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'Bad Request',
                    'message': 'Request body is missing'
                })
            }
        
        # Parse and validate input
        try:
            body = json.loads(event['body'])
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in request body")
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'Invalid Request',
                    'message': 'Request body contains invalid JSON'
                })
            }
        
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
            'id': f"contact_{int(time.time())}_{context.aws_request_id[-8:]}",
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

        # Update visitor counter with error handling
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
            visitor_count = 0  # Default value if update fails

        # Send notification email
        email_response = send_notification_email(
            sanitized_body['name'], sanitized_body['email'], sanitized_body['company'],
            sanitized_body['service'], sanitized_body['budget'], sanitized_body['message'],
            timestamp, sanitized_body['source'], sanitized_body['userAgent'], 
            sanitized_body['pageUrl']
        )

        # Prepare success response
        response_data = {
            'message': 'Contact form submitted successfully!',
            'contactId': contact_item['id'],
            'timestamp': timestamp,
            'visitor_count': visitor_count
        }
        
        logger.info(f"Successfully processed contact submission: {contact_item['id']}")
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps(response_data)
        }

    except ValueError as ve:
        logger.warning(f"Validation error: {str(ve)}")
        return {
            'statusCode': 400,
            'headers': cors_headers,
            'body': json.dumps({
                'error': 'Validation Error',
                'message': str(ve)
            })
        }
    except ClientError as e:
        error_code = 500
        if 'ThrottlingException' in str(e):
            error_code = 429
            logger.error("DynamoDB throttling exception")
        else:
            logger.error(f"AWS service error: {str(e)}")
        
        return {
            'statusCode': error_code,
            'headers': cors_headers,
            'body': json.dumps({
                'error': 'Service Error',
                'message': 'Internal server error. Please try again later.'
            })
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({
                'error': 'Internal Error',
                'message': 'An unexpected error occurred. Please try again later.'
            })
        }