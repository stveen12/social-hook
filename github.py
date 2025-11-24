import os
import json
import time
from pathlib import Path
import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify


load_dotenv(dotenv_path="credentials/github.env")
TOKEN = os.getenv("GITHUB_TOKEN")
TOTAL_REPOS_TO_SCRAPE = int(os.getenv("TOTAL_REPOS_TO_SCRAPE", 5))

headers = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def get_user(username):
    url = f"https://api.github.com/users/{username}"
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json()


def get_repos(username, limit=TOTAL_REPOS_TO_SCRAPE):
    repos = []
    page = 1
    while len(repos) < limit:
        url = f"https://api.github.com/users/{username}/repos"
        r = requests.get(url, headers=headers, params={"per_page": 100, "page": page})
        r.raise_for_status()
        data = r.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos[:limit]


def get_profile_readme(username):
    url = f"https://api.github.com/repos/{username}/{username}/readme"
    r = requests.get(url, headers={**headers, "Accept": "application/vnd.github.v3.raw"})
    if r.status_code == 200:
        return r.text
    return None


def get_contributions_last_year(username):
    url = f"https://api.github.com/users/{username}/events/public"
    contributions = []
    page = 1
    
    while page <= 3:
        r = requests.get(url, headers=headers, params={"per_page": 100, "page": page})
        r.raise_for_status()
        data = r.json()
        if not data:
            break
        contributions.extend(data)
        page += 1
    
    from collections import Counter
    from datetime import datetime
    
    contribution_days = Counter()
    for event in contributions:
        date = datetime.strptime(event['created_at'], "%Y-%m-%dT%H:%M:%SZ").date()
        contribution_days[str(date)] += 1
    
    return {
        "total_events": len(contributions),
        "contribution_days": dict(contribution_days),
        "events_by_type": Counter(e['type'] for e in contributions)
    }


def scrape_github_user(username, total_repos=None):
    if total_repos is None:
        total_repos = TOTAL_REPOS_TO_SCRAPE

    print(f"🔎 Scraping GitHub user: {username}")
    user_data = get_user(username)
    repos = get_repos(username, limit=total_repos)
    readme = get_profile_readme(username)
    contributions = get_contributions_last_year(username)

    biodata = {
        "user": {
            "name": user_data.get("name"),
            "username": user_data.get("login"),
            "bio": user_data.get("bio"),
            "public_repos": user_data.get("public_repos"),
            "profile_readme": readme[:500] + "..." if readme else None,
        },
        "contributions": {
            "total_events": contributions["total_events"],
            "daily": contributions["contribution_days"],
            "events_by_type": dict(contributions["events_by_type"])
        },
        "repos": [
            {
                "name": repo["name"],
                "stars": repo["stargazers_count"],
                "forks": repo["forks_count"],
                "url": repo["html_url"],
                "last_pushed": repo["pushed_at"],
            }
            for repo in repos
        ]
    }
    return biodata


app = Flask(__name__)

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.get_json()
    
    if not data or 'usernames' not in data:
        return jsonify({"error": "Please provide 'usernames' in request body"}), 400
    
    usernames = data['usernames']
    if not isinstance(usernames, list):
        return jsonify({"error": "'usernames' must be a list"}), 400
    
    total_repos = data.get('total_repos', 5)

    results = []
    errors = []
    
    for username in usernames:
        try:
            biodata = scrape_github_user(username, total_repos=total_repos)
            results.append(biodata)
            time.sleep(1)
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
    
    return jsonify(response)

@app.route('/sanity', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "GitHub Scraper"})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)