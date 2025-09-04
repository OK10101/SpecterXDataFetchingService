# SpecterX Data Fetching Service

A Django REST API that integrates Microsoft Graph API with SpecterX platform, designed to work with SharePoint Framework (SPFx) applications.

## Features

- **Graph API Integration**: Fetch files from SharePoint/OneDrive using Microsoft Graph API
- **SpecterX Upload**: Direct integration with SpecterX platform for file uploads
- **File Policy Management**: Set and update policies for files with user ownership validation
- **File Sharing**: Share files with recipients with configurable permissions and options
- **Policy Management**: Retrieve available policies from SpecterX admin API
- **CORS Support**: Full CORS support for cross-origin requests from SPFx applications

## Quick Start

### 1. Environment Setup

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and set your SpecterX API key:

```env
SPECTERX_API_KEY=your_actual_specterx_api_key_here
```

### 2. Install Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Run the Server

```bash
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/api/`

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SPECTERX_API_KEY` | Your SpecterX API key | Yes | Fallback hardcoded key (for development only) |
| `DEBUG` | Django debug mode | No | True |
| `SECRET_KEY` | Django secret key | No | Auto-generated |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | No | Current configuration |

## API Endpoints

- `POST /api/fetch-upload/` - Fetch file from Graph API and upload to SpecterX
- `GET /api/policies/` - Get available policies from SpecterX
- `PUT /api/files/{file_id}/policy/` - Set/update policy for a file
- `POST /api/share/` - Share a file with recipients
- `GET /api/health/` - Health check endpoint

## Security Notes

⚠️ **Important**: Never commit your actual API key to version control. The `.env` file is already in `.gitignore` to prevent accidental commits.

For production deployment:
1. Set `SPECTERX_API_KEY` environment variable on your server
2. Set `DEBUG=False`
3. Configure proper `ALLOWED_HOSTS`
4. Use HTTPS

## Documentation

See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for detailed API reference with examples and request/response formats.