TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_issues_assigned_to_me",
            "description": "Get all issues assigned to the current user in a specific repository",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo": {
                        "type": "string",
                        "description": "The repository name"
                    }
                },
                "required": ["repo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_pull_requests_by_author",
            "description": "Get pull requests created by the current user in a specific repository",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo": {
                        "type": "string",
                        "description": "The repository name"
                    }
                },
                "required": ["repo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_pr_review_comments",
            "description": "Get review comments for a specific pull request",
            "parameters": {
                "type": "object",
                "properties": {
                    "org": {
                        "type": "string",
                        "description": "The GitHub organization name"
                    },
                    "repo": {
                        "type": "string",
                        "description": "The repository name"
                    },
                    "pr_number": {
                        "type": "string",
                        "description": "The pull request number"
                    }
                },
                "required": ["org", "repo", "pr_number"]
            }
        }
    }
]
