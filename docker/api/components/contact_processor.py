# Contact Processor Component - Extracted from lambda_function.py
import os
import time
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from shared.aws_clients import AWSClientManager
from shared.email_service import EmailService
from shared.database_service import DatabaseService
from utils.validation import ValidationService
from models.contact import ContactForm, ContactResponse, ContactRecord

logger = logging.getLogger(__name__)

class ContactProcessor:
    """Contact processing component extracted from lambda_function.py"""
    
    def __init__(self, aws_clients: AWSClientManager):
        self.aws_clients = aws_clients
        self.email_service = EmailService(aws_clients.ses_client)
        self.database_service = DatabaseService(aws_clients)
        self.validation_service = ValidationService()
    
    async def process_contact(self, contact_form: ContactForm) -> ContactResponse:
        """Process contact form submission (from lambda_function.py)"""
        try:
            # Convert Pydantic model to dict and validate
            body = contact_form.dict()
            
            # Validate and sanitize input
            sanitized_body = self.validation_service.validate_contact_input(body)
            
            # Generate timestamp
            timestamp = datetime.utcnow().isoformat() + 'Z'
            
            # Create contact submission record
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
                'pageUrl': sanitized_body['pageUrl'],
                'document_processing_enabled': True,
                'search_capabilities': True
            }
            
            # Save contact submission to DynamoDB
            contact_id = self.database_service.create_contact_record(contact_item)
            
            # Update visitor counter
            visitor_count = self.database_service.update_visitor_count()
            
            # Get document count for this contact
            documents_count = len(self.database_service.get_contact_documents(contact_id))
            
            # Send notification email
            email_response = self.email_service.send_contact_notification(
                sanitized_body['name'], sanitized_body['email'], sanitized_body['company'],
                sanitized_body['service'], sanitized_body['budget'], sanitized_body['message'],
                timestamp, sanitized_body['source'], sanitized_body['userAgent'], 
                sanitized_body['pageUrl'], documents_count
            )
            
            # Return success response
            response_data = ContactResponse(
                message='Contact form submitted successfully!',
                contactId=contact_id,
                timestamp=timestamp,
                visitor_count=visitor_count,
                documents_count=documents_count
            )
            
            logger.info(f"Successfully processed contact submission: {contact_id}")
            return response_data
            
        except ValueError as ve:
            logger.warning(f"Validation error: {str(ve)}")
            raise ValueError(f"Validation Error: {str(ve)}")
        except Exception as e:
            logger.error(f"Unexpected error in contact submission: {str(e)}")
            raise Exception(f"Internal Error: An unexpected error occurred. Please try again later.")
    
    async def process_enhanced_contact(self, contact_form: ContactForm) -> ContactResponse:
        """Process enhanced contact form with document capabilities (from enhanced_app.py)"""
        try:
            # Convert Pydantic model to dict and validate
            body = contact_form.dict()
            
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
            contact_id = self.database_service.create_contact_record(contact_item)
            
            # Update visitor counter
            visitor_count = self.database_service.update_visitor_count()
            
            # Get document count for this contact
            documents_count = len(self.database_service.get_contact_documents(contact_id))
            
            # Send enhanced notification email
            email_response = self.email_service.send_enhanced_contact_notification(
                body['name'], body['email'], body.get('company', 'Not specified'),
                body.get('service', 'Not specified'), body.get('budget', 'Not specified'),
                body['message'], timestamp, body.get('source', 'website'),
                body.get('userAgent', 'Not provided'), body.get('pageUrl', 'Not provided'),
                documents_count
            )
            
            # Return enhanced success response
            response_data = ContactResponse(
                message='Enhanced contact form submitted successfully with document processing capabilities!',
                contactId=contact_id,
                timestamp=timestamp,
                visitor_count=visitor_count,
                documents_count=documents_count
            )
            
            logger.info(f"Successfully processed enhanced contact submission: {contact_id}")
            return response_data
            
        except Exception as e:
            logger.error(f"Unexpected error in enhanced contact submission: {str(e)}")
            raise Exception(f"Internal Error: An unexpected error occurred. Please try again later.")
    
    async def get_contact_documents(self, contact_id: str) -> Dict[str, Any]:
        """Get all documents for a specific contact (from enhanced_app.py)"""
        try:
            documents = self.database_service.get_contact_documents(contact_id)
            
            return {
                'contact_id': contact_id,
                'documents': documents,
                'total_count': len(documents)
            }
            
        except Exception as e:
            logger.error(f"Error getting contact documents: {str(e)}")
            raise Exception(f"Retrieval Error: Failed to retrieve contact documents.")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get visitor statistics (from enhanced_app.py)"""
        try:
            visitor_count = self.database_service.get_visitor_count()
            
            return {
                "visitor_count": visitor_count,
                "timestamp": datetime.utcnow().isoformat() + 'Z',
                "enhanced_features": True
            }
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            raise Exception("Unable to retrieve statistics")
