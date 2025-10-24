import click
import os
import subprocess
import sys
from .ApiUtil.UserService import loginUser
from .session.SessionManager import session
from agent.services.processUserQuery import GitHubAIAgent
from rich.console import Console
from rich.panel import Panel
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
from constants.constants import PROMPT_PAT, PROMPT_QUERY

@click.group()
def cli():
    """GitHub Chatbot CLI"""
    pass

@cli.command()
def start():
    """Start the GitHub Chatbot"""
    click.secho("👋 Welcome to GitHub Chatbot CLI!", fg="cyan", bold=True)
    
    # Check if session is already available
    if session.get_pat() and session.get_org() and session.get_user():
        click.secho("✅ Using saved session:", fg="green")
        click.secho(f"   🏢 Organization: {session.get_org()}", fg="cyan")
        click.secho(f"   👤 Username: {session.get_user()}", fg="cyan")
        
        if click.confirm("Do you want to continue with saved session?"):
            start_chat()
            return
        else:
            session.clear_session()
    
    # If no saved session or user wants to login again
    pat = click.prompt(PROMPT_PAT, hide_input=False)
    
    # Try to login with provided PAT
    if not loginUser(pat):
        click.secho("❌ Login failed. Please try again.", fg="red")
        return

def start_chat():
    """Start the chat loop"""
    
    console = Console()
    
    while True:
        query = click.prompt(PROMPT_QUERY)
        if query.strip().lower() == "exit":
            click.secho("👋 Goodbye!", fg="cyan")
            break

        response = GitHubAIAgent.callLLM(query)
        console.print(Panel(response, title="🤖 Bot Response", border_style="blue"))

@cli.command()
def logout():
    """Clear saved session data"""
    session.clear_session()

if __name__ == "__main__":
    cli()