# LinkedIn Profile PDF Downloader
An automated LinkedIn scraper that downloads LinkedIn profiles as PDFs. The script offers two main modes: bulk dataset collection from your network and individual profile downloads.LinkedIn Profile PDF Downloader
This script collects and downloads LinkedIn profiles (as PDFs) from the **“People you may know”** suggestion list.

---

## ⚙️ How It Works
- **Cookie-based Authentication**: On first run, you log in manually to LinkedIn in Chrome. The script saves your session cookies to `cookies/linkedin_cookies.pkl` for automatic login on subsequent runs.
- **Automated PDF Generation**: Uses LinkedIn's native "Save to PDF" feature to download profile data.
- **Smart Profile Detection**: Automatically finds and collects LinkedIn profile URLs from your network suggestions.
- **Retry Logic**: Built-in retry mechanism for failed downloads to ensure maximum success rate.

---

## 🎯 Features
The script provides an interactive menu with three options:

### 1. Collect Dataset from Network
- Navigates to LinkedIn's "People you may know" section
- Automatically clicks "Show all suggestions" if available
- Allows manual scrolling to load more profiles (up to 1000)
- Extracts and deduplicates profile URLs
- Downloads each profile as PDF with progress tracking

### 2. Download Specific User Profile
- Prompts for individual LinkedIn profile URLs
- Validates URL format (must contain 'linkedin.com/in/')
- Downloads the specified profile as PDF
- Supports multiple downloads in one session

### 3. Exit
- Safely closes the browser and terminates the script

---

## 📂 Output Structure
```
SocialHook/
├── cookies/
│   └── linkedin_cookies.pkl          # Saved login session
├── download/
│   └── linkedin_downloads/           # All PDF downloads
│       ├── Profile.pdf
│       ├── Profile (1).pdf
│       └── ...
└── linkedin.py                       # Main script
```


## 🧩 Installation
- Create a virtual environment
- Install the required libraries
- pip install -r requirements.txt


# Instagram Scraper
Upcoming
# Github Scraper
Upcoming
# X Scraper
Upcoming