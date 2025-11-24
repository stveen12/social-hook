import os
import time
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


COOKIES_FILE = "credentials/linkedin_cookies.json"
DOWNLOAD_DIR = str(Path(__file__).parent / "data" / "linkedin_pdfs_data")
MAX_PROFILES = 1000
WAIT_SEC = 15

def show_menu():
    print("\n" + "="*50)
    print("LinkedIn Profile Scraper")
    print("="*50)
    print("1. Collect dataset from my network")
    print("2. Download specific user profile")
    print("3. Exit")
    print("="*50)
    
    while True:
        choice = input("Select an option (1-3): ").strip()
        if choice in ['1', '2', '3']:
            return choice
        print("Invalid choice. Please enter 1, 2, or 3.")


def setup_driver():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(COOKIES_FILE), exist_ok=True)
    
    options = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    options.add_experimental_option("prefs", prefs)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, WAIT_SEC)
    driver.maximize_window()
    
    return driver, wait


def login_with_cookies(driver):
    driver.get("https://www.linkedin.com")
    time.sleep(2)

    if os.path.exists(COOKIES_FILE):
        with open(COOKIES_FILE, "r", encoding="utf-8") as f:
            cookies = json.load(f)
            for c in cookies:
                if "domain" in c and c["domain"]:
                    driver.add_cookie(c)
                else:
                    c["domain"] = ".linkedin.com"
                    driver.add_cookie(c)
        driver.refresh()
        time.sleep(2)
    else:
        input("No cookies yet. Log in in the opened window, then press Enter here to save cookies...")
        with open(COOKIES_FILE, "w", encoding="utf-8") as f:
            json.dump(driver.get_cookies(), f, indent=4, ensure_ascii=False)
        print("Cookies saved.")


def click_more_then_save_pdf(driver, wait):
    
    more_buttons = wait.until(
        EC.presence_of_all_elements_located((By.XPATH, "//button[@aria-label='More actions']"))
    )
    
    more_buttons = [b for b in more_buttons if b.is_displayed()]
    if not more_buttons:
        raise Exception("No visible 'More actions' button found")
    more_btn = more_buttons[-1]

    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", more_btn)
    time.sleep(0.3)
    driver.execute_script("arguments[0].click();", more_btn)

    wait.until(lambda d: more_btn.get_attribute("aria-expanded") == "true")

    def find_visible_pdf():
        cands = driver.find_elements(By.XPATH, "//div[@aria-label='Save to PDF']")
        cands += driver.find_elements(By.XPATH, "//*[contains(text(),'Save to PDF')]")
        cands = [el for el in cands if el.is_displayed()]
        return cands[0] if cands else None

    pdf_btn = WebDriverWait(driver, WAIT_SEC).until(lambda d: find_visible_pdf())
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", pdf_btn)
    time.sleep(0.2)
    driver.execute_script("arguments[0].click();", pdf_btn)


def collect_dataset(driver, wait):
    print("Starting dataset collection from your network...")
    
    driver.get("https://www.linkedin.com/mynetwork/")
    time.sleep(5)

    try:
        show_all_btn = WebDriverWait(driver, WAIT_SEC).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Show all suggestions for People you may know based on your recent activity']"))
        )
        driver.execute_script("arguments[0].click();", show_all_btn)
        print("Opened 'People you may know' list...")
        time.sleep(3)
    except:
        print("⚠️ Could not find 'Show all suggestions...' button. Continuing with default suggestions...")

    input(f"Scroll to load more profiles (up to {MAX_PROFILES}), then press Enter here...")

    seen = set()
    links = []
    for a in driver.find_elements(By.CSS_SELECTOR, "a[href*='linkedin.com/in/']"):
        href = a.get_attribute("href")
        if not href:
            continue
        href = href.split("?")[0]
        if "/in/" in href and href not in seen:
            seen.add(href)
            links.append(href)

    print(f"Collected {len(links)} profiles:", links[:15])

    for i, url in enumerate(links, 1):
        try:
            driver.get(url)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
            click_more_then_save_pdf(driver, wait)
            print(f"[{i}/{len(links)}] Saved PDF for: {url}")
            time.sleep(3)
        except Exception as e:
            print(f"[{i}/{len(links)}] Failed on {url}: {e}")
            try:
                time.sleep(1.5)
                click_more_then_save_pdf(driver, wait)
                print(f"[{i}/{len(links)}] Saved PDF on retry: {url}")
                time.sleep(3)
            except Exception as e2:
                print(f"[{i}/{len(links)}] Retry failed on {url}: {e2}")


def download_specific_user(driver, wait):
    print("Download specific user profile")
    print("-" * 30)
    
    while True:
        linkedin_url = input("Enter LinkedIn profile URL (or 'back' to return to menu): ").strip()
        
        if linkedin_url.lower() == 'back':
            return
            
        if not linkedin_url:
            print("Please enter a valid URL.")
            continue
            
        
        if "linkedin.com/in/" not in linkedin_url:
            print("Invalid LinkedIn profile URL. Make sure it contains 'linkedin.com/in/'")
            continue
            
        
        linkedin_url = linkedin_url.split("?")[0]
        
        try:
            print(f"Downloading profile: {linkedin_url}")
            driver.get(linkedin_url)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
            click_more_then_save_pdf(driver, wait)
            print(f"✅ Successfully saved PDF for: {linkedin_url}")
            time.sleep(2)
            
            
            another = input("Download another profile? (y/n): ").strip().lower()
            if another != 'y':
                break
                
        except Exception as e:
            print(f"❌ Failed to download {linkedin_url}: {e}")
            retry = input("Try again? (y/n): ").strip().lower()
            if retry != 'y':
                break


def main():
    driver, wait = setup_driver()
    
    try:
        login_with_cookies(driver)
        
        while True:
            choice = show_menu()
            
            if choice == '1':
                collect_dataset(driver, wait)
            elif choice == '2':
                download_specific_user(driver, wait)
            elif choice == '3':
                print("Exiting...")
                break
                
            print(f"\nPDFs saved to: {DOWNLOAD_DIR}")
            
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
