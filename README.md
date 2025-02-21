# Stave Fetcher Setup Guide

## 📌 Overview
This guide will walk you through setting up and running the **Stave Fetcher** project. Follow the steps carefully to ensure everything works smoothly.

---

## 🛠 Prerequisites
- A **Google Cloud Console** account
- Access to the **Independent Stave Company Data Collection (Responses)** Google Sheet
- Python 3 installed on your system
- Git installed on your system

---

## 🚀 Setup Instructions

### **1️⃣ Clone the Repository**
```sh
# Clone the repo to your local machine
git clone <your-repository-url>
cd Stave-Fetcher
```

### **2️⃣ Make a Copy of the Data Sheet**
1. Open **Google Sheets** and locate the file named **"Independent Stave Company Data Collection (Responses)"**.
2. Click on **File > Make a Copy**.
3. Rename the copy to anything you prefer.

### **3️⃣ Set Up Google Cloud Console**
1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. **Create a New Project**:
   - Name it **Stave Project**.
3. **Enable APIs**:
   - Navigate to **APIs & Services** > **Credentials**.
   - Click **Create Credentials** > **Service Account**.
   - Name it **Stave Fetcher** and add a description.
   - Set the **Role** to **Editor**.
4. **Download the API Key**:
   - Click on the service account you just created.
   - Go to the **Keys** tab.
   - Click **Add Key > JSON**.
   - Download the JSON file.
   - Rename it to **credentials.json**.
   - Move it to the **Stave-Fetcher** folder.

### **4️⃣ Grant Access to Google Sheets**
1. Open the **credentials.json** file.
2. Copy the **client_email** field.
3. Open the **Google Sheet copy** you made.
4. Click **Share** and **paste the client email**.
5. Set the permission to **Editor**.

### **5️⃣ Update `stave-fetcher.py`**
1. Open the file `stave-fetcher.py`.
2. Find where the Google Sheet is referenced.
3. Replace it with the name of the **copy** of the sheet you created.

### **6️⃣ Set Up Virtual Environment**
```sh
# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate   # On macOS/Linux
venv\Scripts\activate     # On Windows
```

### **7️⃣ Install Dependencies**
```sh
pip install -r requirements.txt
```

### **8️⃣ Run the Script**
```sh
python3 stave-fetcher.py
```

---

## 🎯 Troubleshooting
- If something doesn’t work as expected, **double-check** the steps above.
- Ensure the **client_email** has been added as an **Editor** to the Google Sheet.
- Confirm that the **Google API key** is correctly placed in `credentials.json`.
- Make sure the **virtual environment** is activated before running the script.

🚀 **If you encounter any issues, contact [Your Name] for assistance.**

