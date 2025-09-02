import requests
import json
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

SPECTERX_CONFIG = {
    'api_base_url': 'https://staging-api.specterx.com',
    'api_key': 'OcEWgYAKcn7jjN6jz7qMh2I6VZkYQ0Qo4UPnVt2R',
    'default_regions': ['eu-central']
}



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
        
        initiate_response = requests.post(
            f"{SPECTERX_CONFIG['api_base_url']}/upload/ext/files",
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
            'X-Api-Key': SPECTERX_CONFIG['api_key'],
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
def get_policies(request):
    """
    API endpoint to fetch policies from SpecterX admin API
    """
    try:
        policies_url = f"{SPECTERX_CONFIG['api_base_url']}/admin/policies?fields=settings"
        headers = {
            'X-Api-Key': SPECTERX_CONFIG['api_key'],
            'Content-Type': 'application/json',
            'x-amz-security-token': 'IQoJb3JpZ2luX2VjEMT//////////wEaDGV1LWNlbnRyYWwtMSJHMEUCIDxUEgieCnpUpSLkb7XZYLpY9XlGRRN+WwFRE0Vsho4xAiEAj45k+7FwdoUwgD0uTxH+8/vnYGyjo31K4b+njjHG2bQq1gQILRADGgwwNzU0OTM5MDg1MTIiDGCnsuDnTLeN2+KTUSqzBLZllSMMySCdGR/jqwWyy1Vs596/fucQiB9v7MI2rCdRTP0VflpNe8S/ARxjG/1/CZzLnuJvPtbPB7mH3aSLmleXlmN+jN8IAi8F/URvvK2IuRB57oF6NDbNw+IUDWCXQiZW/ZsKEEHjdpeNO2bmTbJLi9mX/4pGff+zAZGeVdxUoqp4HvLlOKNp16hyqCA4jm7lpSYnC5wpNm/ks6fj2JSV9xDaQ/hL52RGbnvvB2gaTK6zarRnoMx1X12XgsvlJL+c5wySZQo9GmDPBPvZiZXXAHKc4vjBbqA6aKfNlM38o3MDPpTMzeE3fdfNvIyEZn/NM3Bp6b9q9VOJy3D8IOH4fNdvzwmZOEd/iAS5jbBjU/6lsyXJEcEfSYiKTROWIAzAWKZsNzYzEY7p+t1ZfYy4PVP/Rf4g8g7ertv0EwziYDYDJS2aTe1RWX35FSyPwgDmMwnNmb1B5cFRGZ+tkIvChjaAiL6zor0Zhek42xy9cqiENxvmbeIoLY864APPV7owOIPW9Rret5YZc/5w4TXHxMujxfMAEX1go70nVYf6gZOdGMylFmPoBq4uRmP+irwhhZbORVd5gThss3RrvcRSnxSKMniSEMP+5ppHkx/Wqc579hz6E9SUORg/BepmZiBPkvVfL0VZ0EP9UEZwmi87vbEh8gtvEg8Y4s5ioAMHmQVUDS/Uv8mZG+Ci80neJsZ9veeWwqKZ5YfkIktg8xY5QxbqaTexSvrOlQjHsb5FC4HMMOG828UGOoUCEQ/CeF5eAvEapZkEkFkYovjlGdNv45xxjN1Fx9ux7+PiV5mVNGl6AmBj/Oz3b8z1q+Hh5dDhQV8jWE94g8JQSnvF1/vUTNyM2lQ/LJgiToXs/N5SKHRmzXfQenTAeTRwv8MxodhBEwH66fnTxitH0qGTVVx2rFV8Yjr9sm9ioMEjKWZ2LIwaitFTujxFpXWHreHVSGpD2JH+byDedAKKAb3tmQqKWl0sMhYOwjTAWMU5jTKHzb8YDvemYzF7tOn6hzOJhMMyBGiYC+gWoZHPNHURnjQdI+Ecm8czj3rTitZW11dwHLPDRc/OIaAk9HeSgBqGlJBhKf75UyhYNX3diWxXPO4T',
            'authorization': 'AWS4-HMAC-SHA256 Credential=ASIARDE6JUAQMYXMDQXQ/20250902/eu-central-1/execute-api/aws4_request, SignedHeaders=host;x-amz-date;x-amz-security-token, Signature=0327b7b6621c6e40f52007113b49150679c16e1dd39d20a23634973eae157609',
            'x-amz-date': '20250902T124926Z'
        }
        
        response = requests.get(policies_url, headers=headers, timeout=30)
        
        if not response.ok:
            return Response({
                'error': 'Failed to fetch policies from SpecterX',
                'message': f'SpecterX API returned status {response.status_code}',
                'details': response.text[:500]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        policies_data = response.json()
        
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


@api_view(['GET'])
def health_check(request):
    """
    Health check endpoint
    """
    return Response({
        'status': 'healthy',
        'message': 'SpecterX Data Fetching Service is running'
    }, status=status.HTTP_200_OK)
