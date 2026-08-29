import os
import io
import json
import glob
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# 1. Setup Drive API
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
FOLDER_ID = '12Mejt1hgFK6MNjiVdhVGTL6413kX726C'

creds_json = os.environ.get('GDRIVE_SERVICE_ACCOUNT_KEY')
creds_dict = json.loads(creds_json)
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
service = build('drive', 'v3', credentials=creds)

# 2. Query for the most recently modified .xlsx file in the folder
query = f"'{FOLDER_ID}' in parents and mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' and trashed=false"
results = service.files().list(
    q=query,
    orderBy='modifiedTime desc',
    pageSize=1,
    fields="files(id, name, modifiedTime)"
).execute()

files = results.get('files', [])

if not files:
    print("No Excel files found in Google Drive folder.")
    with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
        fh.write("has_changes=false\n")
    exit(0)

latest_file = files[0]
file_id = latest_file['id']

# Dynamically set target filename or fall back to existing .xlsx file in repo
existing_xlsx = glob.glob("*.xlsx")
if existing_xlsx:
    file_name = existing_xlsx[0]  # Keeps current repo filename (e.g., Fitdays--ームさん(1).xlsx)
else:
    file_name = latest_file['name']  # Uses filename from Google Drive if none exists yet

print(f"Target Excel file: {file_name}")

# 3. Download file content into memory
request = service.files().get_media(fileId=file_id)
fh = io.BytesIO()
downloader = MediaIoBaseDownload(fh, request)
done = False
while not done:
    status, done = downloader.next_chunk()

new_content = fh.getvalue()

# 4. Compare content with existing file
if os.path.exists(file_name):
    with open(file_name, 'rb') as f:
        existing_content = f.read()
    if existing_content == new_content:
        print("No changes detected in Google Drive file. Exiting.")
        with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
            fh.write("has_changes=false\n")
        exit(0)

# 5. Overwrite file with new content
with open(file_name, 'wb') as f:
    f.write(new_content)

print(f"Updated {file_name} from Google Drive.")
with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
    fh.write("has_changes=true\n")
