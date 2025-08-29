import requests
import json
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings



@api_view(['POST'])
@csrf_exempt
def fetch_and_upload_file(request):
    """
    API endpoint to fetch file content from Graph API and upload to SpecterX
    """
    try:
        # Extract required parameters
        graph_token = request.headers.get('Authorization', '').replace('Bearer ', '') or request.data.get('token')
        site_id = request.data.get('site_id')
        drive_id = request.data.get('drive_id')
        drive_item_id = request.data.get('drive_item_id')
        filename = request.data.get('filename')
        user_id = request.data.get('user_id')
        
        # Validate required parameters
        if not all([graph_token, site_id, drive_id, drive_item_id, filename, user_id]):
            return Response({
                'error': 'Missing required parameters',
                'message': 'Required: token, site_id, drive_id, drive_item_id, filename, user_id'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Step 1: Fetch file content from Graph API
        graph_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/items/{drive_item_id}/content"
        graph_headers = {'Authorization': f'Bearer {graph_token}'}
        
        graph_response = requests.get(graph_url, headers=graph_headers, timeout=30)
        if not graph_response.ok:
            return Response({
                'error': 'Failed to fetch file from Graph API',
                'message': f'Graph API returned status {graph_response.status_code}',
                'details': graph_response.text[:500]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        file_content = graph_response.content
        
        # Step 2: Initiate upload to SpecterX
        specterx_config = {
            'api_base_url': 'https://staging-api.specterx.com',
            'api_key': 'OcEWgYAKcn7jjN6jz7qMh2I6VZkYQ0Qo4UPnVt2R',
            'default_regions': ['eu-central']
        }
        
        initiate_payload = {
            'filename': filename,
            'parent_folder': None,
            'regions': specterx_config['default_regions']
        }
        
        initiate_headers = {
            'Content-Type': 'application/json',
            'X-Api-Key': specterx_config['api_key'],
            'SpecterxUserId': user_id
        }
        
        initiate_response = requests.post(
            f"{specterx_config['api_base_url']}/upload/ext/files",
            headers=initiate_headers,
            json=initiate_payload,
            timeout=30
        )
        
        if not initiate_response.ok:
            return Response({
                'error': 'Failed to initiate upload to SpecterX',
                'message': f'SpecterX API returned status {initiate_response.status_code}',
                'details': initiate_response.text[:500]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        initiate_data = initiate_response.json()
        upload_url = initiate_data.get('url')
        file_id = initiate_data.get('file_id')
        
        # Step 3: Upload file content to SpecterX
        upload_headers = {
            'X-Api-Key': specterx_config['api_key'],
            'Content-Type': 'application/octet-stream',
            'SpecterxUserId': user_id
        }
        
        upload_response = requests.put(
            upload_url,
            headers=upload_headers,
            data=file_content,
            timeout=60
        )
        
        if not upload_response.ok:
            return Response({
                'error': 'Failed to upload file to SpecterX',
                'message': f'Upload returned status {upload_response.status_code}',
                'details': upload_response.text[:500]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Return success response
        return Response({
            'success': True,
            'message': f'File {filename} successfully fetched and uploaded',
            'file_id': file_id,
            'filename': filename,
            'upload_status': 'completed'
        }, status=status.HTTP_200_OK)
        
    except requests.exceptions.RequestException as e:
        return Response({
            'error': 'Network request failed',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except Exception as e:
        return Response({
            'error': 'Internal server error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def health_check(request):
    """
    Health check endpoint
    """
    return Response({
        'status': 'healthy',
        'message': 'SpecterX Data Fetching Service is running'
    }, status=status.HTTP_200_OK)
