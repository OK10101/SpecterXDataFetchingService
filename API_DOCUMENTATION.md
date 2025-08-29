# SpecterX Data Fetching Service API Documentation

## Overview

The SpecterX Data Fetching Service is a Django REST API that integrates Microsoft Graph API with SpecterX platform. It's designed to work with SharePoint Framework (SPFx) applications by fetching files from SharePoint/OneDrive using Graph API tokens and uploading them directly to SpecterX.

## Base URL

When running locally: `http://127.0.0.1:8000/api/`

## Authentication

The API accepts Microsoft Graph API tokens via:
- **Authorization Header**: `Bearer <token>`
- **Request Body**: `{"token": "<token>"}`

## Endpoints

### 1. Fetch and Upload File

**Endpoint**: `POST /api/fetch-upload/`

**Description**: Fetches file content from Microsoft Graph API and uploads it to SpecterX in a single operation. This endpoint combines file retrieval from SharePoint/OneDrive with upload to the SpecterX platform.

#### Request Format

```json
{
  "token": "string (optional if provided in Authorization header)",
  "site_id": "string (required)",
  "drive_id": "string (required)", 
  "drive_item_id": "string (required)",
  "filename": "string (required)",
  "user_id": "string (required)"
}
```

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `token` | string | Conditional | Graph API token (required if not in Authorization header) |
| `site_id` | string | Yes | SharePoint site ID where the file is located |
| `drive_id` | string | Yes | SharePoint drive ID containing the file |
| `drive_item_id` | string | Yes | SharePoint drive item ID of the file to fetch |
| `filename` | string | Yes | Name of the file for upload to SpecterX |
| `user_id` | string | Yes | SpecterX user ID for the upload operation |

#### Response Format

**Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "File example.pdf successfully fetched and uploaded",
  "file_id": "12345-abcde-67890-fghij",
  "filename": "example.pdf",
  "upload_status": "completed"
}
```

**Error Responses**:

**400 Bad Request** - Missing parameters:
```json
{
  "error": "Missing required parameters",
  "message": "Required: token, site_id, drive_id, drive_item_id, filename, user_id"
}
```

**400 Bad Request** - Graph API fetch failed:
```json
{
  "error": "Failed to fetch file from Graph API",
  "message": "Graph API returned status 404",
  "details": "Item not found or access denied"
}
```

**400 Bad Request** - SpecterX initiate upload failed:
```json
{
  "error": "Failed to initiate upload to SpecterX",
  "message": "SpecterX API returned status 401",
  "details": "Invalid API key or user ID"
}
```

**400 Bad Request** - SpecterX upload failed:
```json
{
  "error": "Failed to upload file to SpecterX",
  "message": "Upload returned status 413",
  "details": "File size exceeds limit"
}
```

**500 Internal Server Error** - Network/Server error:
```json
{
  "error": "Network request failed",
  "message": "Connection timeout or network error"
}
```

#### Process Flow

1. **Validation**: Validates all required parameters are provided
2. **Fetch**: Retrieves file content from Graph API using the SharePoint coordinates
3. **Initiate**: Calls SpecterX API to initiate file upload and receive upload URL
4. **Upload**: Uploads the file content to SpecterX using the provided upload URL
5. **Response**: Returns success status with SpecterX file ID

#### Example Requests

**With Authorization Header**:
```bash
curl -X POST http://127.0.0.1:8000/api/fetch-upload/ \
  -H "Authorization: Bearer YOUR_GRAPH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "site_id": "contoso.sharepoint.com,12345678-1234-1234-1234-123456789012,87654321-4321-4321-4321-210987654321",
    "drive_id": "b!abcdefgh12345678ijklmnop90qrstuv",
    "drive_item_id": "01ABCDEFGHIJKLMNOPQRSTUVWXYZ234567890",
    "filename": "document.pdf",
    "user_id": "user123"
  }'
```

**With Token in Body**:
```bash
curl -X POST http://127.0.0.1:8000/api/fetch-upload/ \
  -H "Content-Type: application/json" \
  -d '{
    "token": "YOUR_GRAPH_TOKEN",
    "site_id": "contoso.sharepoint.com,12345678-1234-1234-1234-123456789012,87654321-4321-4321-4321-210987654321",
    "drive_id": "b!abcdefgh12345678ijklmnop90qrstuv",
    "drive_item_id": "01ABCDEFGHIJKLMNOPQRSTUVWXYZ234567890",
    "filename": "spreadsheet.xlsx",
    "user_id": "user456"
  }'
```

#### SpecterX Integration

This endpoint integrates with the SpecterX platform using:
- **Base URL**: `https://staging-api.specterx.com`
- **Upload Endpoint**: `/upload/ext/files`
- **Default Region**: `eu-central`
- **Authentication**: X-Api-Key header with SpecterX API key
- **User Context**: SpecterxUserId header for user-specific operations

#### Timeouts

- Graph API requests: 30 seconds
- SpecterX initiate upload: 30 seconds  
- SpecterX file upload: 60 seconds (longer timeout for file transfer)

### 2. Health Check

**Endpoint**: `GET /api/health/`

**Description**: Returns the health status of the API service.

#### Response Format

**Success Response (200 OK)**:
```json
{
  "status": "healthy",
  "message": "SpecterX Data Fetching Service is running"
}
```

#### Example Request

```bash
curl -X GET http://127.0.0.1:8000/api/health/
```

## Features

- **Graph API Integration**: Seamlessly fetch files from SharePoint/OneDrive using Microsoft Graph API
- **SpecterX Upload**: Direct integration with SpecterX platform for file uploads
- **Single Operation**: Combines file fetching and uploading in one API call
- **Error Handling**: Comprehensive error responses for all failure scenarios

## CORS and CSRF

- CSRF protection is disabled for the fetch-upload endpoint to support cross-origin requests from SPFx applications
- The service is designed to work with SharePoint Framework applications

## Error Handling

The API provides detailed error responses for various failure scenarios:
- Missing authentication tokens
- Missing required parameters
- Graph API access failures
- SpecterX API failures
- Network/connectivity issues
- General server errors

## Security Considerations

1. **Token Validation**: The service accepts Microsoft Graph API tokens but does not validate them - validation occurs when making requests to Graph API
2. **API Keys**: SpecterX API key is embedded in the service - ensure proper security for the service deployment
3. **HTTPS**: In production, ensure all communications use HTTPS
4. **Rate Limiting**: Consider implementing rate limiting for production use
5. **Logging**: Monitor and log API usage for security auditing

## Development

To run the service locally:

1. Activate the virtual environment: `source venv/bin/activate`
2. Start the Django development server: `python manage.py runserver`
3. The API will be available at `http://127.0.0.1:8000/api/`

## Dependencies

- Django REST Framework
- Python Requests library
- Django CSRF middleware (disabled for proxy endpoint)