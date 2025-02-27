import os
import csv
import requests
import gspread
import re
import pillow_heif
from PIL import Image
from oauth2client.service_account import ServiceAccountCredentials

# Define paths
STAVE_FETCHER_DIR = os.path.dirname(os.path.abspath(__file__))  # Stave-Fetcher directory
DATA_DIR = os.path.join(STAVE_FETCHER_DIR, "Data")  # Keep Data directory inside Stave-Fetcher
LAST_TIMESTAMP_FILE = os.path.join(STAVE_FETCHER_DIR, "last_timestamp.txt")  # Store timestamp inside Stave-Fetcher
CREDENTIALS_PATH = os.path.join(os.path.dirname(STAVE_FETCHER_DIR), "credentials.json")  # Stave-Project root

SHEET_NAME = "Copy of Independent Stave Company Data Collection (Responses)"  # Update with actual name

# Ensure the data directory exists inside Stave-Fetcher
os.makedirs(DATA_DIR, exist_ok=True)

def authenticate_google_sheets(credentials_path, sheet_name):
    """Authenticate and access Google Sheets."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
    client = gspread.authorize(creds)
    return client.open(sheet_name).sheet1

def read_last_timestamp():
    """Read the last processed timestamp from file."""
    if os.path.exists(LAST_TIMESTAMP_FILE):
        with open(LAST_TIMESTAMP_FILE, "r") as file:
            return file.read().strip()
    return None  # No timestamp file means all data is new

def write_last_timestamp(timestamp):
    """Update the last processed timestamp in file."""
    if timestamp:
        with open(LAST_TIMESTAMP_FILE, "w") as file:
            file.write(timestamp)

def convert_drive_link(view_url):
    """Convert Google Drive share link to direct download link."""
    if "drive.google.com" in view_url:
        if "id=" in view_url:
            file_id = view_url.split("id=")[-1]
            return f"https://drive.google.com/uc?export=download&id={file_id}"
        elif "/file/d/" in view_url:
            file_id = view_url.split("/file/d/")[1].split("/")[0]
            return f"https://drive.google.com/uc?export=download&id={file_id}"
    return view_url  # Return the original if it's not a Drive link

def fetch_sheet_data(sheet, last_timestamp):
    """Retrieve only new rows from Google Sheets, sorted by timestamp."""
    data = sheet.get_all_records()
    extracted_data = []

    for row in data:
        timestamp = str(row.get("Timestamp", "")).strip() if row.get("Timestamp") else ""
        image_url = str(row.get("Upload Stave Pallet Photo", "")).strip() if row.get("Upload Stave Pallet Photo") else ""
        stave_count = str(row.get("Enter Stave Count", "")).strip() if row.get("Enter Stave Count") else ""

        # Convert Google Drive link to direct download link
        image_url = convert_drive_link(image_url)

        # Skip if last_timestamp exists and row is older or empty values exist
        if last_timestamp and timestamp <= last_timestamp:
            continue

        if timestamp and image_url and stave_count:
            extracted_data.append((timestamp, image_url, stave_count))

    # Sort by timestamp to ensure correct processing order
    extracted_data.sort(key=lambda x: x[0])

    return extracted_data

def sanitize_filename(filename):
    """Sanitize filename by replacing invalid characters."""
    return re.sub(r'[\/:*?"<>|]', '-', filename)  # Replace / and other special chars

def convert_heif_to_jpeg(file_path):
    """Convert HEIF/HEIC images to JPEG if needed."""
    try:
        heif_file = pillow_heif.open_heif(file_path)
        img = heif_file.to_pil()
        jpg_path = file_path.rsplit(".", 1)[0] + ".jpg"
        img.save(jpg_path, "JPEG", quality=95)
        os.remove(file_path)  # Delete the original HEIF file
        print(f"✅ Converted HEIF → JPEG: {jpg_path}")
        return jpg_path
    except Exception as e:
        print(f"❌ HEIF conversion failed: {file_path} | Error: {e}")
        return None

def download_image(image_url, save_path):
    """Download image from a given URL and save it locally."""
    try:
        response = requests.get(image_url, stream=True, timeout=10)
        if response.status_code == 200:
            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            print(f"✅ Downloaded: {save_path}")

            # Check if the image is HEIF and convert it
            if save_path.lower().endswith((".heic", ".heif")):
                converted_path = convert_heif_to_jpeg(save_path)
                return converted_path if converted_path else save_path  # Return the new JPEG path if conversion succeeded

            return save_path
        else:
            print(f"❌ Failed to download {image_url}: HTTP {response.status_code}")
            return None
    except requests.exceptions.Timeout:
        print(f"⚠️ Timeout error: Skipping {image_url}")
    except Exception as e:
        print(f"⚠️ Error downloading {image_url}: {e}")
    return None

def main():
    """Main function to fetch new data and download images."""
    sheet = authenticate_google_sheets(CREDENTIALS_PATH, SHEET_NAME)
    last_timestamp = read_last_timestamp()

    data = fetch_sheet_data(sheet, last_timestamp)
    
    if not data:
        print("✅ No new images to download. Exiting.")
        return

    csv_log_path = os.path.join(DATA_DIR, "stave_data_log.csv")

    with open(csv_log_path, mode='a', newline='') as file:  # Append mode to keep previous logs
        writer = csv.writer(file)
        if os.stat(csv_log_path).st_size == 0:
            writer.writerow(["Timestamp", "Filename", "Stave Count"])  # Write header if file is empty

        latest_timestamp = None  # Initialize latest_timestamp correctly

        for timestamp, image_url, stave_count in data:
            # Sanitize timestamp for filename
            safe_timestamp = sanitize_filename(timestamp)
            filename = f"{safe_timestamp}_{stave_count}.jpg"
            save_path = os.path.join(DATA_DIR, filename)

            saved_image = download_image(image_url, save_path)
            if saved_image:  # Log only successfully downloaded images
                writer.writerow([timestamp, os.path.basename(saved_image), stave_count])

            latest_timestamp = timestamp  # Update latest timestamp

    # Save latest timestamp after processing all new entries
    if latest_timestamp:
        write_last_timestamp(latest_timestamp)

    print(f"✅ Download completed. Data log saved at {csv_log_path}")

if __name__ == "__main__":
    main()
