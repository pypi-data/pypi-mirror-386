# Cerevox MCP Server

Model Context Protocol (MCP) server for [Cerevox AI](https://cerevox.ai) - The Data Layer for AI Agents.

This MCP server exposes the full Cerevox API suite through the Model Context Protocol, enabling AI agents to:
- **Parse documents** with industry-leading accuracy (Lexa API)
- **Search and query** document collections with RAG (Hippo API)
- **Manage accounts** and users (Account API)

## Features

### Lexa - Document Parsing
- Parse documents from URLs with AI-powered extraction
- Support for PDF, DOCX, TXT, HTML, and 12+ formats
- Extract text, tables, images, and metadata
- Monitor processing jobs in real-time

### Hippo - RAG & Semantic Search
- Create and manage document folders
- Upload files from URLs for processing
- Create chat sessions for Q&A
- Ask questions with AI-powered answers and source citations
- Retrieve conversation history
- Manage files and folders

### Account - User Management
- Get account information and usage metrics
- View plan details and limits
- List and manage users
- Track API usage and billing

## Installation

### Prerequisites

- Python 3.9 or higher
- Cerevox API key ([get one here](https://cerevox.ai))

### Install from source

```bash
# Clone the repository
git clone https://github.com/CerevoxAI/cerevox-mcp-server.git
cd cerevox-mcp-server

# Install in development mode
pip install -e .
```

### Install from PyPI (coming soon)

```bash
pip install cerevox-mcp-server
```

## Configuration

### Set up your API key

The server requires a Cerevox API key. Set it as an environment variable:

```bash
export CEREVOX_API_KEY="your-api-key-here"
```

Or add it to your shell configuration file (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
echo 'export CEREVOX_API_KEY="your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

### Configure with Claude Desktop

Add this to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "cerevox": {
      "command": "python",
      "args": ["-m", "cerevox_mcp_server"],
      "env": {
        "CEREVOX_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### Configure with other MCP clients

For other MCP clients, refer to their documentation for connecting to MCP servers. Generally, you'll need to:

1. Point the client to the server: `python -m cerevox_mcp_server`
2. Ensure the `CEREVOX_API_KEY` environment variable is set

## Usage Examples

### Document Parsing with Lexa

Parse a document and extract structured content:

```
Use the lexa_parse_document tool to parse this PDF: https://example.com/document.pdf
```

The AI will extract text, tables, and metadata from the document.

### RAG Search with Hippo

Create a folder, upload documents, and ask questions:

```
1. Create a folder called "research_papers" with ID "research"
2. Upload this file: https://arxiv.org/pdf/2301.00001.pdf
3. Create a chat session for the "research" folder
4. Ask: "What are the main findings of this paper?"
```

The AI will:
1. Create the folder
2. Upload and process the document
3. Create a chat session
4. Answer your question using RAG with source citations

### Account Management

Check your account usage:

```
1. Get my account information
2. Show my usage metrics
3. List all users in the account
```

## Available Tools

### Lexa Tools

| Tool | Description |
|------|-------------|
| `lexa_parse_document` | Parse document from URL with AI extraction |
| `lexa_get_job_status` | Check status of parsing job |

### Hippo Folder Tools

| Tool | Description |
|------|-------------|
| `hippo_create_folder` | Create a new document folder |
| `hippo_list_folders` | List all folders |
| `hippo_get_folder` | Get folder details |
| `hippo_delete_folder` | Delete a folder and all contents |

### Hippo File Tools

| Tool | Description |
|------|-------------|
| `hippo_upload_file_url` | Upload file from URL |
| `hippo_list_files` | List files in a folder |
| `hippo_get_file` | Get file details |
| `hippo_delete_file` | Delete a file |

### Hippo Chat/Q&A Tools

| Tool | Description |
|------|-------------|
| `hippo_create_chat` | Create chat session for Q&A |
| `hippo_list_chats` | List all chat sessions |
| `hippo_ask_question` | Ask question with RAG (primary tool) |
| `hippo_get_chat_history` | Get conversation history |
| `hippo_get_question_details` | Get full details of a Q&A |
| `hippo_delete_chat` | Delete chat session |

### Account Tools

| Tool | Description |
|------|-------------|
| `account_get_info` | Get account information |
| `account_get_usage` | Get usage metrics |
| `account_get_plan` | Get plan details and limits |
| `account_list_users` | List all users |
| `account_get_current_user` | Get current user info |

## Development

### Setup development environment

```bash
# Clone and install with dev dependencies
git clone https://github.com/CerevoxAI/cerevox-mcp-server.git
cd cerevox-mcp-server
pip install -e ".[dev]"
```

### Run tests

```bash
pytest
```

### Code formatting

```bash
black src/
```

### Type checking

```bash
mypy src/
```

## Architecture

The server is built on:
- **MCP Python SDK** - Model Context Protocol implementation
- **cerevox-python** - Official Cerevox Python SDK
- **AsyncIO** - Asynchronous operations for optimal performance

### Tool Design

Each tool follows a consistent pattern:
1. **Input validation** - Validates required parameters
2. **Client initialization** - Reuses authenticated clients
3. **API call** - Executes the Cerevox API operation
4. **Response formatting** - Returns structured JSON responses
5. **Error handling** - Provides clear error messages

### Authentication

The server handles authentication automatically:
- API key loaded from `CEREVOX_API_KEY` environment variable
- Clients initialized lazily on first use
- Sessions maintained for optimal performance
- Automatic token refresh handled by cerevox-python SDK

## Troubleshooting

### "CEREVOX_API_KEY environment variable not set"

Make sure you've set the environment variable:
```bash
export CEREVOX_API_KEY="your-api-key-here"
```

### "Connection refused" or "Server not responding"

Ensure the MCP server is running and your client is configured correctly. Check logs for detailed error messages.

### "Authentication failed"

Verify your API key is valid and has the necessary permissions. Get a new key at https://cerevox.ai

### Document parsing is slow

Large documents may take several minutes to process. Use the `lexa_get_job_status` tool to monitor progress.

## Examples

### Complete RAG Workflow

```python
# This would be done through an MCP client like Claude Desktop

# 1. Create a folder for your documents
"Create a Hippo folder with ID 'my_docs' and name 'My Documents'"

# 2. Upload documents
"Upload https://example.com/report.pdf to the 'my_docs' folder"

# 3. Wait for processing (check file status)
"List files in the 'my_docs' folder to check processing status"

# 4. Create a chat session
"Create a chat session for the 'my_docs' folder"

# 5. Ask questions
"Ask in chat [chat_id]: What are the key recommendations in the report?"

# 6. Follow-up questions
"Ask in chat [chat_id]: Can you elaborate on the financial projections?"

# 7. Get conversation history
"Show me the conversation history for chat [chat_id]"
```

### Document Analysis

```python
# Parse a document and analyze its content
"Parse this document: https://example.com/contract.pdf using advanced mode"

# The response will include:
# - Extracted text content
# - Number of pages
# - Number of tables found
# - Content preview
```

### Account Monitoring

```python
# Check account status and usage
"Get my account information"
"Show my usage metrics"
"What's my current plan and its limits?"
```

## Support

- **Documentation**: https://docs.cerevox.ai
- **GitHub Issues**: https://github.com/CerevoxAI/cerevox-mcp-server/issues
- **Discord**: https://discord.gg/cerevox
- **Email**: support@cerevox.ai

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Links

- [Cerevox AI](https://cerevox.ai)
- [Cerevox Python SDK](https://github.com/CerevoxAI/cerevox-python)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

---

Made with ❤️ by the Cerevox team

Happy Building! 🔍 🦛 ✨
