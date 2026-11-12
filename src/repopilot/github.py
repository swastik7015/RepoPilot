import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

def analyze_github_repository(repository):
    parts = repository.strip("/").split("/")

    if len(parts) != 2 or not all(parts):
        raise ValueError("Use owner/repository format.")

    owner, repo = parts
    url = f"https://api.github.com/repos/{owner}/{repo}"

    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "RepoPilot"
        }
    )

    try:
        with urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        if error.code == 404:
            raise ValueError("Repository not found or is private.")
        if error.code == 403:
            raise ValueError("GitHub API rate limit reached. Try later.")
        raise ValueError(f"GitHub API error: HTTP {error.code}")
    except URLError as error:
        raise ValueError(f"Network error: {error.reason}")

    license_data = data.get("license") or {}

    return {
        "repository": data["full_name"],
        "url": data["html_url"],
        "description": data.get("description"),
        "stars": data["stargazers_count"],
        "forks": data["forks_count"],
        "watchers": data["subscribers_count"],
        "open_issues": data["open_issues_count"],
        "language": data.get("language"),
        "license": license_data.get("spdx_id"),
        "default_branch": data["default_branch"],
        "created_at": data["created_at"],
        "updated_at": data["updated_at"],
        "last_push": data["pushed_at"],
        "archived": data["archived"],
        "is_fork": data["fork"],
        "topics": data.get("topics", [])
    }
