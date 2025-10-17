# Email Service - Unified email functionality from all Lambda functions
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class EmailService:
    """Unified email service for all components"""
    
    def __init__(self, ses_client):
        self.ses_client = ses_client
        self.from_email = os.environ.get('SES_FROM_EMAIL', 'noreply@example.com')
        self.to_email = os.environ.get('SES_TO_EMAIL', 'admin@example.com')
    
    def send_contact_notification(self, name: str, email: str, company: str, service: str, 
                                budget: str, message: str, timestamp: str, source: str, 
                                user_agent: str, page_url: str, document_count: int = 0) -> Optional[Dict]:
        """Send contact form notification (from lambda_function.py)"""
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

            response = self.ses_client.send_email(
                Source=self.from_email,
                Destination={
                    'ToAddresses': [self.to_email]
                },
                Message={
                    'Subject': {'Data': f'New Contact: {name} - {service}'},
                    'Body': {'Text': {'Data': email_body}}
                }
            )
            return response
        except ClientError as e:
            logger.error(f"Error sending contact notification email: {str(e)}")
            return None
    
    def send_enhanced_contact_notification(self, name: str, email: str, company: str, service: str, 
                                         budget: str, message: str, timestamp: str, source: str, 
                                         user_agent: str, page_url: str, document_count: int = 0) -> Optional[Dict]:
        """Send enhanced contact notification with document info (from enhanced_app.py)"""
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

            response = self.ses_client.send_email(
                Source=self.from_email,
                Destination={
                    'ToAddresses': [self.to_email]
                },
                Message={
                    'Subject': {'Data': f'Enhanced Contact: {name} - {service} (Documents: {document_count})'},
                    'Body': {'Text': {'Data': email_body}}
                }
            )
            return response
        except ClientError as e:
            logger.error(f"Error sending enhanced contact notification email: {str(e)}")
            return None
    
    def send_processing_notification(self, contact_id: str, document_metadata: Dict[str, Any], 
                                   processing_status: str, contact_email: str) -> Optional[Dict]:
        """Send document processing notification (from enhanced_index.py)"""
        try:
            subject = f"Document Processing Update"
            body = f"""
Document Processing Status Update

Contact ID: {contact_id}
Document: {document_metadata.get('filename', 'Unknown')}
Status: {processing_status}
Timestamp: {datetime.utcnow().isoformat()}

Processing Details:
- Document Type: {document_metadata.get('document_type', 'Unknown')}
- File Size: {document_metadata.get('size', 0)} bytes
- Content Analysis: {'Completed' if processing_status == 'completed' else 'In Progress'}
- Search Indexing: {'Available' if processing_status == 'completed' else 'Pending'}

Next Steps:
- Document is now searchable in the system
- Contact insights have been updated
- Analytics data has been refreshed

Best regards,
Document Processing System
"""
            
            response = self.ses_client.send_email(
                Source=self.from_email,
                Destination={'ToAddresses': [contact_email]},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {'Text': {'Data': body}}
                }
            )
            
            logger.info(f"Sent processing notification to {contact_email}")
            return response
            
        except ClientError as e:
            logger.error(f"Error sending processing notification: {str(e)}")
            return None
    
    def send_admin_notification(self, subject: str, message: str) -> Optional[Dict]:
        """Send admin notification"""
        try:
            response = self.ses_client.send_email(
                Source=self.from_email,
                Destination={'ToAddresses': [self.to_email]},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {'Text': {'Data': message}}
                }
            )
            return response
        except ClientError as e:
            logger.error(f"Error sending admin notification: {str(e)}")
            return None
