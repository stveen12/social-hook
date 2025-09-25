# SocialHook - Social Media Profile Scraper Suite
A collection of automated social media scrapers for LinkedIn and Instagram profile data extraction.

---

## 🧩 Installation
- Create a virtual environment
- Install the required libraries 
`pip install -r requirement.txt`

---

## 📂 Output Structure
```
SocialHook/
├── cookies/
│   ├── linkedin_cookies.json
│   └── instagram_cookies.json
├── downloads/
│   ├── linkedin_downloads/           # LinkedIn PDFs
│   └── instagram_downloads/          # Instagram data
├── linkedin_downloadpdf.py
├── instagram.py
└── requirement.txt
```

---

## 📘 LinkedIn Profile PDF Scraper
Downloads LinkedIn profiles as PDFs from your network and individual profiles.

### ⚙️ How It Works
- On first run, log in manually to LinkedIn in Chrome
- Session cookies saved to `cookies/linkedin_cookies.json` for future runs
- Uses LinkedIn's native "Save to PDF" feature
- Built-in retry mechanism for failed downloads

### 🎯 Features
Interactive menu with three options:

1. **Collect dataset from my network**
2. **Download specific user profile** 
3. **Exit**

### 🖱️ Usage Steps
1. Run `python linkedin_downloadpdf.py`
2. Log in to LinkedIn (first time only)
3. Choose your option from the menu
4. For bulk collection: scroll to load profiles, then press Enter
5. For individual profiles: enter LinkedIn URLs one by one

---

## 📸 Instagram Bio Scraper
Extracts bio data and profile information from Instagram profiles.

### ⚙️ How It Works
- Log in manually to Instagram on first run
- Session cookies saved to `cookies/instagram_cookies.json`
- Scrapes username and bio text from profiles
- Saves data to JSON file for analysis

### 🖱️ Usage Steps
1. Run `python instagram.py`
2. Log in to Instagram (first time only)
3. Enter number of profiles to scrape
4. Input Instagram profile URLs one by one
5. Data saved to `downloads/instagram_downloads/instagram_biodata.json`

### 📊 Output Format
```
{'username': 'profile_name', 'bio': 'Bio text content...'}
```

---

##  Upcoming
- **GitHub Scraper**
- **X (Twitter) Scraper**