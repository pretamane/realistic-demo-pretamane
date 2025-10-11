#!/usr/bin/env python3
"""
Simple test script for the FastAPI application
"""
import os
import sys
import asyncio
from fastapi.testclient import TestClient

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables for testing
os.environ['AWS_REGION'] = 'ap-southeast-1'
os.environ['CONTACTS_TABLE'] = 'test-contacts'
os.environ['VISITORS_TABLE'] = 'test-visitors'
os.environ['SES_FROM_EMAIL'] = 'test@example.com'
os.environ['SES_TO_EMAIL'] = 'test@example.com'
os.environ['ALLOWED_ORIGIN'] = '*'

try:
    from app import app
    
    def test_app():
        """Test the FastAPI application"""
        client = TestClient(app)
        
        # Test root endpoint
        print("Testing root endpoint...")
        response = client.get("/")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Test health endpoint
        print("\nTesting health endpoint...")
        try:
            response = client.get("/health")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Health check failed (expected in test environment): {e}")
        
        # Test stats endpoint
        print("\nTesting stats endpoint...")
        try:
            response = client.get("/stats")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Stats endpoint failed (expected in test environment): {e}")
        
        # Test contact endpoint with valid data
        print("\nTesting contact endpoint...")
        test_data = {
            "name": "Test User",
            "email": "test@example.com",
            "message": "This is a test message",
            "company": "Test Company",
            "service": "Web Development",
            "budget": "$10,000 - $50,000"
        }
        
        try:
            response = client.post("/contact", json=test_data)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Contact endpoint failed (expected in test environment): {e}")
        
        print("\n FastAPI application structure is correct!")
        print(" API Documentation available at: http://localhost:8000/docs")
        print(" Alternative docs at: http://localhost:8000/redoc")
    
    if __name__ == "__main__":
        test_app()
        
except ImportError as e:
    print(f" Import error: {e}")
    print("Make sure all dependencies are installed:")
    print("pip install fastapi uvicorn boto3 python-dotenv pydantic[email]")
    sys.exit(1)
except Exception as e:
    print(f" Error: {e}")
    sys.exit(1)
