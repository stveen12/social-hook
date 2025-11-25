import time
from flask import Flask, request, jsonify
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)
GITHUB_PORT = 5000
INSTAGRAM_PORT = 5001
XTWITTER_PORT = 5003

def call_github_scraper(github_usernames, total_posts):
    print(f"🔎 Calling GitHub scraper for {len(github_usernames)} users...")
    try:
        response = requests.post(
            f"http://localhost:{GITHUB_PORT}/scrape",
            json={"usernames": github_usernames, "total_repos": total_posts},
            timeout=300
        )
        if response.status_code == 200:
            return {"platform": "github", "data": response.json(), "success": True}
        else:
            return {
                "platform": "github",
                "success": False,
                "error": f"GitHub scraper returned status {response.status_code}"
            }
    except Exception as e:
        return {
            "platform": "github",
            "success": False,
            "error": f"Failed to call GitHub scraper: {str(e)}"
        }

def call_instagram_scraper(instagram_urls, total_posts):
    print(f"🔎 Calling Instagram scraper for {len(instagram_urls)} users...")
    try:
        response = requests.post(
            f"http://localhost:{INSTAGRAM_PORT}/scrape",
            json={"usernames": instagram_urls, "total_posts": total_posts},
            timeout=300
        )
        if response.status_code == 200:
            return {"platform": "instagram", "data": response.json(), "success": True}
        else:
            return {
                "platform": "instagram",
                "success": False,
                "error": f"Instagram scraper returned status {response.status_code}"
            }
    except Exception as e:
        return {
            "platform": "instagram",
            "success": False,
            "error": f"Failed to call Instagram scraper: {str(e)}"
        }

def call_xtwitter_scraper(xtwitter_urls, total_posts):
    print(f"🔎 Calling Twitter scraper for {len(xtwitter_urls)} users...")
    try:
        response = requests.post(
            f"http://localhost:{XTWITTER_PORT}/scrape",
            json={"usernames": xtwitter_urls, "total_posts": total_posts},
            timeout=300
        )
        if response.status_code == 200:
            return {"platform": "xtwitter", "data": response.json(), "success": True}
        else:
            return {
                "platform": "xtwitter",
                "success": False,
                "error": f"Twitter scraper returned status {response.status_code}"
            }
    except Exception as e:
        return {
            "platform": "xtwitter",
            "success": False,
            "error": f"Failed to call Twitter scraper: {str(e)}"
        }

@app.route('/scrape_all', methods=['POST'])
def scrape_all():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    github_usernames = data.get('github_usernames', [])
    instagram_urls = data.get('instagram_urls', [])
    xtwitter_urls = data.get('xtwitter_urls', [])
    total_posts = data.get('total_posts', 5)
    trainee_id = data.get('trainee_id', '')
    
    results = {
        "trainee_id": trainee_id,
        "github": [],
        "instagram": [],
        "xtwitter": [],
        "errors": []
    }
    
    tasks = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        
        if github_usernames:
            futures.append(executor.submit(call_github_scraper, github_usernames, total_posts))
        
        if instagram_urls:
            futures.append(executor.submit(call_instagram_scraper, instagram_urls, total_posts))
        
        if xtwitter_urls:
            futures.append(executor.submit(call_xtwitter_scraper, xtwitter_urls, total_posts))
        
        for future in as_completed(futures):
            result = future.result()
            platform = result["platform"]
            
            if result["success"]:
                platform_data = result["data"]
                results[platform] = platform_data.get("results", [])
                
                if "errors" in platform_data:
                    for err in platform_data["errors"]:
                        results["errors"].append({
                            "platform": platform,
                            **err
                        })
            else:
                results["errors"].append({
                    "platform": platform,
                    "error": result["error"]
                })
    
    response = {
        "success": len(results["errors"]) == 0,
        "trainee_id": trainee_id,
        "results": results,
        "summary": {
            "github_scraped": len(results["github"]),
            "instagram_scraped": len(results["instagram"]),
            "xtwitter_scraped": len(results["xtwitter"]),
            "total_errors": len(results["errors"])
        }
    }
    
    return jsonify(response)

@app.route('/sanity', methods=['GET'])
def health():
    services = {
        "handler": {"status": "ok", "port": 8000},
        "github": {"status": "unknown", "port": GITHUB_PORT},
        "instagram": {"status": "unknown", "port": INSTAGRAM_PORT},
        "xtwitter": {"status": "unknown", "port": XTWITTER_PORT}
    }
    
    for service_name, service_info in list(services.items()):
        if service_name == "handler":
            continue
        
        try:
            response = requests.get(f"http://localhost:{service_info['port']}/sanity", timeout=2)
            if response.status_code == 200:
                services[service_name]["status"] = "ok"
            else:
                services[service_name]["status"] = "error"
        except Exception as e:
            services[service_name]["status"] = "offline"
            services[service_name]["error"] = str(e)
    
    all_ok = all(s["status"] == "ok" for s in services.values())
    
    return jsonify({
        "status": "ok" if all_ok else "degraded",
        "service": "Social Hook Handler",
        "services": services
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
