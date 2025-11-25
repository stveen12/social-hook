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
from webdriver_manager.chrome import ChromeDriverManager


COOKIES_FILE = "credentials/instagram_cookies.json"
WAIT_SEC = 1
TOTAL_POSTS_TO_SCRAPE = 5


def setup_driver():
    os.makedirs(os.path.dirname(COOKIES_FILE), exist_ok=True)

    options = webdriver.ChromeOptions()

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, WAIT_SEC)
    driver.maximize_window()

    return driver, wait


def login_with_cookies(driver, login_wait_sec):
    driver.get("https://www.instagram.com/")
    time.sleep(WAIT_SEC)

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
        time.sleep(WAIT_SEC)
        print("Logged in with cookies.")
        return
    else:
        print("No cookies yet. log in manually in the opened browser")
        time.sleep(login_wait_sec)
        with open(COOKIES_FILE, "w", encoding="utf-8") as f:
            json.dump(driver.get_cookies(), f, indent=4, ensure_ascii=False)
        print("Cookies saved.")
        return

def scrape_biodata(driver, wait, profile_username):
    driver.get(profile_username)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "header")))
    time.sleep(WAIT_SEC)

    username = profile_username.rstrip("/").split("/")[-1]
    bio = ""
    profile_image = ""

    try:
        img = driver.find_element(By.CSS_SELECTOR, "img.xpdipgo.x972fbf.x10w94by.x1qhh985.x14e42zd.xk390pu.x5yr21d.xdj266r.x14z9mp.xat24cr.x1lziwak.xl1xv1r.xexx8yu.xyri2b.x18d9i69.x1c1uobl.x11njtxf.xh8yej3")
        profile_image = img.get_attribute("src")
        print(f"  🖼️ Profile image: {profile_image[:60]}...")
    except Exception as e:
        print(f"⚠️ Error scraping profile image for {profile_username}: {e}")

    try:
        bio_spans = driver.find_elements(By.CSS_SELECTOR, "span._ap3a._aaco._aacu._aacx._aad7._aade")
        if bio_spans:
            last_span = bio_spans[-1]
            bio = last_span.text.strip().replace("\n", " ")
            print(f"  📝 Bio: {bio[:60]}...")
    except Exception as e:
        print(f"⚠️ Error scraping bio for {profile_username}: {e}")

    return {
        "user": {
            "username": username,
            "bio": bio,
            "profile_image": profile_image
        }
    }


def get_post_images(driver, wait):
    images = []
    
    try:
        video_elements = driver.find_elements(By.CSS_SELECTOR, "video.x1lliihq.x5yr21d.xh8yej3")
        if video_elements:
            src = video_elements[0].get_attribute("src")
            images.append(src)
            print(f"    🎥 Video found: {src[:60]}...")
            return images
        
        next_img_button = driver.find_elements(By.CSS_SELECTOR, "button._afxw._al46._al47")
        
        if next_img_button:
            print("    📸 Multiple images detected")
            while True:
                try:
                    ul_elements = driver.find_elements(By.CSS_SELECTOR, "ul._acay")
                    if ul_elements:
                        last_ul = ul_elements[-1]
                        first_li = last_ul.find_element(By.CSS_SELECTOR, "li._acaz")
                        img = first_li.find_element(By.CSS_SELECTOR, "img.x5yr21d.xu96u03.x10l6tqk.x13vifvy.x87ps6o.xh8yej3")
                        src = img.get_attribute("src")
                        images.append(src)
                        print(f"    📷 Image {len(images)}: {src[:60]}...")
                    
                    next_btn = driver.find_elements(By.CSS_SELECTOR, "button._afxw._al46._al47")
                    if not next_btn:
                        break
                    driver.execute_script("arguments[0].click();", next_btn[0])
                    time.sleep(WAIT_SEC)
                except Exception as e:
                    print(f"    ⚠️ End of carousel or error: {e}")
                    break
        else:
            try:
                div_container = driver.find_element(By.CSS_SELECTOR, "div._aagu._aato")
                img = div_container.find_element(By.CSS_SELECTOR, "img.x5yr21d.xu96u03.x10l6tqk.x13vifvy.x87ps6o.xh8yej3")
                src = img.get_attribute("src")
                images.append(src)
                print(f"    📷 Single image: {src[:60]}...")
            except Exception as e:
                print(f"    ⚠️ Could not get single image: {e}")
    
    except Exception as e:
        print(f"    ⚠️ Error getting images: {e}")
    
    return images


def scrape_posts(driver, wait, total_posts=None):
    if total_posts is None:
        total_posts = TOTAL_POSTS_TO_SCRAPE
    
    posts = []
    
    try:
        first_post = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div._aagw")))
        driver.execute_script("arguments[0].click();", first_post)
        time.sleep(WAIT_SEC)

        scraped = 0
        clicked_next = False

        while scraped < total_posts:
            post_data = {"caption": "", "images": []}
            
            try:
                caption_el = wait.until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "h1._ap3a._aaco._aacu._aacx._aad7._aade")
                    )
                )
                caption = caption_el.text.strip().replace("\n", " ")
                post_data["caption"] = caption
                print(f"  📝 Post {scraped + 1} caption: {caption[:60]}...")
            except Exception as e:
                print(f"  ℹ️ No caption for post {scraped + 1} (image-only post)")
            
            images = get_post_images(driver, wait)
            post_data["images"] = images
            
            posts.append(post_data)
            scraped += 1

            nav_buttons = driver.find_elements(By.CSS_SELECTOR, "button._abl-")

            if len(nav_buttons) == 1:
                print("ℹ️ Only one post found, stopping.")
                break
            elif len(nav_buttons) == 2:
                if not clicked_next:
                    driver.execute_script("arguments[0].click();", nav_buttons[0])
                    clicked_next = True
                    time.sleep(WAIT_SEC)
                else:
                    print("ℹ️ Reached last post, stopping.")
                    break
            elif len(nav_buttons) == 3:
                driver.execute_script("arguments[0].click();", nav_buttons[1])
                clicked_next = True
                time.sleep(WAIT_SEC)
            else:
                print("⚠️ Unexpected button state, stopping.")
                break

    except Exception as e:
        print(f"⚠️ Error scraping posts: {e}")

    return posts

app = Flask(__name__)

driver = None
wait = None

def initialize_driver(login_wait_sec):
    global driver, wait
    if driver is None:
        driver, wait = setup_driver()
        login_with_cookies(driver, login_wait_sec)
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
                profile_url = f"https://www.instagram.com/{username.strip('/')}/" if not username.startswith('http') else username
                print(f"🔎 Scraping Instagram user: {username}")
                
                biodata = scrape_biodata(driver, wait, profile_url)
                posts = scrape_posts(driver, wait, total_posts=total_posts)
                user_data = {**biodata, "posts": posts}
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
    return jsonify({"status": "ok", "service": "Instagram Scraper"})

@app.route('/login', methods=['POST'])
def login():
    global driver
    data = request.get_json()
    login_wait_sec = data.get('wait_sec', 30) if data else 30
    
    try:
        temp_driver, temp_wait = setup_driver()
        login_with_cookies(temp_driver, login_wait_sec)
        
        return jsonify({"success": True, "message": "Login completed and browser closed"})
    except Exception as e:
        if 'temp_driver' in locals():
            temp_driver.quit()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        temp_driver.quit()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
