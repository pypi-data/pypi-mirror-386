import requests
import os
from dotenv import load_dotenv
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))
from cli.session.SessionManager import session
from constants.constants import (
    GITHUB_PULLS_ENDPOINT, GITHUB_PR_COMMENTS_ENDPOINT, GITHUB_REPOS_ENDPOINT,
    AUTH_BEARER_PREFIX, AUTH_TOKEN_PREFIX,
    HTTP_OK, HTTP_UNAUTHORIZED, HTTP_FORBIDDEN, HTTP_NOT_FOUND,
    ERROR_NO_TOKEN, ERROR_NO_ORG, ERROR_NO_USER,
    ERROR_INVALID_PAT, ERROR_RATE_LIMIT, ERROR_REPO_NOT_FOUND, ERROR_PR_NOT_FOUND
)

load_dotenv()

def get_issues_assigned_to_me(repo):
    """
    Get all issues assigned to the current user in a specific repository
    """
    try:
        token = session.get_pat()
        
        if not token:
            return {"error": ERROR_NO_TOKEN}
        
        org = session.get_org()
        author = session.get_user()
        
        if org is None:
            return {"error": ERROR_NO_ORG}
        if author is None:
            return {"error": ERROR_NO_USER}
        
        # Try Bearer format first
        headers = {"Authorization": f"{AUTH_BEARER_PREFIX} {token}"}
        
        # Repository-specific issues
        url = f"https://api.github.com/repos/{org}/{repo}/issues"
        params = {
            "assignee": author,
            "state": "all",  # Get both open and closed issues
            "sort": "updated",
            "direction": "desc"
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        # If Bearer fails, try token format
        if response.status_code == HTTP_UNAUTHORIZED:
            headers = {"Authorization": f"{AUTH_TOKEN_PREFIX} {token}"}
            response = requests.get(url, headers=headers, params=params)
        
        # Check for HTTP errors
        if response.status_code == HTTP_UNAUTHORIZED:
            return {"error": f"Unauthorized: {ERROR_INVALID_PAT}"}
        elif response.status_code == HTTP_FORBIDDEN:
            return {"error": f"Forbidden: {ERROR_RATE_LIMIT}"}
        elif response.status_code == HTTP_NOT_FOUND:
            return {"error": ERROR_REPO_NOT_FOUND.format(org=org, repo=repo)}
        elif response.status_code != HTTP_OK:
            return {"error": f"GitHub API error: {response.status_code} - {response.text}"}
        
        response_data = response.json()
        
        if isinstance(response_data, dict) and "message" in response_data:
            return {"error": f"GitHub API error: {response_data['message']}"}
        
        # Filter out pull requests (issues have pull_request field if they're PRs)
        actual_issues = [issue for issue in response_data if "pull_request" not in issue]
        
        return [
            {
                "number": issue["number"],
                "title": issue["title"],
                "state": issue["state"],
                "body": issue.get("body", ""),
                "labels": [label["name"] for label in issue.get("labels", [])],
                "assignees": [assignee["login"] for assignee in issue.get("assignees", [])],
                "created_at": issue["created_at"],
                "updated_at": issue["updated_at"],
                "closed_at": issue.get("closed_at"),
                "url": issue["html_url"],
                "comments": issue["comments"],
                "milestone": issue.get("milestone", {}).get("title") if issue.get("milestone") else None,
                "repository": repo  # Repository name is always known since it's required
            }
            for issue in actual_issues
        ]
        
    except Exception as e:
        return {"error": f"Error: {str(e)}"}

def get_pull_requests_by_author(repo):
    try:
        # Get token from session instead of environment
        token = session.get_pat()
        
        if not token:
            return {"error": ERROR_NO_TOKEN}
        
        org = session.get_org()
        author = session.get_user()
        
        if org is None:
            return {"error": ERROR_NO_ORG}
        if author is None:
            return {"error": ERROR_NO_USER}
        
        # Try Bearer format first
        headers = {"Authorization": f"{AUTH_BEARER_PREFIX} {token}"}
        url = GITHUB_PULLS_ENDPOINT.format(org=org, repo=repo)
        
        # Add author parameter to filter by creator and state=all to get all PRs
        params = {"creator": author, "state": "all"}
        
        response = requests.get(url, headers=headers, params=params)
        
        # If Bearer fails, try token format
        if response.status_code == HTTP_UNAUTHORIZED:
            headers = {"Authorization": f"{AUTH_TOKEN_PREFIX} {token}"}
            response = requests.get(url, headers=headers, params=params)
        
        # Check for HTTP errors
        if response.status_code == HTTP_UNAUTHORIZED:
            return {"error": f"Unauthorized: {ERROR_INVALID_PAT}"}
        elif response.status_code == HTTP_FORBIDDEN:
            return {"error": f"Forbidden: {ERROR_RATE_LIMIT}"}
        elif response.status_code == HTTP_NOT_FOUND:
            return {"error": ERROR_REPO_NOT_FOUND.format(org=org, repo=repo)}
        elif response.status_code != HTTP_OK:
            return {"error": f"GitHub API error: {response.status_code} - {response.text}"}
        
        prs = response.json()
        
        if isinstance(prs, dict) and "message" in prs:
            return {"error": f"GitHub API error: {prs['message']}"}
        
        return [
            {
                "title": pr["title"], 
                "state": pr["state"], 
                "url": pr["html_url"],
                "author": pr["user"]["login"],
                "created_at": pr["created_at"],
                "merged_at": pr.get("merged_at")
            }
            for pr in prs
        ]
        
    except Exception as e:
        return {"error": f"Error: {str(e)}"}

def get_pr_review_comments(org, repo, pr_number):
    try:
        # Get token from session instead of environment
        token = session.get_pat()
        
        if not token:
            return {"error": ERROR_NO_TOKEN}
        
        # Try Bearer format first
        headers = {"Authorization": f"{AUTH_BEARER_PREFIX} {token}"}
        url = GITHUB_PR_COMMENTS_ENDPOINT.format(org=org, repo=repo, pr_number=pr_number)
        
        response = requests.get(url, headers=headers)
        
        # If Bearer fails, try token format
        if response.status_code == HTTP_UNAUTHORIZED:
            headers = {"Authorization": f"{AUTH_TOKEN_PREFIX} {token}"}
            response = requests.get(url, headers=headers)
        
        # Check for HTTP errors
        if response.status_code == HTTP_UNAUTHORIZED:
            return {"error": f"Unauthorized: {ERROR_INVALID_PAT}"}
        elif response.status_code == HTTP_FORBIDDEN:
            return {"error": f"Forbidden: {ERROR_RATE_LIMIT}"}
        elif response.status_code == HTTP_NOT_FOUND:
            return {"error": ERROR_PR_NOT_FOUND.format(org=org, repo=repo, pr_number=pr_number)}
        elif response.status_code != HTTP_OK:
            return {"error": f"GitHub API error: {response.status_code} - {response.text}"}
        
        comments = response.json()
        
        if isinstance(comments, dict) and "message" in comments:
            return {"error": f"GitHub API error: {comments['message']}"}
        
        return [
            {
                "id": comment["id"],
                "body": comment["body"],
                "user": comment["user"]["login"],
                "created_at": comment["created_at"],
                "updated_at": comment["updated_at"],
                "path": comment.get("path", "N/A"),
                "line": comment.get("line", "N/A"),
                "url": comment["html_url"]
            }
            for comment in comments
        ]
        
    except Exception as e:
        return {"error": f"Error: {str(e)}"}
