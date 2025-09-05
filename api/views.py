import requests
import json
import os
from functools import wraps
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings

SPECTERX_CONFIG = {
    'api_base_url': 'https://staging-api.specterx.com',
    'api_key': 'OcEWgYAKcn7jjN6jz7qMh2I6VZkYQ0Qo4UPnVt2R',#os.getenv('SPECTERX_API_KEY'),
    'default_regions': ['eu-central']
}

def cors_enabled(allowed_methods):
    """
    Decorator to handle CORS preflight requests and add CORS headers
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # Handle preflight OPTIONS request
            if request.method == 'OPTIONS':
                response = HttpResponse()
                response['Access-Control-Allow-Origin'] = '*'
                response['Access-Control-Allow-Methods'] = ', '.join(allowed_methods + ['OPTIONS'])
                response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, SpecterxUserId, X-Requested-With'
                response['Access-Control-Max-Age'] = '86400'
                return response
            
            # Call the original view function
            result = func(request, *args, **kwargs)
            
            # Add CORS headers to the response
            if hasattr(result, '__setitem__'):  # Check if it's a response object
                result['Access-Control-Allow-Origin'] = '*'
                result['Access-Control-Allow-Methods'] = ', '.join(allowed_methods + ['OPTIONS'])
                result['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, SpecterxUserId, X-Requested-With'
            
            return result
        return wrapper
    return decorator



@cors_enabled(['POST'])
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
        
        try:
            graph_response = requests.get(graph_url, headers=graph_headers, timeout=30)
        except requests.exceptions.Timeout:
            return Response({
                'error': 'Graph API timeout',
                'message': 'Microsoft Graph API request timed out after 30 seconds'
            }, status=status.HTTP_408_REQUEST_TIMEOUT)
        except requests.exceptions.ConnectionError:
            return Response({
                'error': 'Graph API connection error',
                'message': 'Unable to connect to Microsoft Graph API'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
        if not graph_response.ok:
            return Response({
                'error': 'Failed to fetch file from Graph API',
                'message': f'Graph API returned status {graph_response.status_code}',
                'details': graph_response.text[:500]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        file_content = graph_response.content
        
        if not file_content:
            return Response({
                'error': 'Empty file content',
                'message': 'Graph API returned empty file content'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Step 2: Initiate upload to SpecterX
        initiate_payload = {
            'filename': filename,
            'parent_folder': None,
            'regions': SPECTERX_CONFIG['default_regions']
        }
        
        initiate_headers = {
            'Content-Type': 'application/json',
            'X-Api-Key': SPECTERX_CONFIG['api_key'],
            'SpecterxUserId': user_id
        }
        
        try:
            initiate_response = requests.post(
                f"{SPECTERX_CONFIG['api_base_url']}/upload/ext/files",
                headers=initiate_headers,
                json=initiate_payload,
                timeout=30
            )
        except requests.exceptions.Timeout:
            return Response({
                'error': 'Request timeout',
                'message': 'SpecterX API initiate upload request timed out after 30 seconds'
            }, status=status.HTTP_408_REQUEST_TIMEOUT)
        except requests.exceptions.ConnectionError:
            return Response({
                'error': 'Connection error',
                'message': 'Unable to connect to SpecterX API for initiate upload'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        if not initiate_response.ok:
            return Response({
                'error': 'Failed to initiate upload to SpecterX',
                'message': f'SpecterX API returned status {initiate_response.status_code}',
                'details': initiate_response.text[:500]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            initiate_data = initiate_response.json()
        except json.JSONDecodeError:
            return Response({
                'error': 'Invalid response from SpecterX',
                'message': 'SpecterX API returned invalid JSON response for initiate upload'
            }, status=status.HTTP_502_BAD_GATEWAY)
            
        upload_url = initiate_data.get('url')
        file_id = initiate_data.get('file_id')
        
        if not upload_url or not file_id:
            return Response({
                'error': 'Invalid SpecterX response',
                'message': 'SpecterX API did not return required upload_url or file_id'
            }, status=status.HTTP_502_BAD_GATEWAY)
        
        # Step 3: Upload file content to SpecterX
        upload_headers = {
            'X-Api-Key': SPECTERX_CONFIG['api_key'],
            'Content-Type': 'application/octet-stream',
            'SpecterxUserId': user_id
        }
        
        try:
            upload_response = requests.put(
                upload_url,
                headers=upload_headers,
                data=file_content,
                timeout=60
            )
        except requests.exceptions.Timeout:
            return Response({
                'error': 'Upload timeout',
                'message': 'File upload to SpecterX timed out after 60 seconds'
            }, status=status.HTTP_408_REQUEST_TIMEOUT)
        except requests.exceptions.ConnectionError:
            return Response({
                'error': 'Upload connection error',
                'message': 'Unable to connect to SpecterX for file upload'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
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


@cors_enabled(['GET'])
@api_view(['GET', 'OPTIONS'])
@csrf_exempt
def get_policies(request):
    """
    API endpoint to fetch policies from SpecterX admin API
    """
    try:
        user_id = request.headers.get('SpecterxUserId') or request.GET.get('user_id')
        policies_url = f"{SPECTERX_CONFIG['api_base_url']}/admin/policies?fields=settings"
        headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
            'user-agent': 'SpecterX-PolicyGetter/1.0',
            'origin': 'https://staging-app.specterx.com',
            'referer': 'https://staging-app.specterx.com/',
            #'X-API-Key': SPECTERX_CONFIG['api_key'],
            'SpecterxUserId': user_id,
            'authorization': 'AWS4-HMAC-SHA256 Credential=ASIARDE6JUAQOMAHTOOE/20250905/eu-central-1/execute-api/aws4_request, SignedHeaders=host;x-amz-date;x-amz-security-token, Signature=280e646ec4311d7f9b2c1c1f36e02110294ad4a6e30ef384e603e82b6680d8de',
            'x-amz-date': '20250905T114405Z',
            'x-amz-security-token': 'IQoJb3JpZ2luX2VjEAwaDGV1LWNlbnRyYWwtMSJFMEMCIC1Fu3UUAZmzbGIbCtur+fdkj7dCzX8GSjLlEu7zEAtsAh8Yy5AdD8idtuB4+ZV5XWmPnTKX68zdxaNij8SznaJ7KtYECHUQAxoMMDc1NDkzOTA4NTEyIgztHGmGQ7I3kNpOVssqswT5bN2g9exWoaYkiXiFTxpjC5Prj0G2xQGoZJ29MTgx9yYzVLj6COROMpelGuKxTSjEAXEKyww7KLoSB7s6JZ6EEr3/Wa6qQy48WGp/2Nl6kBDriy52P5Gk5sLqfXj7S58J/YfmYm8E9tnwzqrLuTr/jgNXYfHikcKJ2qVHYF3TETK2ALKw0zMdmrJzVWngIoz/hWvkrk2L8ONWu0tAVzte7XrRP2cx9eatnrH0NMTnn5djRMjwtUec64cXVSOJ0sSqWf58Kv0leD80G/A063ls5KrvA8tzmNMqGjMGAi8u5FsKy4GVidimuaHkQ/gskBSfd36aMaRrKDqwrCYRGabZcOxpUAVjO9OihajhSs/cAjWnAJtzmTF3RgI4XeXpYC/UprVvfa/SGzYGSiWFsaBGulr2c7Hj92g4+Lx2UynHxpqhxaCLKANbxGw4drXm2102aCAA4pFnHJ7cPTckVucnhGb3CFpWMLapld4cHoby6cdeS/vGDmHw2rNAgsw4lcS6to842wF9yYC+HGkLNxD4K1xkPFeQ9x5f8sCM0gRDg3LGXSsi+tRPdBo4OJOZvMslZx2KsfmayT3ytuK0zQhNwq5YSYh4sVHje0glLxx7BCXTZRIv3dTySA3yy4lpIC5QIwqnzNNq9TqIB2fxvON8dI8aKF5x+WqUSkdx9pRMWOfbM/cFcI1XJHakdkzPLEzbtGVk9hUNO0s67AUnGbPfrtk4bMBmb5lXFCgnff72JzU7GDCFmuvFBjqHAlXlf2dQsWucy7x4AQ4dWuGjG0NU410wUbDNpON9+Aj25Fohx6T4n5zJ+q4LyZwqQX9lxYTBCBTw3an50yYjx8votA+acJSaYf2jgjg61zwoMnYJ+FLqP0LJ2i5ZngBHezpp1SsLCET2XA0RApoq6udNYTVPofm1S7NVM5RL8EHRU4sAtf/CIxiXHOd97yJLiYHvUdhV7yCv98wxErXTTaPbKBITfXpmFTa/wWkVvFlK72wzCWkvZVpowvWlcrJcynDdRliGGAub9pMSGScyu+xTZyaJwev8cF3i8lUwiiO6EC8eydxT9gSGPNTfunQW68DDsJYVNjehLgEBcxaGThPexhQ/nJDU'
        }
        
        try:
            response = requests.get(policies_url, headers=headers, timeout=30)
        except requests.exceptions.Timeout:
            return Response({
                'error': 'Request timeout',
                'message': 'SpecterX policies API request timed out after 30 seconds'
            }, status=status.HTTP_408_REQUEST_TIMEOUT)
        except requests.exceptions.ConnectionError:
            return Response({
                'error': 'Connection error',
                'message': 'Unable to connect to SpecterX policies API'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        if not response.ok:
            return Response({
                'error': 'Failed to fetch policies from SpecterX',
                'message': f'SpecterX API returned status {response.status_code}',
                'details': response.text[:500]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            policies_data = response.json()
        except json.JSONDecodeError:
            return Response({
                'error': 'Invalid response from SpecterX',
                'message': 'SpecterX policies API returned invalid JSON response'
            }, status=status.HTTP_502_BAD_GATEWAY)
        
        # Handle both list and dict responses
        if isinstance(policies_data, list):
            policies = policies_data
        else:
            policies = policies_data.get('policies', [])
        
        return Response({
            'success': True,
            'policies': policies
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


@cors_enabled(['PUT'])
@api_view(['PUT', 'OPTIONS'])
@csrf_exempt
def set_file_policy(request, file_id):
    """
    API endpoint to set/update a policy for a specific file
    """
    try:
        # Extract required parameters
        policy_id = request.data.get('policy_id')
        user_id = request.headers.get('SpecterxUserId') or request.data.get('user_id')
        
        # Validate required parameters
        if not policy_id:
            return Response({
                'error': 'Missing required parameter: policy_id'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if not user_id:
            return Response({
                'error': 'Missing required parameter: user_id (header SpecterxUserId or body user_id)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Set file policy via SpecterX API
        url = f"{SPECTERX_CONFIG['api_base_url']}/access/ext/files/{file_id}/policy"
        headers = {
            'accept': 'application/json, text/plain, */*',
            'content-type': 'application/json; charset=UTF-8',
            'origin': 'https://staging-app.specterx.com',
            'referer': 'https://staging-app.specterx.com/',
            'user-agent': 'SpecterX-PolicySetter/2.0',
            'X-API-Key': SPECTERX_CONFIG['api_key'],
            'SpecterxUserId': user_id,
        }
        
        payload = {'policy_id': policy_id}
        
        try:
            response = requests.put(
                url,
                headers=headers,
                json=payload,
                verify=False,
                timeout=60
            )
        except requests.exceptions.Timeout:
            return Response({
                'error': 'Request timeout',
                'message': 'SpecterX set policy API request timed out after 60 seconds'
            }, status=status.HTTP_408_REQUEST_TIMEOUT)
        except requests.exceptions.ConnectionError:
            return Response({
                'error': 'Connection error',
                'message': 'Unable to connect to SpecterX set policy API'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        if not response.ok:
            return Response({
                'error': 'Failed to set file policy',
                'message': f'SpecterX API returned status {response.status_code}',
                'details': response.text[:500]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Handle response
        try:
            result = response.json()
        except (ValueError, json.JSONDecodeError):
            result = {'raw': response.text}
        
        return Response({
            'success': True,
            'message': 'File policy set successfully',
            'file_id': file_id,
            'policy_id': policy_id,
            'result': result
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


@cors_enabled(['POST'])
@api_view(['POST', 'OPTIONS'])
@csrf_exempt
def share_file(request):
    """
    API endpoint to share a file with recipients
    """
    try:
        # Extract required parameters
        file_id = request.data.get('file_id')
        recipient = request.data.get('recipient')
        user_id = request.headers.get('SpecterxUserId') or request.data.get('user_id')
        
        # Optional parameters
        policy_id = request.data.get('policy_id')
        notify = request.data.get('notify', True)
        protect_message = request.data.get('protect_message', True)
        message_id = request.data.get('message_id', '')
        read_only = request.data.get('read_only', False)
        actions = request.data.get('actions', [])
        phone = request.data.get('phone')
        prefix = request.data.get('prefix')
        
        # Validate required parameters
        if not file_id:
            return Response({
                'error': 'Missing required parameter: file_id'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if not recipient:
            return Response({
                'error': 'Missing required parameter: recipient'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if not user_id:
            return Response({
                'error': 'Missing required parameter: user_id (header SpecterxUserId or body user_id)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Build payload
        files_entry = {'file_id': file_id}
        if policy_id:
            files_entry['policy_id'] = policy_id
            
        user_entry = {
            'readOnly': read_only,
            'actions': actions,
            'email': recipient,
        }
        
        if phone or prefix:
            user_entry['phoneNumber'] = {'phone': phone or '', 'prefix': prefix or ''}
            
        payload = {
            'files': [files_entry],
            'notify_recipients': notify,
            'message_id': message_id,
            'protect_message': protect_message,
            'users': [user_entry],
            'groups': [],
        }
        
        # Share file via SpecterX API
        url = f"{SPECTERX_CONFIG['api_base_url']}/access/ext/share"
        headers = {
            'accept': 'application/json, text/plain, */*',
            'content-type': 'application/json; charset=UTF-8',
            'origin': 'https://staging-app.specterx.com',
            'referer': 'https://staging-app.specterx.com/',
            'user-agent': 'SpecterX-Share/1.0',
            'X-API-Key': SPECTERX_CONFIG['api_key'],
            'SpecterxUserId': user_id,
        }
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                verify=False,
                timeout=60
            )
        except requests.exceptions.Timeout:
            return Response({
                'error': 'Request timeout',
                'message': 'SpecterX share file API request timed out after 60 seconds'
            }, status=status.HTTP_408_REQUEST_TIMEOUT)
        except requests.exceptions.ConnectionError:
            return Response({
                'error': 'Connection error',
                'message': 'Unable to connect to SpecterX share file API'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        if not response.ok:
            return Response({
                'error': 'Failed to share file',
                'message': f'SpecterX API returned status {response.status_code}',
                'details': response.text[:500]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Handle response
        try:
            result = response.json()
        except (ValueError, json.JSONDecodeError):
            result = {'raw': response.text}
        
        return Response({
            'success': True,
            'message': 'File shared successfully',
            'file_id': file_id,
            'recipient': recipient,
            'result': result
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


@cors_enabled(['POST'])
@api_view(['POST', 'OPTIONS'])
@csrf_exempt
def get_multiple_link(request):
    """
    API endpoint to get shareable link for multiple files
    """
    try:
        # Extract required parameters
        files_ids = request.data.get('files_ids', [])
        recipient_identity = request.data.get('recipient_identity')
        user_id = request.headers.get('SpecterxUserId') or request.data.get('user_id')
        
        # Validate required parameters
        if not files_ids or not isinstance(files_ids, list):
            return Response({
                'error': 'Missing required parameter: files_ids (must be array)'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if not user_id:
            return Response({
                'error': 'Missing required parameter: user_id (header SpecterxUserId or body user_id)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get multiple link via SpecterX API
        url = f"{SPECTERX_CONFIG['api_base_url']}/access/ext/files/multiple_link"
        headers = {
            'accept': 'application/json, text/plain, */*',
            'content-type': 'application/json; charset=UTF-8',
            'origin': 'https://staging-app.specterx.com',
            'referer': 'https://staging-app.specterx.com/',
            'user-agent': 'SpecterX-LinkGetter/1.0',
            'X-API-Key': SPECTERX_CONFIG['api_key'],
            'SpecterxUserId': user_id,
        }
        
        payload = {
            'files_ids': files_ids,
            'recipient_identity': recipient_identity or '__NO_RECIPIENT__'
        }
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                verify=False,
                timeout=30
            )
        except requests.exceptions.Timeout:
            return Response({
                'error': 'Request timeout',
                'message': 'SpecterX multiple link API request timed out after 30 seconds'
            }, status=status.HTTP_408_REQUEST_TIMEOUT)
        except requests.exceptions.ConnectionError:
            return Response({
                'error': 'Connection error',
                'message': 'Unable to connect to SpecterX multiple link API'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        if not response.ok:
            return Response({
                'error': 'Failed to get multiple link',
                'message': f'SpecterX API returned status {response.status_code}',
                'details': response.text[:500]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Handle response
        try:
            result = response.json()
        except (ValueError, json.JSONDecodeError):
            return Response({
                'error': 'Invalid response from SpecterX',
                'message': 'SpecterX multiple link API returned invalid JSON response'
            }, status=status.HTTP_502_BAD_GATEWAY)
        
        # Validate result has expected fields
        if not isinstance(result, dict):
            return Response({
                'error': 'Invalid response format',
                'message': 'SpecterX multiple link API returned unexpected response format'
            }, status=status.HTTP_502_BAD_GATEWAY)
            
        return Response({
            'success': True,
            'message': 'Multiple link retrieved successfully',
            'files_ids': files_ids,
            'link': result.get('link', ''),
            'result': result
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


@cors_enabled(['GET'])
@api_view(['GET', 'OPTIONS'])
@csrf_exempt
def health_check(request):
    """
    Health check endpoint
    """
    return Response({
        'status': 'healthy',
        'message': 'SpecterX Data Fetching Service is running'
    }, status=status.HTTP_200_OK)
