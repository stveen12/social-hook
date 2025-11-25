import os
import time
import json
from pathlib import Path
from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager


COOKIES_FILE = "credentials/twitter_cookies.json"
WAIT_SEC = 2
TOTAL_POSTS_TO_SCRAPE = 5

def setup_driver():
    os.makedirs(os.path.dirname(COOKIES_FILE), exist_ok=True)

    options = webdriver.ChromeOptions()

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, WAIT_SEC)
    driver.maximize_window()

    return driver, wait


def login_with_cookies(driver, wait_sec):
    
    driver.get("https://x.com/")
    time.sleep(WAIT_SEC)

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
        time.sleep(WAIT_SEC)
        print("Logged in with cookies.")
        return
    else:
        
        driver.get("https://x.com/login")
        print("No cookies yet. log in manually in the opened browser")
        time.sleep(wait_sec)
        with open(COOKIES_FILE, "w", encoding="utf-8") as f:
            json.dump(driver.get_cookies(), f, indent=4, ensure_ascii=False)
        print("Cookies saved.")
        return

def scrape_biodata(driver, wait, profile_url):
    driver.get(profile_url)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(WAIT_SEC)

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


def scrape_biodata_and_posts(driver, wait, profile_url, total_posts=None):
    if total_posts is None:
        total_posts = TOTAL_POSTS_TO_SCRAPE
    
    biodata = scrape_biodata(driver, wait, profile_url)
    biodata["captions"] = []

    scraped = 0
    post_index = 1
    time.sleep(WAIT_SEC)
    while scraped < total_posts:
        try:
            
            post_xpath = f"/html/body/div[1]/div/div/div[2]/main/div/div/div/div/div/div[3]/div/div/section/div/div/div[{post_index}]"
            post = driver.find_element(By.XPATH, post_xpath)

            driver.execute_script("arguments[0].scrollIntoView(true);", post)
            time.sleep(WAIT_SEC)

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
            time.sleep(WAIT_SEC)

        except Exception:
            print("ℹ️ No more posts found or reached end of feed.")
            break

    return biodata




app = Flask(__name__)

driver = None
wait = None

def initialize_driver(wait_sec):
    global driver, wait
    if driver is None:
        driver, wait = setup_driver()
        login_with_cookies(driver, wait_sec)
    return driver, wait

@app.route('/scrape', methods=['POST'])
def scrape():
    global driver, wait
    data = request.get_json()
    total_posts = data.get('total_posts', 5) if data else 5
    
    if not data or 'usernames' not in data:
        return jsonify({"error": "Please provide 'usernames' in request body"}), 400
    
    usernames = data['usernames']
    if not isinstance(usernames, list):
        return jsonify({"error": "'usernames' must be a list"}), 400
    
    try:
        driver, wait = initialize_driver(0)
        
        results = []
        errors = []
        
        for username in usernames:
            try:
                profile_url = f"https://x.com/{username.strip('/')}" if not username.startswith('http') else username
                print(f"🔎 Scraping Twitter user: {username}")
                
                user_data = scrape_biodata_and_posts(driver, wait, profile_url, total_posts=total_posts)
                results.append(user_data)
                
            except Exception as e:
                errors.append({"username": username, "error": str(e)})
        
        response = {
            "success": True,
            "scraped": len(results),
            "results": results,
        }
        
        if errors:
            response["errors"] = errors
            response["success"] = False
        
        driver.quit()
        driver = None
        wait = None
        return jsonify(response)
        
    except Exception as e:
        if driver:
            driver.quit()
            driver = None
            wait = None
        return jsonify({"error": str(e), "success": False}), 500

@app.route('/sanity', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "Twitter Scraper"})

@app.route('/login', methods=['POST'])
def login():
    global driver
    data = request.get_json()
    wait_sec = data.get('wait_sec', 30) if data else 30
    
    try:
        temp_driver, temp_wait = setup_driver()
        login_with_cookies(temp_driver, wait_sec)
        
        return jsonify({"success": True, "message": "Login completed and browser closed"})
    except Exception as e:
        if 'temp_driver' in locals():
            temp_driver.quit()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        temp_driver.quit()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5003)
