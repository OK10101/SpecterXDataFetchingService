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

### 2. Get Policies

**Endpoint**: `GET /api/policies/`

**Description**: Fetches all available policies from SpecterX admin API.

#### Request Format

No request body required.

#### Response Format

**Success Response (200 OK)**:
```json
{
  "success": true,
  "policies": [
    {
      "policy_id": "policy_123",
      "name": "Standard Policy",
      "settings": {...}
    }
  ]
}
```

**Error Response (400 Bad Request)**:
```json
{
  "error": "Failed to fetch policies from SpecterX",
  "message": "SpecterX API returned status 401",
  "details": "Invalid API key"
}
```

#### Example Request

```bash
curl -X GET http://127.0.0.1:8000/api/policies/
```

### 3. Set File Policy

**Endpoint**: `PUT /api/files/{file_id}/policy/`

**Description**: Sets or updates a policy for a specific file. Requires user ownership validation.

#### Request Format

```json
{
  "policy_id": "string (required)",
  "user_id": "string (optional if provided in header)"
}
```

#### Request Headers

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `SpecterxUserId` | string | Conditional | SpecterX user ID (required if not in body) |

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_id` | string | Yes | SpecterX file ID (URL parameter) |
| `policy_id` | string | Yes | Policy ID to assign to the file |
| `user_id` | string | Conditional | SpecterX user ID (required if not in header) |

#### Response Format

**Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "File policy set successfully",
  "file_id": "8fab29ed-de04-44e1-95b6-3dbe676294fe",
  "policy_id": "policy_123",
  "result": {...}
}
```

**Error Responses**:

**400 Bad Request** - Missing parameters:
```json
{
  "error": "Missing required parameter: policy_id"
}
```

**400 Bad Request** - SpecterX API error:
```json
{
  "error": "Failed to set file policy",
  "message": "SpecterX API returned status 403",
  "details": "User does not own this file"
}
```

#### Example Request

```bash
curl -X PUT http://127.0.0.1:8000/api/files/8fab29ed-de04-44e1-95b6-3dbe676294fe/policy/ \
  -H "SpecterxUserId: user_specterxstagingmsonmicrosoftcom_40bf5870" \
  -H "Content-Type: application/json" \
  -d '{
    "policy_id": "policy_123"
  }'
```

### 4. Share File

**Endpoint**: `POST /api/share/`

**Description**: Shares a file with one or more recipients with configurable permissions and options.

#### Request Format

```json
{
  "file_id": "string (required)",
  "recipient": "string (required)",
  "user_id": "string (optional if provided in header)",
  "policy_id": "string (optional)",
  "notify": "boolean (optional, default: true)",
  "protect_message": "boolean (optional, default: true)",
  "message_id": "string (optional)",
  "read_only": "boolean (optional, default: false)",
  "actions": "array (optional)",
  "phone": "string (optional)",
  "prefix": "string (optional)"
}
```

#### Request Headers

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `SpecterxUserId` | string | Conditional | SpecterX user ID (required if not in body) |

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_id` | string | Yes | SpecterX file ID to share |
| `recipient` | string | Yes | Email address of the recipient |
| `user_id` | string | Conditional | SpecterX user ID (required if not in header) |
| `policy_id` | string | No | Policy ID to apply for this share |
| `notify` | boolean | No | Notify recipients (default: true) |
| `protect_message` | boolean | No | Protect message (default: true) |
| `message_id` | string | No | Optional message ID to correlate |
| `read_only` | boolean | No | Grant read-only access (default: false) |
| `actions` | array | No | List of allowed actions (e.g., ["download", "print"]) |
| `phone` | string | No | Recipient phone number |
| `prefix` | string | No | Phone prefix/country code |

#### Response Format

**Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "File shared successfully",
  "file_id": "8fab29ed-de04-44e1-95b6-3dbe676294fe",
  "recipient": "bandss@gmail.com",
  "result": {...}
}
```

**Error Responses**:

**400 Bad Request** - Missing parameters:
```json
{
  "error": "Missing required parameter: file_id"
}
```

**400 Bad Request** - SpecterX API error:
```json
{
  "error": "Failed to share file",
  "message": "SpecterX API returned status 403",
  "details": "User does not have sharing permissions"
}
```

#### Example Requests

**Basic Share**:
```bash
curl -X POST http://127.0.0.1:8000/api/share/ \
  -H "SpecterxUserId: user_specterxstagingmsonmicrosoftcom_40bf5870" \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": "8fab29ed-de04-44e1-95b6-3dbe676294fe",
    "recipient": "bandss@gmail.com"
  }'
```

**Advanced Share with Options**:
```bash
curl -X POST http://127.0.0.1:8000/api/share/ \
  -H "SpecterxUserId: user_specterxstagingmsonmicrosoftcom_40bf5870" \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": "8fab29ed-de04-44e1-95b6-3dbe676294fe",
    "recipient": "bandss@gmail.com",
    "policy_id": "policy_123",
    "read_only": true,
    "actions": ["download", "print"],
    "notify": true,
    "protect_message": true
  }'
```

### 5. Health Check

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
- **File Policy Management**: Set and update policies for files with user ownership validation
- **File Sharing**: Share files with recipients with configurable permissions and options
- **Policy Management**: Retrieve available policies from SpecterX admin API
- **Single Operation**: Combines file fetching and uploading in one API call
- **Error Handling**: Comprehensive error responses for all failure scenarios

## CORS and CSRF

- CSRF protection is disabled for specific endpoints (fetch-upload, set-file-policy, share-file) to support cross-origin requests from SPFx applications
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