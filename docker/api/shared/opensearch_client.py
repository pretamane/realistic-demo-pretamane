# OpenSearch Client - Document indexing and search functionality
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class OpenSearchService:
    """OpenSearch service for document indexing and search"""
    
    def __init__(self, aws_clients):
        self.aws_clients = aws_clients
        self.index_name = os.environ.get('OPENSEARCH_INDEX', 'documents')
        self._client = None
    
    def get_client(self):
        """Get OpenSearch client"""
        if self._client is None:
            self._client = self.aws_clients.get_opensearch_client()
        return self._client
    
    def create_index_if_not_exists(self) -> bool:
        """Create index if not exists with enhanced mapping (from enhanced_index.py)"""
        try:
            opensearch = self.get_client()
            if not opensearch:
                logger.warning("OpenSearch client not available")
                return False
            
            if opensearch.indices.exists(index=self.index_name):
                return True
            
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
            
            opensearch.indices.create(index=self.index_name, body=mapping)
            logger.info(f"Created enhanced index: {self.index_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating OpenSearch index: {str(e)}")
            return False
    
    def index_document(self, document: Dict[str, Any]) -> bool:
        """Index document in OpenSearch (from enhanced_index.py)"""
        try:
            opensearch = self.get_client()
            if not opensearch:
                logger.warning("OpenSearch client not available")
                return False
            
            # Ensure index exists
            self.create_index_if_not_exists()
            
            # Index document
            opensearch.index(index=self.index_name, body=document)
            logger.info(f"Indexed enhanced document: {document['id']}")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing document: {str(e)}")
            return False
    
    def search_documents(self, query: str, filters: Optional[Dict] = None, limit: int = 10) -> Dict[str, Any]:
        """Search documents in OpenSearch"""
        try:
            opensearch = self.get_client()
            if not opensearch:
                logger.warning("OpenSearch client not available")
                return {'results': [], 'total_count': 0, 'query': query, 'processing_time': 0.0}
            
            # Build search query
            search_body = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["filename^2", "text_content", "metadata.keywords"]
                    }
                },
                "size": limit,
                "sort": [{"timestamp": {"order": "desc"}}]
            }
            
            # Add filters if provided
            if filters:
                filter_clauses = []
                for key, value in filters.items():
                    filter_clauses.append({"term": {key: value}})
                
                if filter_clauses:
                    search_body["query"] = {
                        "bool": {
                            "must": search_body["query"],
                            "filter": filter_clauses
                        }
                    }
            
            # Execute search
            start_time = datetime.utcnow()
            response = opensearch.search(index=self.index_name, body=search_body)
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Process results
            results = []
            for hit in response['hits']['hits']:
                source = hit['_source']
                results.append({
                    'document_id': source['id'],
                    'filename': source['filename'],
                    'contact_id': source['contact_id'],
                    'document_type': source['document_type'],
                    'text_content': source.get('text_content', ''),
                    'metadata': source.get('metadata', {}),
                    'upload_timestamp': source['upload_timestamp'],
                    'processing_status': source.get('processing_info', {}).get('status', 'unknown'),
                    'score': hit['_score']
                })
            
            return {
                'results': results,
                'total_count': response['hits']['total']['value'],
                'query': query,
                'processing_time': processing_time
            }
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return {'results': [], 'total_count': 0, 'query': query, 'processing_time': 0.0}
    
    def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID from OpenSearch"""
        try:
            opensearch = self.get_client()
            if not opensearch:
                return None
            
            response = opensearch.get(index=self.index_name, id=document_id)
            return response['_source']
            
        except Exception as e:
            logger.error(f"Error getting document by ID: {str(e)}")
            return None
    
    def delete_document(self, document_id: str) -> bool:
        """Delete document from OpenSearch"""
        try:
            opensearch = self.get_client()
            if not opensearch:
                return False
            
            opensearch.delete(index=self.index_name, id=document_id)
            logger.info(f"Deleted document from index: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return False
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        try:
            opensearch = self.get_client()
            if not opensearch:
                return {}
            
            stats = opensearch.indices.stats(index=self.index_name)
            return {
                'total_documents': stats['indices'][self.index_name]['total']['docs']['count'],
                'index_size': stats['indices'][self.index_name]['total']['store']['size_in_bytes'],
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting index stats: {str(e)}")
            return {}
