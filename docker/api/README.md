# Contact Form API - FastAPI Application

A modern, production-ready FastAPI application for handling contact form submissions with AWS integration.

## 🚀 Features

- **FastAPI Framework**: Modern, fast web framework with automatic API documentation
- **AWS Integration**: DynamoDB for data storage and SES for email notifications
- **Input Validation**: Pydantic models for request/response validation
- **Error Handling**: Comprehensive error handling with proper HTTP status codes
- **CORS Support**: Cross-origin resource sharing for web applications
- **Health Checks**: Comprehensive health monitoring endpoints
- **Auto Documentation**: Interactive API docs at `/docs` and `/redoc`
- **Logging**: Structured logging for monitoring and debugging

## 📋 API Endpoints

### `POST /contact`
Submit a contact form with the following fields:
- `name` (required): Contact person's name (1-100 characters)
- `email` (required): Valid email address
- `message` (required): Contact message (1-1000 characters)
- `company` (optional): Company name (max 100 characters)
- `service` (optional): Service required (max 100 characters)
- `budget` (optional): Budget range (max 50 characters)
- `source` (optional): Source of contact (default: "website")
- `userAgent` (optional): User agent string
- `pageUrl` (optional): Page URL where form was submitted

**Response:**
```json
{
  "message": "Contact form submitted successfully!",
  "contactId": "contact_1234567890_abc12345",
  "timestamp": "2024-01-15T10:30:00Z",
  "visitor_count": 1234
}
```

### `GET /health`
Comprehensive health check that verifies:
- DynamoDB connectivity
- SES connectivity
- Application status

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "dynamodb": "connected",
    "ses": "connected"
  },
  "version": "1.0.0"
}
```

### `GET /stats`
Get visitor statistics from the database.

**Response:**
```json
{
  "visitor_count": 1234,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### `GET /`
Root endpoint with API information.

### `OPTIONS /contact`
Handle CORS preflight requests.

## 🔧 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_REGION` | AWS region for services | `ap-southeast-1` |
| `CONTACTS_TABLE` | DynamoDB table for contacts | `realistic-demo-pretamane-contact-submissions` |
| `VISITORS_TABLE` | DynamoDB table for visitors | `realistic-demo-pretamane-website-visitors` |
| `SES_FROM_EMAIL` | SES sender email | `thawzin252467@gmail.com` |
| `SES_TO_EMAIL` | SES recipient email | `thawzin252467@gmail.com` |
| `ALLOWED_ORIGIN` | CORS allowed origins | `*` |

## 🏗️ Architecture

### Data Flow
1. **Request Validation**: Pydantic models validate incoming data
2. **Data Processing**: Input sanitization and business logic
3. **Database Storage**: Contact data saved to DynamoDB
4. **Counter Update**: Visitor count incremented atomically
5. **Email Notification**: SES sends notification email
6. **Response**: Structured JSON response with confirmation

### AWS Services
- **DynamoDB**: NoSQL database for contact submissions and visitor tracking
- **SES**: Email service for notifications
- **IAM**: Role-based access control with IRSA (IAM Roles for Service Accounts)

## 🚀 Deployment

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export AWS_REGION=ap-southeast-1
export CONTACTS_TABLE=your-contacts-table
export VISITORS_TABLE=your-visitors-table

# Run the application
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### Docker Deployment
```bash
# Build the image
docker build -t contact-api .

# Run the container
docker run -p 8000:8000 \
  -e AWS_REGION=ap-southeast-1 \
  -e CONTACTS_TABLE=your-contacts-table \
  -e VISITORS_TABLE=your-visitors-table \
  contact-api
```

### Kubernetes Deployment
The application is configured for deployment on EKS with:
- Service account with IRSA for AWS permissions
- Health checks for liveness and readiness probes
- Resource limits and requests
- Horizontal Pod Autoscaler (HPA) support

## 📊 Monitoring & Observability

### Health Checks
- **Liveness Probe**: `/health` endpoint
- **Readiness Probe**: `/health` endpoint
- **Startup Probe**: Application startup events

### Logging
- Structured logging with timestamps
- Request/response logging
- Error tracking with context
- AWS service interaction logging

### Metrics
- Request count and duration
- Error rates by endpoint
- AWS service health status
- Visitor count tracking

## 🧪 Testing

### Run Tests
```bash
# Test the application structure
python test_app.py

# Test with pytest (if available)
pytest test_app.py -v
```

### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔒 Security Features

- **Input Validation**: Pydantic models prevent injection attacks
- **CORS Configuration**: Configurable cross-origin policies
- **IAM Integration**: Least-privilege access with IRSA
- **Error Handling**: No sensitive information in error responses
- **Logging**: Audit trail for all operations

## 🚨 Error Handling

### HTTP Status Codes
- `200`: Success
- `400`: Validation error
- `429`: Rate limiting (DynamoDB throttling)
- `500`: Internal server error
- `503`: Service unavailable (health check failure)

### Error Response Format
```json
{
  "error": "Error Type",
  "message": "Human-readable error message"
}
```

## 📈 Performance

### Optimizations
- **Async/Await**: Non-blocking I/O operations
- **Connection Pooling**: Boto3 handles AWS connection pooling
- **Input Validation**: Fast Pydantic validation
- **Error Handling**: Efficient exception handling

### Scaling
- **Horizontal Scaling**: Stateless application design
- **Auto-scaling**: HPA support for pod scaling
- **Database Scaling**: DynamoDB auto-scaling
- **Load Balancing**: ALB integration

## 🔄 Migration from Lambda

This FastAPI application was migrated from AWS Lambda with the following improvements:

### Added Features
- **Interactive Documentation**: Auto-generated API docs
- **Better Error Handling**: HTTPException with proper status codes
- **Request/Response Models**: Pydantic validation
- **Health Monitoring**: Comprehensive health checks
- **Startup/Shutdown Events**: Application lifecycle management

### Maintained Compatibility
- **Same Business Logic**: Identical contact form processing
- **Same AWS Integration**: DynamoDB and SES usage
- **Same Data Format**: Compatible request/response structure
- **Same Environment Variables**: Drop-in replacement

## 📚 Dependencies

- **FastAPI**: Modern web framework
- **Uvicorn**: ASGI server
- **Boto3**: AWS SDK
- **Pydantic**: Data validation
- **Python-dotenv**: Environment variable management

## 🤝 Contributing

1. Follow PEP 8 style guidelines
2. Add tests for new features
3. Update documentation
4. Use meaningful commit messages

## 📄 License

This project is part of the realistic-demo-pretamane application.
