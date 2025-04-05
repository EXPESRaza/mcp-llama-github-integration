# Model Context Protocol Server with Llama and GitHub Integration

This repository contains a Model Context Protocol (MCP) server implementation that integrates with a locally running Llama model and provides GitHub repository file listing capabilities. The MCP server enhances AI applications with relevant information from both a local LLM and GitHub repositories.

## Overview

The project consists of two main components:

1. **MCP Server** - A FastAPI-based server that:
   - Implements the Model Context Protocol
   - Forwards queries to a local Llama model
   - Lists files from GitHub repositories
2. **Python Client** - A sample client application that demonstrates how to interact with the MCP server

## Prerequisites

- Python 3.7 or higher
- A running Llama model server (e.g., Ollama) at http://localhost:11434/
- Internet connection for GitHub API access
- Git installed on your machine
- GitHub account

## Installation

### Clone the Repository

```bash
git clone https://github.com/YourUsername/mcp-llama-integration.git
cd mcp-llama-integration
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

## File Structure

```
mcp-llama-integration/
├── llama_mcp_server.py      # MCP server with Llama and GitHub integration
├── llama_client_app.py      # Sample client application
└── README.md                # Project documentation
```

## Setting Up the Llama Model

1. If you haven't already, install [Ollama](https://ollama.ai/download)
2. Pull the Llama model:
   ```bash
   ollama pull llama3.2
   ```
3. Verify the model is running:
   ```bash
   curl http://localhost:11434/api/tags
   http://localhost:11434
   http://localhost:11434/api/tags
   ```
   ![image](https://github.com/user-attachments/assets/ce4d8ec5-16e6-4233-9b1e-e08420c04a87)

## Running the MCP Server

1. Start the server:
   ```bash
   python llama_mcp_server.py
   ```
2. The server will start running on `http://localhost:8000`
3. You can verify the server is running by checking the health endpoint:
   ```bash
   curl http://localhost:8000/health
   ```
   ![image](https://github.com/user-attachments/assets/b3b2aa31-cbf6-4a86-b8cd-9cff41f941de)

   ![image](https://github.com/user-attachments/assets/beabe62c-e83c-4b8c-b306-ad52dccf7682)

## Using the Client Application

1. In a separate terminal, start the client application:
   ```bash
   python llama_client_app.py
   ```
2. The application will prompt you for input
3. Type your queries and receive responses from the Llama model
4. To list files from a GitHub repository, use a query like:
   ```
   List files from https://github.com/username/repository
   List files from https://github.com/EXPESRaza/mcp-llama-github-integration
   ```
5. Type 'exit' to quit the application
   ![image](https://github.com/user-attachments/assets/b10665be-68d7-4eb3-9b36-7a385db3d5b7)

## API Documentation

### MCP Server Endpoints

#### POST /context

Request a context for a given query. Can also handle GitHub repository listing.

**Request Body:**

```json
{
  "query_text": "Your query here or 'List files from https://github.com/username/repo'",
  "user_id": "optional-user-id",
  "session_id": "optional-session-id",
  "additional_context": {}
}
```

**Response:**

```json
{
  "context_elements": [
    {
      "content": "Response from Llama model or GitHub file listing",
      "source": "llama_model or github_api",
      "relevance_score": 0.9
    }
  ],
  "metadata": {
    "processing_time_ms": 150,
    "query": "Your query here"
  }
}
```

#### POST /github/list-files

Dedicated endpoint for listing files in a GitHub repository.

**Request Body:**

```json
{
  "repo_url": "https://github.com/username/repository"
}
```

**Response:**

```json
{
  "files": ["📄 README.md", "📁 src", "📄 LICENSE"],
  "repository": "repository",
  "owner": "username",
  "success": true,
  "message": null
}
```

#### GET /health

Check the health status of the MCP server and its connections.

**Response:**

```json
{
  "status": "healthy",
  "llama_status": "connected",
  "github_status": "connected"
}
```

## Customization

### Changing the Llama Model

If you want to use a different Llama model, modify the `model` parameter in the `query_llama` function in `llama_mcp_server.py`:

```python
payload = {
    "model": "your-model-name",  # Change this to your model name
    "prompt": text,
    "stream": False
}
```

### Modifying the GitHub API Integration

The server currently lists files only from the root directory of a repository. To support subdirectories or other GitHub features, modify the `list_github_repo_files` function in `llama_mcp_server.py`.

## Error Handling

The application includes robust error handling for both the Llama model and GitHub API:

1. If the Llama model is unavailable, an error message will be returned
2. If a GitHub repository URL is invalid, the user will be notified
3. If the GitHub API returns an error (e.g., repository not found, rate limiting), an appropriate error message will be shown

## Troubleshooting

### Common Issues

1. **Connection Refused Error**

   - Make sure the Llama model is running at http://localhost:11434/
   - Verify Ollama is properly installed and running

2. **GitHub API Errors**

   - Check if the repository URL is correct
   - GitHub API has rate limits for unauthenticated requests

3. **GitHub Repository Not Found**
   - Verify that the repository exists and is public
   - Private repositories require authentication (not implemented in this version)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
