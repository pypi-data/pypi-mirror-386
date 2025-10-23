import requests
import ast
import urllib3
import base64
import json
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context




response =  {
    "url": "http://minio.sintef.cloud/quasar-bucket",
    "fields": "{'key': 'test-s3-node', 'AWSAccessKeyId': 'sintef', 'policy': 'eyJleHBpcmF0aW9uIjogIjIwMjUtMTAtMjJUMTQ6MTI6MzFaIiwgImNvbmRpdGlvbnMiOiBbWyJlcSIsICIkYnVja2V0IiwgInF1YXNhci1idWNrZXQiXSwgWyJlcSIsICIka2V5IiwgInRlc3QtczMtbm9kZSJdLCB7ImJ1Y2tldCI6ICJxdWFzYXItYnVja2V0In0sIHsia2V5IjogInRlc3QtczMtbm9kZSJ9XX0=', 'signature': 'UVehEhVbn5qKgjlv8eYbxMZft7E='}"
  }
if isinstance(response['fields'], str):
    response['fields'] = ast.literal_eval(response['fields'])

print("Fields being sent:")
print(response['fields'])

# Upload a file - simpler approach without requests' files parameter
object_name = 'pexels-pixabay-356036.jpg'

with open(object_name, 'rb') as f:
    # Create files dict with just the file
    files = {'file': (object_name, f, 'application/octet-stream')}
    
    # Post with data and files separately  
    http_response = requests.post(
        response['url'],
        data=response['fields'],
        files=files
    )

print(f"Status Code: {http_response.status_code}")
print(f"Response: {http_response.text}")

if http_response.status_code == 204:
    print("\n✓ File uploaded successfully!")
else:
    print(f"\n✗ Upload failed with status {http_response.status_code}")

