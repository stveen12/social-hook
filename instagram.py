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


COOKIES_FILE = "credentials/instagram_cookies.json"
DOWNLOAD_DIR = str(Path(__file__).parent / "data" / "instagram_data")
WAIT_SEC = 15
TOTAL_POSTS_TO_SCRAPE = 5


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
    driver.get("https://www.instagram.com/")
    time.sleep(3)

    if os.path.exists(COOKIES_FILE):
        with open(COOKIES_FILE, "r", encoding="utf-8") as f:
            cookies = json.load(f)
            for c in cookies:
                if "domain" in c and c["domain"]:
                    driver.add_cookie(c)
                else:
                    c["domain"] = ".instagram.com"
                    driver.add_cookie(c)
        driver.refresh()
        time.sleep(3)
    else:
        input("No cookies yet. Log in manually in the opened browser, then press Enter here to save cookies...")
        with open(COOKIES_FILE, "w", encoding="utf-8") as f:
            json.dump(driver.get_cookies(), f, indent=4, ensure_ascii=False)
        print("Cookies saved.")

def scrape_biodata_and_posts(driver, wait, profile_url):
    driver.get(profile_url)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "header")))
    time.sleep(2)

    biodata = {"username": profile_url.rstrip("/").split("/")[-1], "bio": "", "captions": []}

    
    try:
        img = driver.find_element(By.XPATH, f"//img[contains(@alt, \"'s profile picture\")]")
        section = img.find_element(By.XPATH, "./ancestor::section[1]")
        all_sections = section.find_elements(By.XPATH, "./ancestor::header[1]/section")

        if len(all_sections) >= 4:
            bio_section = all_sections[3]
            biodata["bio"] = bio_section.text.strip().replace("\n", " ")
        else:
            biodata["bio"] = ""
    except Exception as e:
        print(f"⚠️ Error scraping bio for {profile_url}: {e}")

    
    try:
        first_post = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div._aagw")))
        driver.execute_script("arguments[0].click();", first_post)
        time.sleep(2)

        scraped = 0
        clicked_next = False  

        while scraped < TOTAL_POSTS_TO_SCRAPE:
            
            try:
                caption_el = wait.until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "h1._ap3a._aaco._aacu._aacx._aad7._aade")
                    )
                )
                caption = caption_el.text.strip().replace("\n", " ")
                biodata["captions"].append(caption)
                scraped += 1
                print(f"  📝 Post {scraped} caption: {caption[:60]}...")
            except Exception as e:
                print(f"⚠️ Could not get caption for post {scraped+1}: {e}")

            
            nav_buttons = driver.find_elements(By.CSS_SELECTOR, "button._abl-")

            if len(nav_buttons) == 1:
                
                print("ℹ️ Only one post found, stopping.")
                break
            elif len(nav_buttons) == 2:
                if not clicked_next:
                    
                    driver.execute_script("arguments[0].click();", nav_buttons[0])
                    clicked_next = True
                    time.sleep(2)
                else:
                    
                    print("ℹ️ Reached last post, stopping.")
                    break
            elif len(nav_buttons) == 3:
                
                driver.execute_script("arguments[0].click();", nav_buttons[1])
                clicked_next = True
                time.sleep(2)
            else:
                print("⚠️ Unexpected button state, stopping.")
                break

    except Exception as e:
        print(f"⚠️ Error scraping posts for {profile_url}: {e}")

    return biodata

def main():
    driver, wait = setup_driver()

    try:
        login_with_cookies(driver)

        num_users = int(input("How many Instagram users to scrape? ").strip())

        urls = []
        for i in range(num_users):
            url = input(f"Enter Instagram profile URL #{i+1}: ").strip()
            if not url.startswith("http"):
                print("Invalid URL, skipping.")
                continue
            urls.append(url)

        results = []
        for i, url in enumerate(urls, 1):
            data = scrape_biodata_and_posts(driver, wait, url)
            results.append(data)
            print(f"[{i}/{len(urls)}] ✅ Scraped: {data['username']}")

        out_file = os.path.join(DOWNLOAD_DIR, "instagram_biodata.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)

        print(f"\nAll biodata + captions saved to: {out_file}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
