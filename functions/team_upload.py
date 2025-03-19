import requests, os
from auth_code_req import get_access_token

def upload_file_to_teams_channel(team_id, channel_id, file_path, file_name, secret):
    """Post a file to the specified Teams channel."""
    base_url = "https://graph.microsoft.com/v1.0"
    url = f"{base_url}/teams/{team_id}/channels/{channel_id}/filesFolder"
    

    access_token = get_access_token(secret)

    # First, get the ID of the destination folder in Teams
    headers = {
        "Authorization": f"Bearer {access_token[0]}",
        "Content-Type": "application/json"
    }
    
    folder_response = requests.get(url, headers=headers)
    if folder_response.status_code != 200:
        print("Could not retrieve folder information", folder_response.text)
        return

    folder_info = folder_response.json()
    folder_id = folder_info.get('id')
    if not folder_id:
        print("Could not find folder ID from response")
        return

    drive_id = folder_info.get('parentReference', {}).get('driveId')
    if not drive_id:
        print("Could not find drive ID from response")
        return

    # Upload file to the folder using file API
    upload_url = f"{base_url}/drives/{drive_id}/items/{folder_id}:/{file_name}:/content"
    
    with open(file_path, 'rb') as file_data:
        file_headers = {
            "Authorization": f"Bearer {access_token[0]}",
            "Content-Type": "application/octet-stream"
        }
        upload_response = requests.put(upload_url, headers=file_headers, data=file_data)
    
    if upload_response.status_code in (200, 201):
        web_url = os.path.join(folder_info.get('webUrl'), file_name)
        print(f"File sucessfully uploaded: {web_url}")
    else:
        web_url = None
        print("Failed to upload file", upload_response.text)
    return web_url

def post_message_to_teams(webhook_url, message):
    payload = {
        "text": message
    }

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(webhook_url, json=payload, headers=headers)
    return response.status_code, response.text