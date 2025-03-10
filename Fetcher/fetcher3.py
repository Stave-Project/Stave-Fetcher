import os
import requests
import gspread
import re
import logging
import time
from urllib.parse import urlparse
from oauth2client.service_account import ServiceAccountCredentials
import pillow_heif
from pillow_heif import register_heif_opener
from PIL import Image
from google.oauth2 import service_account
from google.auth.transport.requests import Request

register_heif_opener()

# Paths
STAVE_FETCHER_DIR = os.path.dirname(os.path.abspath(__file__))  # Directory of this script
DATA_DIR = os.path.join(STAVE_FETCHER_DIR, "Data")              # Main data folder
LAST_TIMESTAMP_FILE = os.path.join(STAVE_FETCHER_DIR, "last_timestamp.txt")
LAST_DOWNLOADED_FILE = os.path.join(STAVE_FETCHER_DIR, "last_downloaded.txt")
FAILED_DOWNLOADS_FILE = os.path.join(STAVE_FETCHER_DIR, "failed_downloads.txt")
CREDENTIALS_PATH = "/Users/boncui/Desktop/Projects/Stave Project/Stave-Fetcher/credentials.json"

SHEET_NAME = "Copy of Independent Stave Company Data Collection (Responses)"
MAX_RETRIES = 5  # Maximum retry attempts for failed downloads

# Ensure the Data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(message)s')


def authenticate_google_sheets(credentials_path, sheet_name):
    """Authenticates and opens a Google Sheet (first tab)."""
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
    client = gspread.authorize(creds)
    return client.open(sheet_name).sheet1


def get_google_drive_token():
    """Retrieve a fresh OAuth token for Google Drive API requests."""
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_PATH,
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    creds.refresh(Request())
    return creds.token


def convert_drive_link(view_url):
    """Convert a Google Drive share link to a direct download link, if applicable."""
    if "drive.google.com" in view_url:
        if "id=" in view_url:
            file_id = view_url.split("id=")[-1]
        elif "/file/d/" in view_url:
            file_id = view_url.split("/file/d/")[1].split("/")[0]
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return view_url


def get_file_extension(file_path_or_url):
    """Extract the correct file extension from a URL or local file path."""
    parsed_url = urlparse(file_path_or_url)
    _, ext = os.path.splitext(parsed_url.path)
    return ext.lower().lstrip(".") if ext else "jpg"


def sanitize_filename(filename):
    """Replace invalid filename characters with a dash."""
    return re.sub(r'[\\/:*?"<>|]', '-', filename)


def save_last_successful_download(file_name):
    """Ensure the last saved filename is always stored as JPG (not HEIC)."""
    normalized_name = file_name.rsplit('.', 1)[0] + ".jpg"  # Convert to JPG
    with open(LAST_DOWNLOADED_FILE, "w") as f:
        f.write(normalized_name)

def get_last_successful_download():
    """Retrieve the last successfully processed file from last_downloaded.txt."""
    if os.path.exists(LAST_DOWNLOADED_FILE):
        with open(LAST_DOWNLOADED_FILE, "r") as f:
            return f.read().strip()  # Read and return the last successful download
    return None  # Return None if no record exists


def log_failed_download(image_url):
    """Log failed downloads to a separate file."""
    with open(FAILED_DOWNLOADS_FILE, "a") as f:
        f.write(image_url + "\n")


def download_image(image_url, stave_count):
    """Download image from Google Drive and save with correct filename."""
    try:
        file_id = image_url.split("id=")[-1]
        metadata_url = f"https://www.googleapis.com/drive/v3/files/{file_id}?fields=name"
        headers = {"Authorization": f"Bearer {get_google_drive_token()}"}

        metadata_response = requests.get(metadata_url, headers=headers)
        if metadata_response.status_code != 200:
            logging.error(f"❌ Failed to fetch filename for {image_url}")
            return None

        file_name = metadata_response.json().get("name", "UnknownFile")
        file_ext = get_file_extension(file_name)
        file_name = sanitize_filename(file_name)
        save_path = os.path.join(DATA_DIR, f"{file_name}_{stave_count}.{file_ext}")

        response = requests.get(image_url, stream=True, timeout=10)
        if response.status_code == 200:
            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)

            print(f"✅ Downloaded {file_name} -> {save_path}")
            return save_path

        else:
            logging.error(f"❌ Download failed with status {response.status_code}: {image_url}")

    except Exception as e:
        logging.error(f"❌ Download failed: {image_url} | {e}")

    return None


def convert_heic_to_jpg(heic_path):
    """Convert HEIC to JPG and delete the original HEIC file."""
    try:
        heif_file = pillow_heif.read_heif(heic_path)
        image = Image.frombytes(heif_file.mode, heif_file.size, heif_file.data, "raw", heif_file.mode, heif_file.stride)
        jpg_path = heic_path.rsplit('.', 1)[0] + ".jpg"
        image.save(jpg_path, "JPEG")
        os.remove(heic_path)
        print(f"✅ Converted HEIC -> JPG: {jpg_path}")
        return jpg_path
    except Exception as e:
        logging.error(f"❌ HEIC to JPG conversion failed: {heic_path} | {e}")
        return heic_path

def fetch_sheet_data(sheet, last_timestamp):
    all_rows = sheet.get_all_records()

    print("\nDEBUG: Detected column headers ->", sheet.row_values(1))
    print("DEBUG: Raw data from sheet ->", all_rows[:5])

    extracted_data = []

    for row in all_rows:
        timestamp = str(row.get("Timestamp", "")).strip()
        image_url = str(row.get("Upload Stave Pallet Photo", "")).strip()
        stave_count = str(row.get("Enter Stave Count", "")).strip()

        print(f"DEBUG: Processing row -> Timestamp: {timestamp}, URL: {image_url}, Stave Count: {stave_count}")

        image_url = convert_drive_link(image_url)

        if last_timestamp and timestamp <= last_timestamp:
            print(f"DEBUG: Skipping {timestamp} (Older than last processed timestamp: {last_timestamp})")
            continue

        if timestamp and image_url and stave_count:
            extracted_data.append((timestamp, image_url, stave_count))

    print(f"DEBUG: Extracted {len(extracted_data)} new images for processing.\n")
    extracted_data.sort(key=lambda x: x[0])
    return extracted_data

def process_images():
    sheet = authenticate_google_sheets(CREDENTIALS_PATH, SHEET_NAME)
    last_downloaded = get_last_successful_download()

    new_data = fetch_sheet_data(sheet, None)
    if not new_data:
        logging.info("✅ No new images to download.")
        return

    start_processing = False if last_downloaded else True

    for timestamp, image_url, stave_count in new_data:
        retry_attempts = 0
        file_name = f"{sanitize_filename(image_url.split('id=')[-1])}_{stave_count}.jpg"

        if last_downloaded and file_name == last_downloaded:
            start_processing = True  # Begin processing after this file

        if not start_processing:
            print(f"⏩ Skipping already processed file: {file_name}")
            continue

        while retry_attempts < MAX_RETRIES:
            downloaded_file = download_image(image_url, stave_count)
            if downloaded_file:
                break  # Exit loop if download succeeds
            print(f"🔄 Retrying failed download: {file_name} (Attempt {retry_attempts+1}/{MAX_RETRIES})")
            retry_attempts += 1
            time.sleep(30)  # Wait 30 seconds before retrying

        if downloaded_file and get_file_extension(downloaded_file) in ["heic", "heif"]:
            downloaded_file = convert_heic_to_jpg(downloaded_file)

        if downloaded_file:
            save_last_successful_download(file_name)  # Save only if successfully processed
        else:
            log_failed_download(image_url)  # Log failed file

    logging.info("✅ Image processing completed.")


if __name__ == "__main__":
    process_images()
