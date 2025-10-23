import os
import requests
import py7zr

def download_large_data():
    url = "https://drive.google.com/file/d/1F8vWwhbVB6z8rE8fSwGF1WmIhgfykMRB/view?usp=drive_link"  
    archive_path = os.path.join(os.path.expanduser("~"), "DSE3Installer.7z")
    extract_path = os.path.join(os.path.expanduser("~"), "wrapper")

    if not os.path.exists(extract_path):
        print("Downloading large 7z archive from Google Drive...")
        download_file_from_google_drive(url, archive_path)
        print("Extracting 7z archive...")
        with py7zr.SevenZipFile(archive_path, mode='r') as archive:
            archive.extractall(path=extract_path)
        os.remove(archive_path)
        print("Download and extraction completed.")
    else:
        print("Data already available.")

def download_file_from_google_drive(file_url, destination):
    file_id = None
    if "id=" in file_url:
        file_id = file_url.split("id=")[1].split("&")[0]
    elif "/d/" in file_url:
        file_id = file_url.split("/d/")[1].split("/")[0]
    else:
        raise ValueError("Invalid Google Drive link")

    URL = "https://drive.google.com/file/d/1F8vWwhbVB6z8rE8fSwGF1WmIhgfykMRB/view?usp=drive_link"

    session = requests.Session()

    response = session.get(URL, params={'id': file_id}, stream=True)
    token = get_confirm_token(response)

    if token:
        params = {'id': file_id, 'confirm': token}
        response = session.get(URL, params=params, stream=True)

    save_response_content(response, destination)

def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value
    return None

def save_response_content(response, destination):
    CHUNK_SIZE = 32768
    with open(destination, "wb") as f:
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk:
                f.write(chunk)
