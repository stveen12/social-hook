import os
import time
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager


COOKIES_FILE = "cookies/twitter_cookies.json"
DOWNLOAD_DIR = str(Path(__file__).parent / "downloads" / "twitter_downloads")
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
    
    driver.get("https://x.com/")
    time.sleep(2)

    if os.path.exists(COOKIES_FILE):
        with open(COOKIES_FILE, "r", encoding="utf-8") as f:
            cookies = json.load(f)
            for c in cookies:
                
                if "domain" not in c or not c["domain"]:
                    c["domain"] = ".x.com"
                try:
                    driver.add_cookie(c)
                except Exception:
                    
                    simple = {k: v for k, v in c.items() if k in ("name", "value", "domain", "path", "expiry", "secure", "httpOnly")}
                    try:
                        driver.add_cookie(simple)
                    except Exception as e:
                        print("⚠️ Skipped a cookie due to:", e)
        driver.refresh()
        time.sleep(3)
    else:
        
        driver.get("https://x.com/login")
        input("No cookies yet. Log in manually in the opened browser, then press Enter here to save cookies...")
        with open(COOKIES_FILE, "w", encoding="utf-8") as f:
            json.dump(driver.get_cookies(), f, indent=4, ensure_ascii=False)
        print("Cookies saved.")

def scrape_biodata(driver, wait, profile_url):
    driver.get(profile_url)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(2)

    biodata = {"username": profile_url.rstrip("/").split("/")[-1], "bio": ""}

    try:
        bio_parent = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.css-175oi2r.r-3pj75a.r-ttdzmv.r-1ifxtd0")
            )
        )
        child_divs = bio_parent.find_elements(By.XPATH, "./div")
        if len(child_divs) < 3:
            print("⚠️ Expected at least 3 child divs inside the container but found", len(child_divs))
            return biodata

        third_div = child_divs[2]

        span = None
        try:
            span = third_div.find_element(By.XPATH, ".//div/div/div//span[normalize-space(.)!='']")
        except NoSuchElementException:
            try:
                span = third_div.find_element(By.XPATH, ".//div/div//span[normalize-space(.)!='']")
            except NoSuchElementException:
                try:
                    span = third_div.find_element(By.XPATH, ".//span[normalize-space(.)!='']")
                except NoSuchElementException:
                    span = None

        if span:
            biodata["bio"] = span.text.strip().replace("\n", " ")
        else:
            print("⚠️ Could not find bio span under the 3rd div for", profile_url)

    except TimeoutException:
        print("⚠️ Timeout while waiting for profile page to load:", profile_url)
    except Exception as e:
        print(f"⚠️ Error scraping bio for {profile_url}: {e}")

    return biodata


def scrape_biodata_and_posts(driver, wait, profile_url):
    
    biodata = scrape_biodata(driver, wait, profile_url)
    biodata["captions"] = []

    scraped = 0
    post_index = 1
    time.sleep(5)
    while scraped < TOTAL_POSTS_TO_SCRAPE:
        try:
            
            post_xpath = f"/html/body/div[1]/div/div/div[2]/main/div/div/div/div/div/div[3]/div/div/section/div/div/div[{post_index}]"
            post = driver.find_element(By.XPATH, post_xpath)

            driver.execute_script("arguments[0].scrollIntoView(true);", post)
            time.sleep(1)

            try:
                
                caption_div = post.find_element(
                    By.CSS_SELECTOR,
                    "div.css-146c3p1.r-bcqeeo.r-1ttztb7.r-qvutc0.r-37j5jr.r-a023e6.r-rjixqe.r-16dba41.r-bnwqim"
                )
                span = caption_div.find_element(By.TAG_NAME, "span")
                caption = span.text.strip().replace("\n", " ")
                biodata["captions"].append(caption)
                scraped += 1
                print(f"  📝 Post {scraped} caption: {caption[:60]}...")
            except Exception as e:
                print(f"⚠️ Could not get caption for post #{post_index}: {e}")

            post_index += 1
            driver.execute_script("window.scrollBy(0, 600);")
            time.sleep(2)

        except Exception:
            print("ℹ️ No more posts found or reached end of feed.")
            break

    return biodata




def main():
    driver, wait = setup_driver()

    try:
        login_with_cookies(driver)

        num_users = int(input("How many Twitter users to scrape? ").strip())

        urls = []
        for i in range(num_users):
            url = input(f"Enter Twitter/X profile URL #{i+1}: ").strip()
            if not url.startswith("http"):
                print("Invalid URL, skipping.")
                continue
            urls.append(url)

        results = []
        for i, url in enumerate(urls, 1):
            data = scrape_biodata_and_posts(driver, wait, url)
            results.append(data)
            print(f"[{i}/{len(urls)}] ✅ Scraped: {data['username']} — bio length {len(data['bio'])}")

        out_file = os.path.join(DOWNLOAD_DIR, "twitter_biodata.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)

        print(f"\nAll biodata saved to: {out_file}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
