from calendar import prmonth
from dotenv import load_dotenv
from openai import OpenAI
from ..template.agentTemplate import system_prompt
from ..template.toolsTemplate import TOOLS
import json
from ..tools.tools import get_pull_requests_by_author, get_pr_review_comments, get_issues_assigned_to_me
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from cli.session.SessionManager import session
import traceback

class GitHubAIAgent:
    load_dotenv()

    # Initialize the OpenAI client but point it to DeepSeek’s API
    client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com"
    )

    conversation = [
        {"role": "system", "content": system_prompt}
    ]

    @classmethod
    def callLLM(cls, prompt: str):
        """
        Call the LLM with the user's prompt and handle tool calls
        """
        # Add user message to conversation
        cls.conversation.append({"role": "user", "content": prompt})
        
        try:
            # Make initial request to LLM
            response = cls.client.chat.completions.create(
                model="deepseek-chat",
                messages=cls.conversation,
                tools=TOOLS,
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            
            # Handle case where content might be None
            content = message.content if message.content is not None else ""
            
            # Add assistant's response to conversation
            assistant_message = {
                "role": "assistant", 
                "content": content
            }
            
            # Only add tool_calls if they exist
            if message.tool_calls:
                assistant_message["tool_calls"] = message.tool_calls
                
            cls.conversation.append(assistant_message)
            
            # Handle tool calls if any
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # Execute the appropriate tool function
                    if function_name == "get_issues_assigned_to_me":
                        repo = function_args.get("repo") 
                        if not repo:
                            result = {"error": "Repository name is required for fetching issues"}
                        else:
                            result = get_issues_assigned_to_me(repo=repo)
                    elif function_name == "get_pull_requests_by_author":
                        result = get_pull_requests_by_author(
                            repo=function_args["repo"]
                        )
                    elif function_name == "get_pr_review_comments":
                        result = get_pr_review_comments(
                            org=function_args["org"],
                            repo=function_args["repo"],
                            pr_number=function_args["pr_number"]
                        )
                    else:
                        result = f"Unknown function: {function_name}"
                    
                    
                    # Add tool result to conversation
                    cls.conversation.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result)
                    })
                
                # Make another request to get the final response with tool results
                final_response = cls.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=cls.conversation,
                    tools=TOOLS,
                    tool_choice="auto"
                )
                
                final_message = final_response.choices[0].message
                final_content = final_message.content if final_message.content is not None else ""
                
                cls.conversation.append({
                    "role": "assistant",
                    "content": final_content
                })
                
                return final_content
            
            return content
            
        except Exception as e:
            print(f"Detailed error: {e}")
            traceback.print_exc()
            return f"Error calling LLM: {str(e)}"

    @classmethod
    def reset_conversation(cls):
        """
        Reset the conversation history
        """
        cls.conversation = [
            {"role": "system", "content": system_prompt}
        ]

        
