import click
import requests
from agent.services.processUserQuery import GitHubAIAgent
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from ..session.SessionManager import session
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from constants.constants import (
    GITHUB_USER_ENDPOINT, AUTH_BEARER_PREFIX, AUTH_TOKEN_PREFIX,
    HTTP_OK, HTTP_UNAUTHORIZED, HTTP_FORBIDDEN, HTTP_NOT_FOUND,
    ERROR_INVALID_PAT, ERROR_NETWORK, ERROR_INTERNAL,
    SUCCESS_AUTHENTICATED, SUCCESS_SESSION_SAVED,
    PROMPT_ORG, PROMPT_USERNAME, PROMPT_QUERY,
    STATUS_SUCCESS, STATUS_ERROR
)

console = Console()

def validate_github_pat(pat: str):
    """
    Validate GitHub PAT by making a request to GitHub API
    """
    try:
        headers = {"Authorization": f"{AUTH_BEARER_PREFIX} {pat}"}
        response = requests.get(GITHUB_USER_ENDPOINT, headers=headers)
        
        if response.status_code == HTTP_OK:
            user_data = response.json()
            return {
                "status": STATUS_SUCCESS,
                "message": SUCCESS_AUTHENTICATED.format(username=user_data.get('login', 'Unknown')),
                "user": {
                    "login": user_data.get('login'),
                    "name": user_data.get('name'),
                    "email": user_data.get('email')
                }
            }
        elif response.status_code == HTTP_UNAUTHORIZED:
            return {
                "status": STATUS_ERROR,
                "message": ERROR_INVALID_PAT
            }
        else:
            return {
                "status": STATUS_ERROR,
                "message": f"GitHub API error: {response.status_code}"
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "status": STATUS_ERROR,
            "message": f"{ERROR_NETWORK}: {str(e)}"
        }
    except Exception as e:
        return {
            "status": STATUS_ERROR,
            "message": f"{ERROR_INTERNAL}: {str(e)}"
        }

def loginUser(pat: str):
    """
    Login user by validating GitHub PAT
    """
    # Validate PAT using GitHub API
    result = validate_github_pat(pat)
    
    print(f"Authentication Status: {result['status']}")
    
    if result["status"] == STATUS_ERROR:
        click.secho(f"❌ {result['message']}", fg="red")
        return False
    
    # Authentication successful
    session.set_pat(pat)
    click.secho(f"✅ {result['message']}", fg="green")
    
    # Ask for organization after successful login
    org = click.prompt(PROMPT_ORG)
    session.set_org(org)
    
    # Ask for username for "my PRs" queries
    username = click.prompt(PROMPT_USERNAME)
    session.set_user(username)
    
    # Show session saved message only once
    click.secho(f"✅ {SUCCESS_SESSION_SAVED}", fg="green")
    
    # Start chat immediately
    start_chat()
    return True

def start_chat():
    """Start the chat loop"""
    while True:
        query = click.prompt(PROMPT_QUERY)
        if query.strip().lower() == "exit":
            click.secho("👋 Goodbye!", fg="cyan")
            break

        response = GitHubAIAgent.callLLM(query)
        console.print(Panel(response, title="🤖 Bot Response", border_style="blue"))