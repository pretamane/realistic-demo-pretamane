# /lambda-code/index.py
# Lambda function for S3 to OpenSearch indexing

import json
import boto3
import os
from opensearchpy import OpenSearch, helpers
from datetime import datetime

# Initialize OpenSearch client
def get_opensearch_client():
    return OpenSearch(
        hosts=[os.environ['OPENSEARCH_ENDPOINT']],
        http_auth=(os.environ['OPENSEARCH_USERNAME'], os.environ['OPENSEARCH_PASSWORD']),
        use_ssl=True,
        verify_certs=True,
        ssl_assert_hostname=False,
        ssl_show_warn=False
    )

# Initialize S3 client
s3_client = boto3.client('s3')

def lambda_handler(event, context):
    """
    Lambda function to process S3 objects and index them in OpenSearch
    """
    try:
        # Get OpenSearch client
        opensearch = get_opensearch_client()
        
        # Process S3 event
        for record in event['Records']:
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            
            print(f"Processing S3 object: s3://{bucket}/{key}")
            
            # Get object from S3
            response = s3_client.get_object(Bucket=bucket, Key=key)
            content = response['Body'].read().decode('utf-8')
            
            # Parse JSON content
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                print(f"Invalid JSON in {key}, skipping...")
                continue
            
            # Prepare document for indexing
            document = {
                'id': f"{bucket}_{key}_{datetime.now().isoformat()}",
                'source': 's3',
                'bucket': bucket,
                'key': key,
                'timestamp': datetime.now().isoformat(),
                'content': data,
                'metadata': {
                    'size': response['ContentLength'],
                    'last_modified': response['LastModified'].isoformat(),
                    'content_type': response.get('ContentType', 'application/json')
                }
            }
            
            # Index document in OpenSearch
            index_name = os.environ.get('OPENSEARCH_INDEX', 'documents')
            
            # Create index if not exists
            if not opensearch.indices.exists(index=index_name):
                mapping = {
                    "mappings": {
                        "properties": {
                            "id": {"type": "keyword"},
                            "source": {"type": "keyword"},
                            "bucket": {"type": "keyword"},
                            "key": {"type": "keyword"},
                            "timestamp": {"type": "date"},
                            "content": {"type": "object"},
                            "metadata": {"type": "object"}
                        }
                    }
                }
                opensearch.indices.create(index=index_name, body=mapping)
                print(f"Created index: {index_name}")
            
            # Index the document
            opensearch.index(index=index_name, body=document)
            print(f"Indexed document: {document['id']}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully processed S3 objects',
                'processed_count': len(event['Records'])
            })
        }
        
    except Exception as e:
        print(f"Error processing S3 event: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
