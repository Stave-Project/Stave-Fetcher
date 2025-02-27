import os
import requests
import gspread
import re
import logging
from urllib.parse import urlparse
import mimetypes
from concurrent.futures import ThreadPoolExecutor, as_completed
from oauth2client.service_account import ServiceAccountCredentials

# 🏠 Define Paths
STAVE_FETCHER_DIR = os.path.dirname(os.path.abspath(__file__))  # Stave-Fetcher directory
DATA_DIR = os.path.join(STAVE_FETCHER_DIR, "Data")  # Main data folder
LAST_TIMESTAMP_FILE = os.path.join(STAVE_FETCHER_DIR, "last_timestamp.txt")
CREDENTIALS_PATH = os.path.join(os.path.dirname(STAVE_FETCHER_DIR), "credentials.json")

SHEET_NAME = "Copy of Independent Stave Company Data Collection (Responses)"

# 📂 Ensure the Data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(message)s')


# 📜 **Helper Functions**
def authenticate_google_sheets(credentials_path, sheet_name):
    """Authenticate and access Google Sheets."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
    client = gspread.authorize(creds)
    return client.open(sheet_name).sheet1


def get_file_extension(file_path_or_url):
    """Extracts the correct file extension from a URL or local file path."""
    parsed_url = urlparse(file_path_or_url)
    ext = os.path.splitext(parsed_url.path)[1].lower().lstrip(".")
    return ext if ext else "jpg"  # Default fallback if extension is missing


def convert_drive_link(view_url):
    """Convert Google Drive share link to direct download link."""
    if "drive.google.com" in view_url:
        if "id=" in view_url:
            file_id = view_url.split("id=")[-1]
        elif "/file/d/" in view_url:
            file_id = view_url.split("/file/d/")[1].split("/")[0]
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return view_url


def sanitize_filename(filename):
    """Sanitize filename by replacing invalid characters."""
    return re.sub(r'[\/:*?"<>|]', '-', filename)


def create_type_directories():
    """Create separate folders for each image type inside the Data directory."""
    folders = ["JPEG", "PNG", "HEIC", "TIFF", "OTHERS"]
    for folder in folders:
        os.makedirs(os.path.join(DATA_DIR, folder), exist_ok=True)


def move_file_to_type_folder(file_path):
    """Move file to its corresponding type folder."""
    file_extension = get_file_extension(file_path)
    type_folders = {
        "jpg": "JPEG",
        "jpeg": "JPEG",
        "png": "PNG",
        "heic": "HEIC",
        "heif": "HEIC",
        "tiff": "TIFF",
        "tif": "TIFF",
    }
    folder = type_folders.get(file_extension, "OTHERS")
    new_path = os.path.join(DATA_DIR, folder, os.path.basename(file_path))
    os.rename(file_path, new_path)
    return new_path


def download_image(image_url, save_path):
    """Download image from URL and save it locally."""
    try:
        response = requests.get(image_url, stream=True, timeout=10)
        if response.status_code == 200:
            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            return save_path
    except Exception as e:
        logging.error(f"❌ Download failed: {image_url} | {e}")
    return None


def fetch_sheet_data(sheet, last_timestamp):
    """Retrieve only new rows from Google Sheets, sorted by timestamp."""
    data = sheet.get_all_records()
    extracted_data = []

    for row in data:
        timestamp = str(row.get("Timestamp", "")).strip()
        image_url = str(row.get("Upload Stave Pallet Photo", "")).strip()
        stave_count = str(row.get("Enter Stave Count", "")).strip()

        image_url = convert_drive_link(image_url)

        if last_timestamp and timestamp <= last_timestamp:
            continue

        if timestamp and image_url and stave_count:
            extracted_data.append((timestamp, image_url, stave_count))

    extracted_data.sort(key=lambda x: x[0])
    return extracted_data


def process_images():
    """Fetch, download, and categorize images from Google Sheets."""
    sheet = authenticate_google_sheets(CREDENTIALS_PATH, SHEET_NAME)
    last_timestamp = None
    data = fetch_sheet_data(sheet, last_timestamp)

    if not data:
        logging.info("✅ No new images to download.")
        return

    create_type_directories()

    for timestamp, image_url, stave_count in data:
        ext = get_file_extension(image_url)
        filename = f"{sanitize_filename(timestamp)}_{stave_count}.{ext}"
        save_path = os.path.join(DATA_DIR, filename)

        downloaded_file = download_image(image_url, save_path)
        if downloaded_file:
            # Move to the correct type folder
            move_file_to_type_folder(downloaded_file)
            last_timestamp = timestamp

    if last_timestamp:
        with open(LAST_TIMESTAMP_FILE, "w") as file:
            file.write(last_timestamp)

    logging.info("✅ Image processing completed.")


# 🎯 Run the script
if __name__ == "__main__":
    process_images()
