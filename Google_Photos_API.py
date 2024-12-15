import pickle
import os
import requests
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from datetime import datetime

class GooglePhotosApi:
    def __init__(self,
                 client_secret_file=r'./credentials/client_secret.json',
                 scopes=['https://www.googleapis.com/auth/photoslibrary.readonly']):
        self.client_secret_file = client_secret_file
        self.scopes = scopes
        self.cred_pickle_file = './credentials/token_photoslibrary_v1.pickle'
        self.cred = None
        self.base_url = "https://photoslibrary.googleapis.com/v1"
    
    # Initialize and authenticate
    def run_local_server(self):
        if os.path.exists(self.cred_pickle_file):
            with open(self.cred_pickle_file, 'rb') as token:
                self.cred = pickle.load(token)

        if not self.cred or not self.cred.valid:
            if self.cred and self.cred.expired and self.cred.refresh_token:
                try:
                    self.cred.refresh(Request())
                except Exception as e:
                    print(f"Token refresh failed: {e}")
                    flow = InstalledAppFlow.from_client_secrets_file(self.client_secret_file, self.scopes)
                    self.cred = flow.run_local_server(port=0)
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.client_secret_file, self.scopes)
                self.cred = flow.run_local_server(port=0)

            os.makedirs(os.path.dirname(self.cred_pickle_file), exist_ok=True)
            with open(self.cred_pickle_file, 'wb') as token:
                pickle.dump(self.cred, token)

        return self.cred
    # 列出相簿包含共享相簿
    def list_albums(self):
        if not self.cred:
            raise ValueError("Credentials not available. Please authenticate first.")

        headers = {'Authorization': f"Bearer {self.cred.token}"}
        albums = []
        next_page_token = None

        while True:
            params = {}
            if next_page_token:
                params['pageToken'] = next_page_token

            try:
                response = requests.get(f"{self.base_url}/albums", headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                albums.extend(data.get('albums', []))
                next_page_token = data.get('nextPageToken')
                if not next_page_token:
                    break
            except requests.exceptions.RequestException as e:
                print(f"API request failed: {e}")
                break

        return albums
    
    # List and download media items from the selected album
    def list_media_items_in_album(self, album_id):

        if not self.cred:
            raise ValueError("Credentials not available. Please authenticate first.")

        headers = {'Authorization': f"Bearer {self.cred.token}"}
        media_items = []
        next_page_token = None

        while True:
            payload = {"albumId": album_id}
            if next_page_token:
                payload["pageToken"] = next_page_token

            try:
                response = requests.post(f"{self.base_url}/mediaItems:search",
                                         headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                media_items.extend(data.get('mediaItems', []))
                next_page_token = data.get('nextPageToken')
                if not next_page_token:
                    break
            except requests.exceptions.RequestException as e:
                print(f"API request failed: {e}")
                break

        return media_items

    def download_media_items(self, media_items, download_path='./downloads'):

        if not os.path.exists(download_path):
            os.makedirs(download_path)
        icount = 0
        for item in media_items:
            try:
                file_name = item['filename']
                base_url = item['baseUrl']
                download_url = f"{base_url}=d"  # Append '=d' to download original quality

                file_Noextension, file_extension = os.path.splitext(file_name)
                file_extension = file_extension.upper()

                sCreation_time = item['mediaMetadata'].get('creationTime', None)
                if sCreation_time:  
                    creation_time = datetime.fromisoformat(sCreation_time.replace("Z", "+00:00"))
                    creation_timestamp = creation_time.timestamp()
                    # 將時間戳轉換為 datetime 物件，再次轉為避免時間錯誤
                    creation_time = datetime.fromtimestamp(creation_timestamp)                   
                    new_file_name = f"IMG_{creation_time.strftime('%Y%m%d_%H%M%S')}{file_extension}"
                else:
                  new_file_name = file_name

                file_path = os.path.join(download_path, new_file_name)
              
                # Skip download if file already exists
                if os.path.exists(file_path):
                    print(f"File already exists: {file_name}. Skipping download. ")
                    continue

                response = requests.get(download_url)
                response.raise_for_status()

                if not file_extension in ['.JPG', '.HEIC']:
                     continue

                # 儲存檔案
                with open(file_path, 'wb') as f:
                # 寫入二進位資料
                    f.write(response.content)

                print(f"Downloaded: {file_name} ") 

                # 更改檔案修改時間
                if sCreation_time:               
                    os.utime(file_path, (creation_timestamp, creation_timestamp))
                    # print(f"Set modification time for {file_name} to {creation_time}")

            except Exception as e:
                print(f"Failed to download {file_name}: {e} ")