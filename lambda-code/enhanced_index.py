# Enhanced Lambda function for Document Processing & Contact Intelligence
# Processes S3 events and enriches contact data with document metadata

import json
import boto3
import os
from opensearchpy import OpenSearch, helpers
from datetime import datetime
import hashlib
import mimetypes
import re
from typing import Dict, Any, List
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses')

def get_opensearch_client():
    """Initialize OpenSearch client with enhanced configuration"""
    return OpenSearch(
        hosts=[os.environ['OPENSEARCH_ENDPOINT']],
        http_auth=(os.environ['OPENSEARCH_USERNAME'], os.environ['OPENSEARCH_PASSWORD']),
        use_ssl=True,
        verify_certs=True,
        ssl_assert_hostname=False,
        ssl_show_warn=False,
        timeout=30,
        max_retries=3,
        retry_on_timeout=True
    )

def extract_text_from_content(content: str, content_type: str) -> str:
    """Extract text content from various file types"""
    try:
        if content_type == 'application/json':
            data = json.loads(content)
            return json.dumps(data, indent=2)
        elif content_type == 'text/plain':
            return content
        elif content_type == 'text/csv':
            # Basic CSV processing
            lines = content.split('\n')
            return '\n'.join(lines[:10])  # First 10 lines for preview
        else:
            # For other types, return a preview
            return content[:1000] + "..." if len(content) > 1000 else content
    except Exception as e:
        logger.error(f"Error extracting text: {str(e)}")
        return content[:500] if content else ""

def extract_metadata_from_content(content: str, filename: str) -> Dict[str, Any]:
    """Extract metadata from document content"""
    metadata = {
        'word_count': len(content.split()) if content else 0,
        'character_count': len(content) if content else 0,
        'line_count': len(content.split('\n')) if content else 0,
        'file_extension': os.path.splitext(filename)[1].lower(),
        'has_email': bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)),
        'has_phone': bool(re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', content)),
        'has_url': bool(re.search(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)),
        'language_detected': 'en',  # Simplified - would use language detection library in production
        'keywords': extract_keywords(content),
        'entities': extract_entities(content)
    }
    return metadata

def extract_keywords(content: str) -> List[str]:
    """Extract keywords from content (simplified implementation)"""
    if not content:
        return []
    
    # Simple keyword extraction - in production, use NLP libraries
    words = re.findall(r'\b[a-zA-Z]{3,}\b', content.lower())
    word_freq = {}
    for word in words:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    # Return top 10 most frequent words
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in sorted_words[:10] if freq > 1]

def extract_entities(content: str) -> Dict[str, List[str]]:
    """Extract entities from content (simplified implementation)"""
    entities = {
        'emails': re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content),
        'phones': re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', content),
        'urls': re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content),
        'dates': re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', content),
        'amounts': re.findall(r'\$\d+(?:,\d{3})*(?:\.\d{2})?', content)
    }
    return entities

def enrich_contact_data(contact_id: str, document_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich contact data with document insights"""
    try:
        contacts_table = os.environ.get('CONTACTS_TABLE', 'realistic-demo-pretamane-contact-submissions')
        table = dynamodb.Table(contacts_table)
        
        # Get current contact data
        response = table.get_item(Key={'id': contact_id})
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
                'complexity_score': calculate_complexity_score(document_metadata),
                'confidence_level': 'high' if document_metadata.get('word_count', 0) > 100 else 'medium'
            }
        }
        
        # Update contact with document insights
        update_expression = "SET document_insights = :insights, last_updated = :timestamp"
        expression_values = {
            ':insights': document_insights,
            ':timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        table.update_item(
            Key={'id': contact_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values
        )
        
        logger.info(f"Enriched contact {contact_id} with document insights")
        return document_insights
        
    except Exception as e:
        logger.error(f"Error enriching contact data: {str(e)}")
        return {}

def calculate_complexity_score(metadata: Dict[str, Any]) -> float:
    """Calculate document complexity score"""
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

def send_processing_notification(contact_id: str, document_metadata: Dict[str, Any], processing_status: str):
    """Send notification about document processing status"""
    try:
        contacts_table = os.environ.get('CONTACTS_TABLE', 'realistic-demo-pretamane-contact-submissions')
        table = dynamodb.Table(contacts_table)
        
        response = table.get_item(Key={'id': contact_id})
        if 'Item' not in response:
            return
        
        contact = response['Item']
        
        subject = f"Document Processing Update - {contact['name']}"
        body = f"""
Document Processing Status Update

Contact: {contact['name']} ({contact['email']})
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
        
        ses.send_email(
            Source=os.environ.get('SES_FROM_EMAIL', 'noreply@example.com'),
            Destination={'ToAddresses': [contact['email']]},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': body}}
            }
        )
        
        logger.info(f"Sent processing notification to {contact['email']}")
        
    except Exception as e:
        logger.error(f"Error sending processing notification: {str(e)}")

def lambda_handler(event, context):
    """
    Enhanced Lambda function to process S3 objects and enrich contact data
    """
    try:
        logger.info(f"Processing event: {json.dumps(event)}")
        
        # Get OpenSearch client
        opensearch = get_opensearch_client()
        
        # Process S3 event
        for record in event['Records']:
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            
            logger.info(f"Processing S3 object: s3://{bucket}/{key}")
            
            # Get object from S3
            response = s3_client.get_object(Bucket=bucket, Key=key)
            content = response['Body'].read().decode('utf-8')
            content_type = response.get('ContentType', 'application/octet-stream')
            
            # Extract metadata from S3 object metadata
            s3_metadata = response.get('Metadata', {})
            contact_id = s3_metadata.get('contact_id', 'unknown')
            document_type = s3_metadata.get('document_type', 'unknown')
            upload_timestamp = s3_metadata.get('upload_timestamp', datetime.utcnow().isoformat())
            
            # Extract text content
            text_content = extract_text_from_content(content, content_type)
            
            # Extract metadata
            filename = os.path.basename(key)
            document_metadata = extract_metadata_from_content(text_content, filename)
            
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
            documents_table = os.environ.get('DOCUMENTS_TABLE', 'realistic-demo-pretamane-documents')
            doc_table = dynamodb.Table(documents_table)
            
            # Find document by S3 key
            response_scan = doc_table.scan(
                FilterExpression='s3_key = :s3_key',
                ExpressionAttributeValues={':s3_key': key}
            )
            
            if response_scan['Items']:
                document_id = response_scan['Items'][0]['id']
                
                # Update document with processing metadata
                doc_table.update_item(
                    Key={'id': document_id},
                    UpdateExpression='SET processing_status = :status, processing_metadata = :metadata, processing_timestamp = :timestamp',
                    ExpressionAttributeValues={
                        ':status': 'processing',
                        ':metadata': document_metadata,
                        ':timestamp': datetime.utcnow().isoformat() + 'Z'
                    }
                )
                
                logger.info(f"Updated document {document_id} with processing metadata")
            
            # Prepare document for OpenSearch indexing
            index_name = os.environ.get('OPENSEARCH_INDEX', 'documents')
            
            # Create index if not exists with enhanced mapping
            if not opensearch.indices.exists(index=index_name):
                mapping = {
                    "mappings": {
                        "properties": {
                            "id": {"type": "keyword"},
                            "contact_id": {"type": "keyword"},
                            "filename": {"type": "text", "analyzer": "standard"},
                            "document_type": {"type": "keyword"},
                            "content": {"type": "text", "analyzer": "standard"},
                            "text_content": {"type": "text", "analyzer": "standard"},
                            "metadata": {
                                "type": "object",
                                "properties": {
                                    "word_count": {"type": "integer"},
                                    "character_count": {"type": "integer"},
                                    "line_count": {"type": "integer"},
                                    "file_extension": {"type": "keyword"},
                                    "has_email": {"type": "boolean"},
                                    "has_phone": {"type": "boolean"},
                                    "has_url": {"type": "boolean"},
                                    "language_detected": {"type": "keyword"},
                                    "keywords": {"type": "keyword"},
                                    "entities": {"type": "object"}
                                }
                            },
                            "s3_metadata": {
                                "type": "object",
                                "properties": {
                                    "bucket": {"type": "keyword"},
                                    "key": {"type": "keyword"},
                                    "size": {"type": "long"},
                                    "content_type": {"type": "keyword"},
                                    "last_modified": {"type": "date"}
                                }
                            },
                            "processing_info": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "keyword"},
                                    "timestamp": {"type": "date"},
                                    "complexity_score": {"type": "float"}
                                }
                            },
                            "timestamp": {"type": "date"},
                            "upload_timestamp": {"type": "date"},
                            "processing_timestamp": {"type": "date"}
                        }
                    },
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0,
                        "analysis": {
                            "analyzer": {
                                "custom_text_analyzer": {
                                    "type": "custom",
                                    "tokenizer": "standard",
                                    "filter": ["lowercase", "stop", "snowball"]
                                }
                            }
                        }
                    }
                }
                opensearch.indices.create(index=index_name, body=mapping)
                logger.info(f"Created enhanced index: {index_name}")
            
            # Calculate complexity score
            complexity_score = calculate_complexity_score(document_metadata)
            
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
            opensearch.index(index=index_name, body=document)
            logger.info(f"Indexed enhanced document: {document['id']}")
            
            # Update document status to completed
            if response_scan['Items']:
                doc_table.update_item(
                    Key={'id': document_id},
                    UpdateExpression='SET processing_status = :status, complexity_score = :score, indexed_timestamp = :timestamp',
                    ExpressionAttributeValues={
                        ':status': 'completed',
                        ':score': complexity_score,
                        ':timestamp': datetime.utcnow().isoformat() + 'Z'
                    }
                )
            
            # Enrich contact data
            contact_insights = enrich_contact_data(contact_id, document_metadata)
            logger.info(f"Enriched contact {contact_id} with insights: {contact_insights}")
            
            # Send processing notification
            send_processing_notification(contact_id, document_metadata, 'completed')
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully processed and enriched documents',
                'processed_count': len(event['Records']),
                'enhanced_features': {
                    'contact_enrichment': True,
                    'content_analysis': True,
                    'complexity_scoring': True,
                    'entity_extraction': True,
                    'search_indexing': True,
                    'notification_system': True
                }
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing S3 event: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'enhanced_processing': True
            })
        }



