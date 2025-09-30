import os
import json
import time
from pathlib import Path
import requests
from dotenv import load_dotenv


load_dotenv(dotenv_path="credentials/github.env")
TOKEN = os.getenv("GITHUB_TOKEN")


TOTAL_REPOS_TO_SCRAPE = 5

DOWNLOAD_DIR = str(Path(__file__).parent / "data" / "github_data")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

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


def scrape_github_user(username):
    print(f"🔎 Scraping GitHub user: {username}")
    user_data = get_user(username)
    repos = get_repos(username)
    readme = get_profile_readme(username)

    biodata = {
        "name": user_data.get("name"),
        "login": user_data.get("login"),
        "bio": user_data.get("bio"),
        "public_repos": user_data.get("public_repos"),
        "repos": [
            {
                "name": repo["name"],
                "stars": repo["stargazers_count"],
                "forks": repo["forks_count"],
                "url": repo["html_url"],
            }
            for repo in repos
        ],
        "profile_readme": readme[:500] + "..." if readme else None,
    }
    return biodata


def main():
    num_users = int(input("How many GitHub users to scrape? ").strip())

    usernames = []
    for i in range(num_users):
        username = input(f"Enter GitHub username #{i+1}: ").strip()
        if not username:
            print("⚠️ Invalid username, skipping.")
            continue
        usernames.append(username)

    results = []
    for i, username in enumerate(usernames, 1):
        try:
            data = scrape_github_user(username)
            results.append(data)
            print(f"[{i}/{len(usernames)}] ✅ Scraped: {data['login']}")
            time.sleep(1)  
        except Exception as e:
            print(f"❌ Error scraping {username}: {e}")

    out_file = os.path.join(DOWNLOAD_DIR, "github_biodata.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    print(f"\nAll GitHub biodata saved to: {out_file}")


if __name__ == "__main__":
    main()
