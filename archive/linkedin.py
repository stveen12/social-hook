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
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager


COOKIES_FILE = "credentials/linkedin_cookies.json"
WAIT_SEC = 15


def setup_driver():
    os.makedirs(os.path.dirname(COOKIES_FILE), exist_ok=True)

    options = webdriver.ChromeOptions()

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, WAIT_SEC)
    driver.maximize_window()

    return driver, wait


def login_with_cookies(driver, wait_sec):
    driver.get("https://www.linkedin.com/")
    time.sleep(3)

    if os.path.exists(COOKIES_FILE):
        with open(COOKIES_FILE, "r", encoding="utf-8") as f:
            cookies = json.load(f)
            for c in cookies:
                if "domain" not in c or not c["domain"]:
                    c["domain"] = ".linkedin.com"
                try:
                    driver.add_cookie(c)
                except Exception:
                    continue
        driver.refresh()
        time.sleep(3)
        print("Logged in with cookies.")
        return
    else:
        print("No cookies yet. log in manually in the opened browser")
        time.sleep(wait_sec)
        with open(COOKIES_FILE, "w", encoding="utf-8") as f:
            json.dump(driver.get_cookies(), f, indent=4, ensure_ascii=False)
        print("Cookies saved.")
        return

def scrape_experience(driver, wait, profile_url):
    exp_url = profile_url.rstrip("/") + "/details/experience/"
    driver.get(exp_url)

    try:
        exp_section = wait.until(
            EC.presence_of_element_located((By.XPATH,
                '//*[@id="profile-content"]/div/div[2]/div/div/main/section/div[2]/div/div[1]/ul'
            ))
        )
        time.sleep(WAIT_SEC)

        for hidden in exp_section.find_elements(By.CSS_SELECTOR, "span.visually-hidden"):
            driver.execute_script("arguments[0].remove();", hidden)

        exp_text = exp_section.text.strip()
        return exp_text
    except TimeoutException:
        print(f"⚠️ Experience section not found for {profile_url}")
        return ""


def scrape_education(driver, wait, profile_url):
    edu_url = profile_url.rstrip("/") + "/details/education/"
    driver.get(edu_url)

    try:
        edu_section = wait.until(
            EC.presence_of_element_located((By.XPATH,
                '//*[@id="profile-content"]/div/div[2]/div/div/main/section/div[2]/div/div[1]/ul'
            ))
        )
        time.sleep(WAIT_SEC)

        for hidden in edu_section.find_elements(By.CSS_SELECTOR, "span.visually-hidden"):
            driver.execute_script("arguments[0].remove();", hidden)

        edu_text = edu_section.text.strip()
        return edu_text
    except TimeoutException:
        print(f"⚠️ Education section not found for {profile_url}")
        return ""


def scrape_certifications(driver, wait, profile_url):
    cert_url = profile_url.rstrip("/") + "/details/certifications/"
    driver.get(cert_url)

    try:
        cert_section = wait.until(
            EC.presence_of_element_located((By.XPATH,
                '//*[@id="profile-content"]/div/div[2]/div/div/main/section/div[2]/div/div[1]/ul'
            ))
        )
        time.sleep(WAIT_SEC)

        for hidden in cert_section.find_elements(By.CSS_SELECTOR, "span.visually-hidden"):
            driver.execute_script("arguments[0].remove();", hidden)

        cert_text = cert_section.text.strip()
        return cert_text
    except TimeoutException:
        print(f"⚠️ Certifications section not found for {profile_url}")
        return ""


def scrape_skills(driver, wait, profile_url):
    skills_url = profile_url.rstrip("/") + "/details/skills/"
    driver.get(skills_url)

    try:
        skills_section = wait.until(
            EC.presence_of_element_located((By.XPATH,
                '//*[@id="ember50"]/div/div/div[1]/ul'
            ))
        )
        time.sleep(WAIT_SEC)

        for hidden in skills_section.find_elements(By.CSS_SELECTOR, "span.visually-hidden"):
            driver.execute_script("arguments[0].remove();", hidden)

        skills_text = skills_section.text.strip()
        return skills_text
    except TimeoutException:
        print(f"⚠️ Skills section not found for {profile_url}")
        return ""


def scrape_posts(driver, wait, profile_url, total_posts=None):
    if total_posts is None:
        total_posts = 5
    
    posts_url = profile_url.rstrip("/") + "/recent-activity/all/"
    driver.get(posts_url)
    time.sleep(WAIT_SEC)

    posts = []

    try:
        post_container = driver.find_elements(By.CSS_SELECTOR, "ul.display-flex.flex-wrap.list-style-none.justify-center")
        
        if not post_container:
            print(f"ℹ️ No posts found for {profile_url}")
            return posts
        
        post_items = post_container[0].find_elements(By.CSS_SELECTOR, "li.jlceCXnNnUIXJwYwiqGBgFCTgjOGbeOxJ")
        
        for post_item in post_items[:total_posts]:
            post_data = {"is_repost": False, "caption": "", "images": []}
            
            repost_indicator = post_item.find_elements(By.CSS_SELECTOR, "span.update-components-header__text-view")
            if repost_indicator:
                post_data["is_repost"] = True
            
            try:
                caption_el = post_item.find_element(By.CSS_SELECTOR, "span.break-words.tvm-parent-container")
                post_data["caption"] = caption_el.text.strip()
            except Exception as e:
                print(f"    ⚠️ Could not get caption: {e}")
            
            try:
                image_buttons = post_item.find_elements(By.CSS_SELECTOR, "button.update-components-image__image-link")
                for btn in image_buttons:
                    try:
                        img = btn.find_element(By.TAG_NAME, "img")
                        img_src = img.get_attribute("src")
                        if img_src:
                            post_data["images"].append(img_src)
                    except Exception:
                        continue
            except Exception as e:
                print(f"    ⚠️ Could not get images: {e}")
            
            posts.append(post_data)
        
        print(f"  📝 Found {len(posts)} posts")
        
    except Exception as e:
        print(f"⚠️ Error scraping posts for {profile_url}: {e}")
    
    return posts




def scrape_biodata(driver, wait, profile_url, total_posts=None):
    driver.get(profile_url)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(2)

    biodata = {"username": profile_url.rstrip("/").split("/")[-1], "bio": "", "about": ""}

    
    try:
        bio_el = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.text-body-medium.break-words"))
        )
        biodata["bio"] = bio_el.text.strip().replace("\n", " ")
    except TimeoutException:
        print(f"⚠️ Could not find bio for {profile_url}")

    
    try:
        about_el = wait.until(
            EC.presence_of_element_located((By.XPATH,
                '//*[@id="profile-content"]/div/div[2]/div/div/main/section[3]/div[3]/div/div/div//span'
            ))
        )
        biodata["about"] = about_el.text.strip().replace("\n", " ")
    except TimeoutException:
        print(f"⚠️ Could not find about section for {profile_url}")


    biodata["experience"] = scrape_experience(driver, wait, profile_url)
    biodata["education"] = scrape_education(driver, wait, profile_url)
    biodata["certifications"] = scrape_certifications(driver, wait, profile_url)
    biodata["skills"] = scrape_skills(driver, wait, profile_url)
    biodata["posts"] = scrape_posts(driver, wait, profile_url, total_posts=total_posts)

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
    data = request.get_json()
    total_posts = data.get('total_posts', 5) if data else 5
    
    if not data or 'urls' not in data:
        return jsonify({"error": "Please provide 'urls' in request body"}), 400
    
    urls = data['urls']
    if not isinstance(urls, list):
        return jsonify({"error": "'urls' must be a list"}), 400
    
    try:
        driver, wait = initialize_driver(0)
        
        results = []
        errors = []
        
        for url in urls:
            try:
                if not url.startswith("http"):
                    errors.append({"url": url, "error": "Invalid URL format"})
                    continue
                
                print(f"🔎 Scraping LinkedIn user: {url}")
                biodata = scrape_biodata(driver, wait, url, total_posts=total_posts)
                results.append(biodata)
                
            except Exception as e:
                errors.append({"url": url, "error": str(e)})
        
        response = {
            "success": True,
            "scraped": len(results),
            "results": results,
        }
        
        if errors:
            response["errors"] = errors
            response["success"] = False
        
        driver.quit()
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@app.route('/sanity', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "LinkedIn Scraper"})

@app.route('/login', methods=['POST'])
def login():
    """Initialize driver and login with cookies"""
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
    app.run(debug=True, host="0.0.0.0", port=5002)
