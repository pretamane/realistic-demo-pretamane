# Database Service - Unified database operations
import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class DatabaseService:
    """Unified database service for all components"""
    
    def __init__(self, aws_clients):
        self.aws_clients = aws_clients
        self.contacts_table_name = os.environ.get('CONTACTS_TABLE', 'realistic-demo-pretamane-contact-submissions')
        self.visitors_table_name = os.environ.get('VISITORS_TABLE', 'realistic-demo-pretamane-website-visitors')
        self.documents_table_name = os.environ.get('DOCUMENTS_TABLE', 'realistic-demo-pretamane-documents')
    
    def get_contacts_table(self):
        """Get contacts table"""
        return self.aws_clients.get_dynamo_table(self.contacts_table_name)
    
    def get_visitors_table(self):
        """Get visitors table"""
        return self.aws_clients.get_dynamo_table(self.visitors_table_name)
    
    def get_documents_table(self):
        """Get documents table"""
        return self.aws_clients.get_dynamo_table(self.documents_table_name)
    
    def create_contact_record(self, contact_data: Dict[str, Any]) -> str:
        """Create contact record (from lambda_function.py and enhanced_app.py)"""
        try:
            contact_table = self.get_contacts_table()
            contact_table.put_item(Item=contact_data)
            logger.info(f"Saved contact submission with ID: {contact_data['id']}")
            return contact_data['id']
        except ClientError as e:
            logger.error(f"Error creating contact record: {str(e)}")
            raise
    
    def update_visitor_count(self) -> int:
        """Update visitor counter (from lambda_function.py and enhanced_app.py)"""
        try:
            visitor_table = self.get_visitors_table()
            visitor_response = visitor_table.update_item(
                Key={'id': 'visitor_count'},
                UpdateExpression='ADD #count :inc',
                ExpressionAttributeNames={'#count': 'count'},
                ExpressionAttributeValues={':inc': 1},
                ReturnValues='UPDATED_NEW'
            )
            visitor_count = int(visitor_response["Attributes"]["count"])
            return visitor_count
        except ClientError as e:
            logger.error(f"Error updating visitor count: {str(e)}")
            return 0
    
    def get_visitor_count(self) -> int:
        """Get current visitor count"""
        try:
            visitor_table = self.get_visitors_table()
            response = visitor_table.get_item(Key={'id': 'visitor_count'})
            return response.get('Item', {}).get('count', 0)
        except ClientError as e:
            logger.error(f"Error getting visitor count: {str(e)}")
            return 0
    
    def create_document_record(self, document_data: Dict[str, Any]) -> str:
        """Create document record (from enhanced_app.py)"""
        try:
            document_table = self.get_documents_table()
            document_table.put_item(Item=document_data)
            logger.info(f"Saved document metadata: {document_data['id']}")
            return document_data['id']
        except ClientError as e:
            logger.error(f"Error creating document record: {str(e)}")
            raise
    
    def update_document_status(self, document_id: str, status: str, metadata: Optional[Dict] = None) -> bool:
        """Update document processing status (from enhanced_index.py)"""
        try:
            document_table = self.get_documents_table()
            
            update_expression = "SET processing_status = :status, processing_timestamp = :timestamp"
            expression_values = {
                ':status': status,
                ':timestamp': datetime.utcnow().isoformat() + 'Z'
            }
            
            if metadata:
                update_expression += ", processing_metadata = :metadata"
                expression_values[':metadata'] = metadata
            
            document_table.update_item(
                Key={'id': document_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            
            logger.info(f"Updated document {document_id} with status: {status}")
            return True
        except ClientError as e:
            logger.error(f"Error updating document status: {str(e)}")
            return False
    
    def update_document_completion(self, document_id: str, complexity_score: float) -> bool:
        """Update document with completion data (from enhanced_index.py)"""
        try:
            document_table = self.get_documents_table()
            
            document_table.update_item(
                Key={'id': document_id},
                UpdateExpression='SET processing_status = :status, complexity_score = :score, indexed_timestamp = :timestamp',
                ExpressionAttributeValues={
                    ':status': 'completed',
                    ':score': complexity_score,
                    ':timestamp': datetime.utcnow().isoformat() + 'Z'
                }
            )
            
            logger.info(f"Updated document {document_id} with completion data")
            return True
        except ClientError as e:
            logger.error(f"Error updating document completion: {str(e)}")
            return False
    
    def get_contact_documents(self, contact_id: str) -> List[Dict[str, Any]]:
        """Get all documents for a contact (from enhanced_app.py)"""
        try:
            document_table = self.get_documents_table()
            
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
            
            return documents
        except ClientError as e:
            logger.error(f"Error getting contact documents: {str(e)}")
            return []
    
    def enrich_contact_data(self, contact_id: str, document_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich contact data with document insights (from enhanced_index.py)"""
        try:
            contact_table = self.get_contacts_table()
            
            # Get current contact data
            response = contact_table.get_item(Key={'id': contact_id})
            if 'Item' not in response:
                logger.warning(f"Contact {contact_id} not found")
                return {}
            
            contact = response['Item']
            
            # Calculate document insights
            document_insights = {
                'total_documents': 1,  # This would be calculated from all documents
                'document_types': [document_metadata.get('document_type', 'unknown')],
                'total_size': document_metadata.get('size', 0),
                'last_document_upload': document_metadata.get('upload_timestamp'),
                'processing_status': document_metadata.get('processing_status', 'pending'),
                'content_analysis': {
                    'has_business_content': document_metadata.get('has_business_keywords', False),
                    'complexity_score': self._calculate_complexity_score(document_metadata),
                    'confidence_level': 'high' if document_metadata.get('word_count', 0) > 100 else 'medium'
                }
            }
            
            # Update contact with document insights
            contact_table.update_item(
                Key={'id': contact_id},
                UpdateExpression="SET document_insights = :insights, last_updated = :timestamp",
                ExpressionAttributeValues={
                    ':insights': document_insights,
                    ':timestamp': datetime.utcnow().isoformat() + 'Z'
                }
            )
            
            logger.info(f"Enriched contact {contact_id} with document insights")
            return document_insights
            
        except ClientError as e:
            logger.error(f"Error enriching contact data: {str(e)}")
            return {}
    
    def _calculate_complexity_score(self, metadata: Dict[str, Any]) -> float:
        """Calculate document complexity score (from enhanced_index.py)"""
        score = 0.0
        
        # Word count factor
        word_count = metadata.get('word_count', 0)
        if word_count > 1000:
            score += 0.3
        elif word_count > 500:
            score += 0.2
        elif word_count > 100:
            score += 0.1
        
        # Entity richness
        entities = metadata.get('entities', {})
        entity_count = sum(len(v) for v in entities.values())
        if entity_count > 10:
            score += 0.3
        elif entity_count > 5:
            score += 0.2
        elif entity_count > 0:
            score += 0.1
        
        # Keyword diversity
        keywords = metadata.get('keywords', [])
        if len(keywords) > 10:
            score += 0.2
        elif len(keywords) > 5:
            score += 0.1
        
        # File type complexity
        file_ext = metadata.get('file_extension', '')
        if file_ext in ['.pdf', '.docx', '.pptx']:
            score += 0.2
        elif file_ext in ['.doc', '.xlsx']:
            score += 0.1
        
        return min(score, 1.0)
    
    def search_documents(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search documents (from enhanced_app.py)"""
        try:
            document_table = self.get_documents_table()
            
            # Basic search simulation
            response = document_table.scan(
                FilterExpression='contains(filename, :query) OR contains(description, :query)',
                ExpressionAttributeValues={':query': query}
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
            return results[:limit]
        except ClientError as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []
    
    def get_analytics_data(self) -> Dict[str, Any]:
        """Get system analytics (from enhanced_app.py)"""
        try:
            contact_table = self.get_contacts_table()
            document_table = self.get_documents_table()
            
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
            
            return {
                'total_contacts': total_contacts,
                'total_documents': total_documents,
                'document_types': document_types,
                'processing_stats': processing_stats,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        except ClientError as e:
            logger.error(f"Error getting analytics data: {str(e)}")
            return {
                'total_contacts': 0,
                'total_documents': 0,
                'document_types': {},
                'processing_stats': {},
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
