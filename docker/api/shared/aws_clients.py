# AWS Client Management - Shared across all components
import boto3
import os
import logging
from typing import Optional
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class AWSClientManager:
    """Centralized AWS client management for all components"""
    
    def __init__(self):
        self.region = os.environ.get('AWS_REGION', 'ap-southeast-1')
        self._dynamodb = None
        self._s3_client = None
        self._ses_client = None
        self._opensearch_client = None
        
    @property
    def dynamodb(self):
        """Lazy initialization of DynamoDB resource"""
        if self._dynamodb is None:
            self._dynamodb = boto3.resource('dynamodb', region_name=self.region)
        return self._dynamodb
    
    @property
    def s3_client(self):
        """Lazy initialization of S3 client"""
        if self._s3_client is None:
            self._s3_client = boto3.client('s3', region_name=self.region)
        return self._s3_client
    
    @property
    def ses_client(self):
        """Lazy initialization of SES client"""
        if self._ses_client is None:
            self._ses_client = boto3.client('ses', region_name=self.region)
        return self._ses_client
    
    def get_opensearch_client(self):
        """Get OpenSearch client with enhanced configuration"""
        if self._opensearch_client is None:
            try:
                from opensearchpy import OpenSearch
                self._opensearch_client = OpenSearch(
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
            except ImportError:
                logger.warning("OpenSearch client not available - opensearch-py not installed")
                return None
            except KeyError as e:
                logger.warning(f"OpenSearch configuration missing: {e}")
                return None
        return self._opensearch_client
    
    def get_dynamo_table(self, table_name: str):
        """Get DynamoDB table with error handling"""
        try:
            table = self.dynamodb.Table(table_name)
            table.load()
            return table
        except ClientError as e:
            logger.error(f"Error accessing DynamoDB table {table_name}: {str(e)}")
            raise Exception("Database configuration error")
    
    def test_aws_connectivity(self) -> dict:
        """Test connectivity to all AWS services"""
        results = {}
        
        # Test DynamoDB
        try:
            contacts_table = os.environ.get('CONTACTS_TABLE', 'realistic-demo-pretamane-contact-submissions')
            table = self.get_dynamo_table(contacts_table)
            results['dynamodb'] = 'connected'
        except Exception as e:
            results['dynamodb'] = f'error: {str(e)}'
        
        # Test SES
        try:
            self.ses_client.get_send_quota()
            results['ses'] = 'connected'
        except Exception as e:
            results['ses'] = f'error: {str(e)}'
        
        # Test S3
        try:
            s3_bucket = os.environ.get('S3_DATA_BUCKET', 'realistic-demo-pretamane-data')
            self.s3_client.head_bucket(Bucket=s3_bucket)
            results['s3'] = 'connected'
        except Exception as e:
            results['s3'] = f'error: {str(e)}'
        
        # Test OpenSearch
        try:
            opensearch = self.get_opensearch_client()
            if opensearch:
                opensearch.cluster.health()
                results['opensearch'] = 'connected'
            else:
                results['opensearch'] = 'not_configured'
        except Exception as e:
            results['opensearch'] = f'error: {str(e)}'
        
        return results
