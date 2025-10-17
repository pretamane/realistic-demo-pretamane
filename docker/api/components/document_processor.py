# Document Processor Component - Extracted from enhanced_index.py
import os
import time
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import UploadFile

from shared.aws_clients import AWSClientManager
from shared.email_service import EmailService
from shared.database_service import DatabaseService
from shared.opensearch_client import OpenSearchService
from utils.document_processing import DocumentProcessingService
from utils.validation import ValidationService
from models.document import DocumentUpload, DocumentResponse, SearchRequest, SearchResponse, DocumentRecord
from models.contact import ContactRecord

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Document processing component extracted from enhanced_index.py"""
    
    def __init__(self, aws_clients: AWSClientManager):
        self.aws_clients = aws_clients
        self.email_service = EmailService(aws_clients.ses_client)
        self.database_service = DatabaseService(aws_clients)
        self.opensearch_service = OpenSearchService(aws_clients)
        self.validation_service = ValidationService()
        
        # Configuration
        self.MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
        self.ALLOWED_EXTENSIONS = {
            # Document formats
            '.pdf', '.doc', '.docx', '.txt', '.json', '.csv', '.xlsx', '.pptx',
            # Image formats
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.tiff', '.tif'
        }
        self.UPLOAD_DIR = "/mnt/efs/uploads"
        self.PROCESSED_DIR = "/mnt/efs/processed"
    
    def validate_file(self, file: UploadFile) -> bool:
        """Validate uploaded file (from enhanced_app.py)"""
        if not file.filename:
            return False
        
        return self.validation_service.validate_file_extension(file.filename, self.ALLOWED_EXTENSIONS)
    
    async def upload_document(self, file: UploadFile, contact_id: str, document_type: str, 
                            description: Optional[str] = None, tags: Optional[str] = None) -> DocumentResponse:
        """Upload and process documents with contact association (from enhanced_app.py)"""
        try:
            # Validate file
            if not self.validate_file(file):
                raise ValueError(f'File type not supported. Allowed types: {", ".join(self.ALLOWED_EXTENSIONS)}')
            
            # Read file content
            content = await file.read()
            
            # Check file size
            if len(content) > self.MAX_FILE_SIZE:
                raise ValueError(f'File size exceeds maximum limit of {self.MAX_FILE_SIZE // (1024*1024)}MB')
            
            # Generate document metadata
            document_id = str(uuid.uuid4())
            file_hash = DocumentProcessingService.get_file_hash(content)
            timestamp = datetime.utcnow().isoformat() + 'Z'
            
            # Determine content type
            import mimetypes
            content_type, _ = mimetypes.guess_type(file.filename)
            if not content_type:
                content_type = 'application/octet-stream'
            
            # Save file to EFS
            file_path = os.path.join(self.UPLOAD_DIR, f"{document_id}_{file.filename}")
            import aiofiles
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            # Upload to S3 for processing
            s3_key = f"documents/{contact_id}/{document_id}_{file.filename}"
            s3_bucket = os.environ.get('S3_DATA_BUCKET', 'realistic-demo-pretamane-data')
            
            self.aws_clients.s3_client.put_object(
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
            
            self.database_service.create_document_record(document_item)
            
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
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}")
            raise Exception(f"Upload Error: Failed to upload document. Please try again.")
    
    async def process_s3_document(self, bucket: str, key: str) -> Dict[str, Any]:
        """Process S3 document (from enhanced_index.py)"""
        try:
            logger.info(f"Processing S3 object: s3://{bucket}/{key}")
            
            # Get object from S3
            response = self.aws_clients.s3_client.get_object(Bucket=bucket, Key=key)
            content = response['Body'].read().decode('utf-8')
            content_type = response.get('ContentType', 'application/octet-stream')
            
            # Extract metadata from S3 object metadata
            s3_metadata = response.get('Metadata', {})
            contact_id = s3_metadata.get('contact_id', 'unknown')
            document_type = s3_metadata.get('document_type', 'unknown')
            upload_timestamp = s3_metadata.get('upload_timestamp', datetime.utcnow().isoformat())
            
            # Extract text content
            text_content = DocumentProcessingService.extract_text_from_content(content, content_type)
            
            # Extract metadata
            filename = os.path.basename(key)
            document_metadata = DocumentProcessingService.extract_metadata_from_content(text_content, filename)
            
            # Add S3 metadata
            document_metadata.update({
                'filename': filename,
                'size': response['ContentLength'],
                'content_type': content_type,
                'last_modified': response['LastModified'].isoformat(),
                's3_bucket': bucket,
                's3_key': key,
                'contact_id': contact_id,
                'document_type': document_type,
                'upload_timestamp': upload_timestamp,
                'processing_timestamp': datetime.utcnow().isoformat(),
                'processing_status': 'processing'
            })
            
            # Update document status in DynamoDB
            documents_table = self.database_service.get_documents_table()
            
            # Find document by S3 key
            response_scan = documents_table.scan(
                FilterExpression='s3_key = :s3_key',
                ExpressionAttributeValues={':s3_key': key}
            )
            
            document_id = None
            if response_scan['Items']:
                document_id = response_scan['Items'][0]['id']
                
                # Update document with processing metadata
                self.database_service.update_document_status(document_id, 'processing', document_metadata)
                
                logger.info(f"Updated document {document_id} with processing metadata")
            
            # Prepare document for OpenSearch indexing
            self.opensearch_service.create_index_if_not_exists()
            
            # Calculate complexity score
            complexity_score = DocumentProcessingService.calculate_complexity_score(document_metadata)
            
            # Prepare document for indexing
            document = {
                'id': f"{contact_id}_{filename}_{int(time.time())}",
                'contact_id': contact_id,
                'filename': filename,
                'document_type': document_type,
                'content': content,
                'text_content': text_content,
                'metadata': document_metadata,
                's3_metadata': {
                    'bucket': bucket,
                    'key': key,
                    'size': response['ContentLength'],
                    'content_type': content_type,
                    'last_modified': response['LastModified'].isoformat()
                },
                'processing_info': {
                    'status': 'processing',
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'complexity_score': complexity_score
                },
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'upload_timestamp': upload_timestamp,
                'processing_timestamp': datetime.utcnow().isoformat() + 'Z'
            }
            
            # Index document in OpenSearch
            self.opensearch_service.index_document(document)
            logger.info(f"Indexed enhanced document: {document['id']}")
            
            # Update document status to completed
            if document_id:
                self.database_service.update_document_completion(document_id, complexity_score)
            
            # Enrich contact data
            contact_insights = self.database_service.enrich_contact_data(contact_id, document_metadata)
            logger.info(f"Enriched contact {contact_id} with insights: {contact_insights}")
            
            # Send processing notification
            self._send_processing_notification(contact_id, document_metadata, 'completed')
            
            return {
                'message': 'Successfully processed and enriched documents',
                'processed_count': 1,
                'enhanced_features': {
                    'contact_enrichment': True,
                    'content_analysis': True,
                    'complexity_scoring': True,
                    'entity_extraction': True,
                    'search_indexing': True,
                    'notification_system': True
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing S3 document: {str(e)}")
            return {
                'error': str(e),
                'enhanced_processing': True
            }
    
    async def search_documents(self, search_request: SearchRequest) -> SearchResponse:
        """Search documents with advanced filtering (from enhanced_app.py)"""
        try:
            start_time = time.time()
            
            # Try OpenSearch first, fallback to DynamoDB
            opensearch_results = self.opensearch_service.search_documents(
                search_request.query, 
                search_request.filters, 
                search_request.limit
            )
            
            if opensearch_results['total_count'] > 0:
                processing_time = time.time() - start_time
                return SearchResponse(
                    results=opensearch_results['results'],
                    total_count=opensearch_results['total_count'],
                    query=search_request.query,
                    processing_time=processing_time
                )
            
            # Fallback to DynamoDB search
            results = self.database_service.search_documents(search_request.query, search_request.limit)
            processing_time = time.time() - start_time
            
            return SearchResponse(
                results=results,
                total_count=len(results),
                query=search_request.query,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            raise Exception(f"Search Error: Failed to search documents. Please try again.")
    
    async def get_analytics(self) -> Dict[str, Any]:
        """Get system analytics and insights (from enhanced_app.py)"""
        try:
            return self.database_service.get_analytics_data()
        except Exception as e:
            logger.error(f"Error getting analytics: {str(e)}")
            raise Exception(f"Analytics Error: Failed to retrieve analytics data.")
    
    def _send_processing_notification(self, contact_id: str, document_metadata: Dict[str, Any], processing_status: str):
        """Send processing notification (from enhanced_index.py)"""
        try:
            # Get contact email from database
            contact_table = self.database_service.get_contacts_table()
            response = contact_table.get_item(Key={'id': contact_id})
            if 'Item' not in response:
                return
            
            contact = response['Item']
            contact_email = contact.get('email')
            
            if contact_email:
                self.email_service.send_processing_notification(
                    contact_id, document_metadata, processing_status, contact_email
                )
            
        except Exception as e:
            logger.error(f"Error sending processing notification: {str(e)}")
    
    async def process_background_tasks(self):
        """Process background tasks for S3 events"""
        # This would be implemented as a background task processor
        # For now, it's a placeholder for the background processing functionality
        pass
