# SocialHook - Social Media Profile Scraper Suite
A collection of automated social media scrapers for LinkedIn, Instagram, and Twitter/X profile data extraction.

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
│   ├── instagram_cookies.json
│   └── twitter_cookies.json
├── downloads/
│   ├── linkedin_downloads/           # LinkedIn PDFs
│   ├── instagram_downloads/          # Instagram data
│   └── twitter_downloads/            # Twitter data
├── linkedin_downloadpdf.py
├── instagram.py
├── xtwitter.py
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

### 🔧 Selenium Data Extraction Process
1. **Navigate to profile** → Load the LinkedIn profile page
2. **Click "More actions" button** → Find button with `aria-label='More actions'`
3. **Click "Save to PDF"** → Locate and click the PDF download option from dropdown
4. **Automatic download** → LinkedIn generates and downloads the PDF to specified folder

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

## 📸 Instagram Profile & Posts Scraper
Extracts bio data and post captions from Instagram profiles.

### ⚙️ How It Works
- Log in manually to Instagram on first run
- Session cookies saved to `cookies/instagram_cookies.json`
- Scrapes username, bio text, and post captions from profiles
- Saves data to JSON file for analysis

### 🔧 Selenium Data Extraction Process
1. **Navigate to profile** → Load the Instagram profile page
2. **Extract bio data** → Find profile picture, then locate the third `<section>` tag after it to get bio text
3. **Access posts** → Click the first post using `div._aagw` selector
4. **Extract captions** → Get post caption from `h1._ap3a._aaco._aacu._aacx._aad7._aade` element
5. **Navigate posts** → Click next post using `button._abl-` to scrape up to 5 post captions per profile

### 🖱️ Usage Steps
1. Run `python instagram.py`
2. Log in to Instagram (first time only)
3. Enter number of profiles to scrape
4. Input Instagram profile URLs one by one
5. Data saved to `downloads/instagram_downloads/instagram_biodata.json`

### 📊 Output Format
```json
{
  "username": "profile_name", 
  "bio": "Bio text content...",
  "captions": [
    "First post caption text...",
    "Second post caption text...",
    "Third post caption text..."
  ]
}
```

---

## 🐦 Twitter/X Profile & Posts Scraper
Extracts bio data and post captions from Twitter/X profiles.

### ⚙️ How It Works
- Log in manually to Twitter/X on first run
- Session cookies saved to `cookies/twitter_cookies.json`
- Scrapes username, bio text, and post captions from profiles
- Saves data to JSON file for analysis

### 🔧 Selenium Data Extraction Process
1. **Navigate to profile** → Load the Twitter/X profile page
2. **Extract bio data** → Find container `div.css-175oi2r.r-3pj75a.r-ttdzmv.r-1ifxtd0`, then locate the third child div and extract bio text from nested span
3. **Access posts** → Use XPath to target posts by index `/html/body/div[1]/div/div/div[2]/main/div/div/div/div/div/div[3]/div/div/section/div/div/div[{post_index}]`
4. **Extract captions** → Get post caption from `div.css-146c3p1.r-bcqeeo.r-1ttztb7.r-qvutc0.r-37j5jr.r-a023e6.r-rjixqe.r-16dba41.r-bnwqim > span`
5. **Navigate posts** → Scroll down and increment post index to scrape up to 5 post captions per profile

### 🖱️ Usage Steps
1. Run `python xtwitter.py`
2. Log in to Twitter/X (first time only)
3. Enter number of profiles to scrape
4. Input Twitter/X profile URLs one by one
5. Data saved to `downloads/twitter_downloads/twitter_biodata.json`

### 📊 Output Format
```json
{
  "username": "profile_name", 
  "bio": "Bio text content...",
  "captions": [
    "First post caption text...",
    "Second post caption text...",
    "Third post caption text..."
  ]
}
```

---

## 🔮 Upcoming
- **GitHub Scraper**