import httpx
import base64
import asyncio
import os

async def fetch_github_readme(url: str) -> str:
    """
    Accepts a GitHub repo URL like https://github.com/owner/repo
    Returns the README text content.
    """
    parts = url.rstrip("/").split("/")
    owner, repo = parts[-2], parts[-1]

    api_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    async with httpx.AsyncClient() as client:
        response = await client.get(api_url, headers={"Accept": "application/vnd.github.v3+json"})
        response.raise_for_status()
        data = response.json()
        return base64.b64decode(data["content"]).decode("utf-8")

async def fetch_all_github_projects(profile_url: str) -> str:
    """
    Accepts a GitHub profile URL like https://github.com/hareshramasamy
    Fetches top 20 public repos and their READMEs concurrently, returns combined text.
    """
    username = profile_url.rstrip("/").split("/")[-1]
    token = os.getenv("GITHUB_TOKEN")
    headers = {
        "Accept": "application/vnd.github.v3+json",
        **({"Authorization": f"Bearer {token}"} if token else {})
    }

    async with httpx.AsyncClient(headers=headers) as client:
        repos_response = await client.get(
            f"https://api.github.com/users/{username}/repos",
            params={"per_page": 100, "sort": "updated"}
        )
        repos_response.raise_for_status()
        repos = repos_response.json()[:20]

        async def fetch_readme(repo):
            try:
                response = await client.get(
                    f"https://api.github.com/repos/{username}/{repo['name']}/readme"
                )
                response.raise_for_status()
                data = response.json()
                return base64.b64decode(data["content"]).decode("utf-8")
            except Exception:
                return ""

        readmes = await asyncio.gather(*[fetch_readme(repo) for repo in repos])

    combined = f"GitHub projects for {username}:\n\n"
    for repo, readme in zip(repos, readmes):
        combined += f"## {repo['name']}\n"
        combined += f"Description: {repo['description'] or 'No description'}\n"
        combined += f"Language: {repo['language']}\n"
        combined += f"Stars: {repo['stargazers_count']} | Last updated: {repo['pushed_at']}\n"
        combined += f"URL: {repo['html_url']}\n"
        if readme:
            combined += f"\nREADME:\n{readme}\n"
        combined += "\n"
    return combined.strip()