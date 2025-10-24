"""
Constants for GitHub Chatbot application
"""

# GitHub API Configuration
GITHUB_API_BASE_URL = "https://api.github.com"
GITHUB_USER_ENDPOINT = f"{GITHUB_API_BASE_URL}/user"
GITHUB_REPOS_ENDPOINT = f"{GITHUB_API_BASE_URL}/orgs/{{org}}/repos"
GITHUB_PULLS_ENDPOINT = f"{GITHUB_API_BASE_URL}/repos/{{org}}/{{repo}}/pulls"
GITHUB_PR_COMMENTS_ENDPOINT = f"{GITHUB_API_BASE_URL}/repos/{{org}}/{{repo}}/pulls/{{pr_number}}/comments"

# Authentication
AUTH_BEARER_PREFIX = "Bearer"
AUTH_TOKEN_PREFIX = "token"

# HTTP Status Codes
HTTP_OK = 200
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404

# Error Messages
ERROR_INVALID_PAT = "Invalid or expired GitHub PAT"
ERROR_RATE_LIMIT = "Rate limit exceeded or insufficient permissions"
ERROR_REPO_NOT_FOUND = "Repository '{org}/{repo}' not found"
ERROR_PR_NOT_FOUND = "PR #{pr_number} not found in repository '{org}/{repo}'"
ERROR_NETWORK = "Network error"
ERROR_INTERNAL = "Internal server error"
ERROR_NO_TOKEN = "No GitHub token found. Please login first"
ERROR_NO_ORG = "No organization set in session. Please set organization first"
ERROR_NO_USER = "No username set in session. Please set username first"

# Success Messages
SUCCESS_AUTHENTICATED = "Successfully authenticated as {username}"
SUCCESS_SESSION_SAVED = "Session configured and saved!"

# UI Messages
PROMPT_ORG = "🏢 Enter your GitHub organization name"
PROMPT_USERNAME = "👤 Enter your GitHub username"
PROMPT_PAT = "🔐 Enter your GitHub PAT"
PROMPT_QUERY = "💬 Ask your Query (or type 'exit' to quit)"

# Status Messages
STATUS_SUCCESS = "success"
STATUS_ERROR = "error"

# File Configuration
CONFIG_FILE_NAME = ".github-chatbot-secrets"
CONFIG_FILE_PERMISSIONS = 0o600

# Encryption Configuration
ENCRYPTION_SALT = b'github-chatbot-salt'
ENCRYPTION_ITERATIONS = 100000

# Default Values
DEFAULT_USERNAME = "default"
