from Google_Photos_API import GooglePhotosApi 

# Initialize and authenticate
google_photos_api = GooglePhotosApi()
creds = google_photos_api.run_local_server()

# 列出相簿包含共享相簿
albums = google_photos_api.list_albums()
# for album in albums:
#     print(f"Album: {album['title']} (ID: {album['id']})")

# print("Available albums:")

for i, album in enumerate(albums):
    print(f"{i + 1}. {album['title']} (ID: {album['id']})")

# Select an album to download
album_index = int(input("Enter the album number to download: ")) - 1
selected_album = albums[album_index]
album_id = selected_album['id']
album_title = selected_album['title']
print(f"Downloading album: {album_title}")

# List and download media items from the selected album
media_items = google_photos_api.list_media_items_in_album(album_id)
google_photos_api.download_media_items(media_items, 'downloads/' + album_title)
print(f"Downloaded all media items from album: {album_title}")