from fastapi import FastAPI
import uvicorn
import logging
import requests
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define data models
class ContextRequest(BaseModel):
    query_text: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    additional_context: Optional[Dict[str, Any]] = None

class ContextResponse(BaseModel):
    context_elements: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None

class LlamaRequest(BaseModel):
    model: str = "llama3.2"  # Default model, update as needed
    prompt: str
    stream: bool = False
    options: Optional[Dict[str, Any]] = None

class GitHubListFilesRequest(BaseModel):
    repo_url: str

class GitHubListFilesResponse(BaseModel):
    files: List[str]
    repository: str
    owner: str
    success: bool
    message: Optional[str] = None

# Initialize FastAPI app
app = FastAPI(title="Model Context Protocol Server with Llama and GitHub Integration")

# Llama API endpoint
LLAMA_API_URL = "http://localhost:11434/api/generate"

def query_llama(text: str) -> str:
    """Query local Llama model for information."""
    try:
        payload = {
            "model": "llama3",  # Update to match your specific model
            "prompt": text,
            "stream": False
        }
        
        logger.info(f"Querying Llama model with: {text}")
        response = requests.post(LLAMA_API_URL, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "No response from model")
        else:
            logger.error(f"Error from Llama API: {response.status_code} - {response.text}")
            return f"Error querying model: {response.status_code}"
            
    except Exception as e:
        logger.error(f"Exception when querying Llama: {str(e)}")
        return f"Error: {str(e)}"

def parse_github_url(url: str) -> Union[Dict[str, str], None]:
    """
    Parse a GitHub URL to extract owner and repository name.
    Returns None if the URL is not a valid GitHub repository URL.
    """
    # Match patterns like:
    # https://github.com/owner/repo
    # https://github.com/owner/repo.git
    # github.com/owner/repo
    pattern = r"(?:https?://)?(?:www\.)?github\.com/([^/]+)/([^/\.]+)(?:\.git)?"
    match = re.match(pattern, url)
    
    if match:
        return {
            "owner": match.group(1),
            "repo": match.group(2)
        }
    return None

def list_github_repo_files(owner: str, repo: str, path: str = "") -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """
    List files in a GitHub repository at the specified path.
    Returns a list of file information or an error dictionary.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            contents = response.json()
            return contents
        else:
            error_message = response.json().get("message", f"Error: Status code {response.status_code}")
            return {"error": error_message}
            
    except Exception as e:
        return {"error": str(e)}

@app.post("/context", response_model=ContextResponse)
async def get_context(request: ContextRequest):
    logger.info(f"Received context request: {request}")
    
    # Check if it's a GitHub repository listing request
    if "github" in request.query_text.lower() and ("list" in request.query_text.lower() or "files" in request.query_text.lower()):
        # Extract GitHub URL using regex
        url_pattern = r"https?://(?:www\.)?github\.com/[^/\s]+/[^/\s]+"
        url_match = re.search(url_pattern, request.query_text)
        
        if url_match:
            github_url = url_match.group(0)
            repo_info = parse_github_url(github_url)
            
            if repo_info:
                files_data = list_github_repo_files(repo_info["owner"], repo_info["repo"])
                
                if "error" not in files_data:
                    # Create a formatted list of files
                    file_list = []
                    directory_list = []
                    
                    for item in files_data:
                        if item["type"] == "file":
                            file_list.append(f"📄 {item['name']}")
                        else:
                            directory_list.append(f"📁 {item['name']}")
                    
                    all_items = directory_list + file_list
                    
                    content = f"Repository: {repo_info['owner']}/{repo_info['repo']}\n\n"
                    content += "Files and directories:\n" + "\n".join(all_items)
                    
                    context_elements = [{
                        "content": content,
                        "source": "github_api",
                        "relevance_score": 0.95
                    }]
                else:
                    error_msg = files_data.get("error", "Unknown error when accessing GitHub repository")
                    context_elements = [{
                        "content": f"Error accessing GitHub repository: {error_msg}",
                        "source": "github_api_error",
                        "relevance_score": 0.9
                    }]
            else:
                context_elements = [{
                    "content": "The GitHub URL provided is not valid. Please provide a URL in the format: https://github.com/owner/repo",
                    "source": "github_url_parser",
                    "relevance_score": 0.9
                }]
        else:
            # No valid GitHub URL found, use Llama model
            prompt = f"""Please provide relevant information for the following query: 
            {request.query_text}
            
            Respond with factual, helpful information."""
            
            llama_response = query_llama(prompt)
            
            context_elements = [{
                "content": llama_response,
                "source": "llama_model",
                "relevance_score": 0.9
            }]
    else:
        # Not a GitHub request, use Llama model
        prompt = f"""Please provide relevant information for the following query: 
        {request.query_text}
        
        Respond with factual, helpful information."""
        
        llama_response = query_llama(prompt)
        
        context_elements = [{
            "content": llama_response,
            "source": "llama_model",
            "relevance_score": 0.9
        }]
    
    logger.info("Context retrieved")
    return ContextResponse(
        context_elements=context_elements,
        metadata={
            "processing_time_ms": 150,
            "query": request.query_text
        }
    )

@app.post("/github/list-files", response_model=GitHubListFilesResponse)
async def list_files(request: GitHubListFilesRequest):
    """
    Dedicated endpoint to list files from a GitHub repository.
    """
    logger.info(f"GitHub list files request for: {request.repo_url}")
    
    repo_info = parse_github_url(request.repo_url)
    
    if not repo_info:
        return GitHubListFilesResponse(
            files=[],
            repository="",
            owner="",
            success=False,
            message="Invalid GitHub repository URL. Please provide a URL in the format: https://github.com/owner/repo"
        )
    
    files_data = list_github_repo_files(repo_info["owner"], repo_info["repo"])
    
    if "error" in files_data:
        return GitHubListFilesResponse(
            files=[],
            repository=repo_info["repo"],
            owner=repo_info["owner"],
            success=False,
            message=f"Error accessing repository: {files_data['error']}"
        )
    
    file_list = []
    for item in files_data:
        file_type_prefix = "📁 " if item["type"] == "dir" else "📄 "
        file_list.append(f"{file_type_prefix}{item['path']}")
    
    return GitHubListFilesResponse(
        files=file_list,
        repository=repo_info["repo"],
        owner=repo_info["owner"],
        success=True
    )

@app.get("/health")
async def health_check():
    # Check if Llama API is accessible
    try:
        response = requests.get("http://localhost:11434/api/tags")
        llama_status = "connected" if response.status_code == 200 else "unavailable"
    except Exception as e:
        llama_status = f"error: {str(e)}"
    
    # Check if GitHub API is accessible
    try:
        response = requests.get("https://api.github.com/rate_limit")
        github_status = "connected" if response.status_code == 200 else "unavailable"
    except Exception as e:
        github_status = f"error: {str(e)}"
    
    return {
        "status": "healthy" if llama_status == "connected" and github_status == "connected" else "degraded",
        "llama_status": llama_status,
        "github_status": github_status
    }

if __name__ == "__main__":
    logger.info("Starting Model Context Protocol server with Llama and GitHub integration")
    uvicorn.run(app, host="0.0.0.0", port=8000)