import requests
import logging
import re
from typing import Dict, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelContextClient:
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        logger.info(f"Initialized ModelContextClient with server URL: {server_url}")
        
        # Check server health on initialization
        try:
            health = requests.get(f"{self.server_url}/health")
            if health.status_code == 200:
                health_data = health.json()
                logger.info(f"Server health: {health_data}")
                if health_data.get("llama_status") != "connected":
                    logger.warning(f"Llama status is: {health_data.get('llama_status')}")
                if health_data.get("github_status") != "connected":
                    logger.warning(f"GitHub status is: {health_data.get('github_status')}")
            else:
                logger.warning(f"Server health check failed: {health.status_code}")
        except Exception as e:
            logger.error(f"Could not connect to MCP server: {e}")
    
    def get_context(self, 
                   query_text: str, 
                   user_id: Optional[str] = None,
                   session_id: Optional[str] = None,
                   additional_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Fetch context information from the Model Context Protocol server.
        """
        request_data = {
            "query_text": query_text,
            "user_id": user_id,
            "session_id": session_id,
            "additional_context": additional_context or {}
        }
        
        logger.info(f"Sending context request for query: {query_text}")
        
        try:
            response = requests.post(
                f"{self.server_url}/context", 
                json=request_data,
                timeout=10  # Increased timeout for processing
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching context: {e}")
            return {"error": str(e)}
    
    def list_github_files(self, repo_url: str) -> Dict[str, Any]:
        """
        List files in a GitHub repository using the dedicated endpoint.
        """
        logger.info(f"Listing files for GitHub repository: {repo_url}")
        
        try:
            response = requests.post(
                f"{self.server_url}/github/list-files",
                json={"repo_url": repo_url},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error listing GitHub files: {e}")
            return {"error": str(e), "success": False}

class AIAssistant:
    def __init__(self, context_client: ModelContextClient):
        self.context_client = context_client
    
    def generate_response(self, user_query: str) -> str:
        """
        Generate a response to the user query with context enhancement.
        """
        # Check if this is a GitHub file listing request
        github_url_match = re.search(r"https?://(?:www\.)?github\.com/[^/\s]+/[^/\s]+", user_query)
        github_request = ("github" in user_query.lower() and 
                          ("list" in user_query.lower() or "files" in user_query.lower()))
        
        if github_request and github_url_match:
            # Use dedicated GitHub endpoint
            github_url = github_url_match.group(0)
            result = self.context_client.list_github_files(github_url)
            
            if result.get("success", False):
                files = result.get("files", [])
                if files:
                    response = f"Files in {result.get('owner')}/{result.get('repository')}:\n\n"
                    response += "\n".join(files)
                else:
                    response = f"The repository {result.get('owner')}/{result.get('repository')} appears to be empty."
            else:
                # Fall back to context API if dedicated endpoint fails
                context_data = self.context_client.get_context(user_query)
                if "error" in context_data:
                    return f"Sorry, I couldn't list the GitHub repository files: {result.get('message', 'Unknown error')}"
                
                context_elements = context_data.get("context_elements", [])
                if context_elements:
                    response = context_elements[0]["content"]
                else:
                    response = "I couldn't retrieve any information about the GitHub repository."
        else:
            # Use regular context API for non-GitHub queries
            context_data = self.context_client.get_context(user_query)
            
            if "error" in context_data:
                return f"Sorry, I couldn't generate a proper response due to: {context_data['error']}"
            
            context_elements = context_data.get("context_elements", [])
            
            if not context_elements:
                return "I don't have enough information to answer that question."
            
            # Return the content from the context response
            response = context_elements[0]["content"]
        
        return response

def main():
    # Create a client connected to our MCP server
    context_client = ModelContextClient()
    
    # Initialize an assistant that uses the context
    assistant = AIAssistant(context_client)
    
    print("AI Assistant with Llama and GitHub integration")
    print("Type 'exit' to quit")
    print("You can ask questions or request GitHub repository files with a query like:")
    print("'List files from https://github.com/username/repository'")
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == 'exit':
            break
            
        response = assistant.generate_response(user_input)
        print(f"\nAssistant: {response}")

if __name__ == "__main__":
    main()