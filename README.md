# Stave Fetcher - Setup Guide

This guide will help you set up the **Stave Fetcher** tool step by step.

---

## **1. Clone the Repository**
Download the repository to your local machine:

```sh
git clone <your-repo-url>
cd Stave-Fetcher
```

---

## **2. Setup Google Sheets for Data Collection**
1. Open the Google Sheet named **"Independent Stave Company Data Collection (Responses)"**.
2. **Make a copy**:  
   - Click **File > Make a Copy**.
   - Rename the copy (e.g., **"My Stave Data Copy"**).

---

## **3. Set Up Google Cloud Console**
1. Go to **[Google Cloud Console](https://console.cloud.google.com/)** and sign in.
2. Click **Select a Project** (top-left) > **New Project**.
3. Name the project **Stave Project** and click **Create**.

---

## **4. Enable Google Sheets API**
1. In Google Cloud Console, navigate to **`APIs & Services > Library`**.
2. Search for **Google Sheets API** and enable it.

---

## **5. Create and Download API Credentials**
1. Go to **`APIs & Services > Credentials`**.
2. Click **Create Credentials > Service Account**.
3. Set:
   - **Name:** `Stave Fetcher`
   - **Description:** `API for fetching stave data`
4. Under **Role**, select **Editor**.
5. Click **Create & Continue > Done**.
6. In the **Service Accounts** tab:
   - Click on your new service account.
   - Go to the **Keys** tab.
   - Click **Add Key > Create New Key**.
   - Select **JSON format** and download it.
7. Rename the downloaded file to **`credentials.json`**.
8. Move `credentials.json` into the **Stave-Fetcher** folder.

---

## **6. Grant API Access to Google Sheets**
1. Open `credentials.json`.
2. Find the **"client_email"** field.
3. Open your **Google Sheet copy**.
4. Click **Share** and paste the **client email**.
5. Set **Editor** access and save.

---

## **7. Update the Stave Fetcher Script**
1. Open `stave-fetcher.py`.
2. Find the **Google Sheet name**.
3. **Replace it** with the name of your **Google Sheet copy**.

---

## **8. Set Up Virtual Environment and Install Dependencies**
1. Ensure Python 3 is installed.
2. Run:

```sh
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate    # Windows
```

3. Install required packages:

```sh
pip install -r requirements.txt
```

---

## **9. Run the Script**
Execute the script:

```sh
python3 stave-fetcher.py
```

---

## **10. Troubleshooting**
If you face any issues, check the following:
- Ensure **`credentials.json`** is in the correct folder.
- The **Google Sheet name** in `stave-fetcher.py` matches exactly.
- The **client email** has **editor** access to the sheet.
- Your **virtual environment** is activated before running the script.

✅ **Setup Complete!** 🎉

