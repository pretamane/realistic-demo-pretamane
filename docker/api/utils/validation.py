# Validation utilities - Extracted from lambda_function.py
import re
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Constants from lambda_function.py
MAX_MESSAGE_LENGTH = 1000
MAX_NAME_LENGTH = 100
MAX_EMAIL_LENGTH = 254

class ValidationService:
    """Validation service for input data"""
    
    @staticmethod
    def validate_contact_input(body: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize contact form input (from lambda_function.py)"""
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
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_filename(filename: str) -> bool:
        """Validate filename"""
        if not filename:
            return False
        
        # Check for dangerous characters
        dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in dangerous_chars:
            if char in filename:
                return False
        
        return True
    
    @staticmethod
    def validate_file_extension(filename: str, allowed_extensions: set) -> bool:
        """Validate file extension"""
        if not filename:
            return False
        
        file_ext = os.path.splitext(filename)[1].lower()
        return file_ext in allowed_extensions
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage"""
        # Remove dangerous characters
        dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
        sanitized = filename
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '_')
        
        # Limit length
        if len(sanitized) > 255:
            name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
            sanitized = name[:255-len(ext)-1] + '.' + ext if ext else name[:255]
        
        return sanitized
