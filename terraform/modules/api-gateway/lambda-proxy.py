import json
import urllib.request
import urllib.parse
import urllib.error
import os
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda function to proxy requests to the Kubernetes NodePort service
    """
    try:
        # Extract the HTTP method and path
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        
        # Get the Kubernetes service URL from environment variables
        service_url = os.environ.get('K8S_SERVICE_URL', 'http://172.20.236.39:80')

        # Construct the target URL
        target_url = f"{service_url}{path}"
        
        # Handle query parameters
        query_params = event.get('queryStringParameters') or {}
        if query_params:
            query_string = urllib.parse.urlencode(query_params)
            target_url += f"?{query_string}"
        
        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'API-Gateway-Proxy/1.0'
        }
        
        # Add request headers
        request_headers = event.get('headers', {})
        for header_name, header_value in request_headers.items():
            if header_name.lower() not in ['host', 'content-length']:
                headers[header_name] = header_value
        
        # Prepare request data
        body = event.get('body', '')
        if body and http_method in ['POST', 'PUT', 'PATCH']:
            # If body is a string, encode it
            if isinstance(body, str):
                data = body.encode('utf-8')
            else:
                data = body
        else:
            data = None
        
        # Create the request
        req = urllib.request.Request(
            target_url,
            data=data,
            headers=headers,
            method=http_method
        )
        
        # Make the request
        logger.info(f"Proxying {http_method} request to {target_url}")
        
        with urllib.request.urlopen(req, timeout=30) as response:
            response_body = response.read().decode('utf-8')
            status_code = response.getcode()
            
            # Get response headers
            response_headers = {}
            for header_name, header_value in response.headers.items():
                response_headers[header_name] = header_value
            
            return {
                'statusCode': status_code,
                'headers': response_headers,
                'body': response_body
            }
            
    except urllib.error.HTTPError as e:
        logger.error(f"HTTP Error: {e.code} - {e.reason}")
        return {
            'statusCode': e.code,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Upstream service error',
                'message': str(e.reason),
                'status_code': e.code
            })
        }
        
    except urllib.error.URLError as e:
        logger.error(f"URL Error: {str(e)}")
        return {
            'statusCode': 502,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Bad Gateway',
                'message': 'Unable to connect to upstream service',
                'details': str(e)
            })
        }
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred',
                'details': str(e)
            })
        }
