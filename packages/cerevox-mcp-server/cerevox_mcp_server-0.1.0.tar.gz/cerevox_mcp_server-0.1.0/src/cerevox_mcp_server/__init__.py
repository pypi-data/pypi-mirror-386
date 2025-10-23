"""
Cerevox MCP Server

Exposes Cerevox AI APIs (Lexa, Hippo, Account) through the Model Context Protocol.
Enables AI agents to parse documents, perform RAG searches, and manage accounts.
"""

import asyncio
import json
import logging
import os
from typing import Any, Optional

from cerevox import AsyncLexa, AsyncHippo, Account
from cerevox.core import ProcessingMode, ResponseType, ReasoningLevel
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Server instance
app = Server("cerevox-mcp-server")

# Global clients (initialized with API key from environment)
_lexa_client: Optional[AsyncLexa] = None
_hippo_client: Optional[AsyncHippo] = None
_account_client: Optional[Account] = None


def get_api_key() -> str:
    """Get API key from environment variable."""
    api_key = os.getenv("CEREVOX_API_KEY")
    if not api_key:
        raise ValueError(
            "CEREVOX_API_KEY environment variable not set. "
            "Please set it to your Cerevox API key."
        )
    return api_key


async def get_lexa_client() -> AsyncLexa:
    """Get or create async Lexa client."""
    global _lexa_client
    if _lexa_client is None:
        api_key = get_api_key()
        _lexa_client = AsyncLexa(api_key=api_key)
    return _lexa_client


async def get_hippo_client() -> AsyncHippo:
    """Get or create async Hippo client."""
    global _hippo_client
    if _hippo_client is None:
        api_key = get_api_key()
        _hippo_client = AsyncHippo(api_key=api_key)
    return _hippo_client


def get_account_client() -> Account:
    """Get or create Account client (sync)."""
    global _account_client
    if _account_client is None:
        api_key = get_api_key()
        _account_client = Account(api_key=api_key)
    return _account_client


# ============================================================================
# Tool Definitions
# ============================================================================

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available MCP tools."""
    return [
        # Lexa - Document Parsing Tools
        Tool(
            name="lexa_parse_document",
            description=(
                "Parse a document using Cerevox Lexa AI. "
                "Extracts text, tables, images, and metadata from documents. "
                "Supports PDF, DOCX, TXT, HTML, and more. Returns structured content."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "file_url": {
                        "type": "string",
                        "description": "URL of the document to parse (publicly accessible)",
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["default", "fast", "advanced"],
                        "default": "default",
                        "description": "Processing mode: 'default' (balanced), 'fast' (quick), 'advanced' (highest quality)",
                    },
                },
                "required": ["file_url"],
            },
        ),
        Tool(
            name="lexa_get_job_status",
            description=(
                "Check the status of a Lexa document parsing job. "
                "Use this to monitor long-running parsing operations."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "request_id": {
                        "type": "string",
                        "description": "Job request ID returned from parse operation",
                    },
                },
                "required": ["request_id"],
            },
        ),

        # Hippo - Folder Management Tools
        Tool(
            name="hippo_create_folder",
            description=(
                "Create a new folder in Hippo for organizing documents. "
                "Folders are used to group related documents for RAG operations."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_id": {
                        "type": "string",
                        "description": "Unique identifier for the folder (alphanumeric, underscores, hyphens)",
                    },
                    "folder_name": {
                        "type": "string",
                        "description": "Human-readable display name for the folder",
                    },
                },
                "required": ["folder_id", "folder_name"],
            },
        ),
        Tool(
            name="hippo_list_folders",
            description=(
                "List all folders in Hippo. "
                "Optionally filter by name substring."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "search_name": {
                        "type": "string",
                        "description": "Optional substring to filter folder names",
                    },
                },
            },
        ),
        Tool(
            name="hippo_get_folder",
            description=(
                "Get detailed information about a specific folder. "
                "Returns metadata, file count, and processing status."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_id": {
                        "type": "string",
                        "description": "Unique identifier of the folder",
                    },
                },
                "required": ["folder_id"],
            },
        ),
        Tool(
            name="hippo_delete_folder",
            description=(
                "Delete a folder and all its contents permanently. "
                "This operation cannot be undone."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_id": {
                        "type": "string",
                        "description": "Unique identifier of the folder to delete",
                    },
                },
                "required": ["folder_id"],
            },
        ),

        # Hippo - File Management Tools
        Tool(
            name="hippo_upload_file_url",
            description=(
                "Upload a file from a URL to a Hippo folder for RAG processing. "
                "The file will be parsed and indexed for semantic search."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_id": {
                        "type": "string",
                        "description": "Folder identifier to upload the file to",
                    },
                    "file_url": {
                        "type": "string",
                        "description": "URL of the file to upload (must be publicly accessible)",
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["default", "advanced"],
                        "default": "default",
                        "description": "Processing mode for document extraction",
                    },
                },
                "required": ["folder_id", "file_url"],
            },
        ),
        Tool(
            name="hippo_list_files",
            description=(
                "List all files in a Hippo folder. "
                "Optionally filter by filename substring."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_id": {
                        "type": "string",
                        "description": "Folder identifier to list files from",
                    },
                    "search_name": {
                        "type": "string",
                        "description": "Optional substring to filter filenames",
                    },
                },
                "required": ["folder_id"],
            },
        ),
        Tool(
            name="hippo_get_file",
            description=(
                "Get detailed information about a specific file. "
                "Returns metadata, processing status, and file details."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_id": {
                        "type": "string",
                        "description": "Folder identifier containing the file",
                    },
                    "file_id": {
                        "type": "string",
                        "description": "Unique identifier of the file",
                    },
                },
                "required": ["folder_id", "file_id"],
            },
        ),
        Tool(
            name="hippo_delete_file",
            description=(
                "Delete a specific file from a folder. "
                "This permanently removes the file and its embeddings."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_id": {
                        "type": "string",
                        "description": "Folder identifier containing the file",
                    },
                    "file_id": {
                        "type": "string",
                        "description": "Unique identifier of the file to delete",
                    },
                },
                "required": ["folder_id", "file_id"],
            },
        ),

        # Hippo - Chat and Q&A Tools
        Tool(
            name="hippo_create_chat",
            description=(
                "Create a new chat session for Q&A on a folder's documents. "
                "Chat sessions maintain conversation context for follow-up questions."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_id": {
                        "type": "string",
                        "description": "Folder identifier to create chat session for",
                    },
                },
                "required": ["folder_id"],
            },
        ),
        Tool(
            name="hippo_list_chats",
            description=(
                "List all chat sessions. "
                "Optionally filter by folder ID."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_id": {
                        "type": "string",
                        "description": "Optional folder ID to filter chats",
                    },
                },
            },
        ),
        Tool(
            name="hippo_ask_question",
            description=(
                "Ask a question about documents in a chat session using RAG. "
                "Returns AI-generated answers with source citations. "
                "This is the primary tool for extracting insights from documents."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "description": "Chat session identifier",
                    },
                    "query": {
                        "type": "string",
                        "description": "Question to ask about the documents",
                    },
                    "response_type": {
                        "type": "string",
                        "enum": ["answers", "sources"],
                        "default": "answers",
                        "description": "'answers' for AI response with citations, 'sources' for relevant passages only",
                    },
                    "top_k": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 100,
                        "description": "Number of top relevant passages to retrieve (1-100)",
                    },
                    "reasoning_level": {
                        "type": "string",
                        "enum": ["none", "basic", "detailed"],
                        "default": "none",
                        "description": "Level of reasoning to include in the response",
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["lite", "pro"],
                        "default": "lite",
                        "description": "Query processing mode: 'lite' (faster) or 'pro' (comprehensive)",
                    },
                },
                "required": ["chat_id", "query"],
            },
        ),
        Tool(
            name="hippo_get_chat_history",
            description=(
                "Get conversation history from a chat session. "
                "Returns all questions and answers with truncated content."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "description": "Chat session identifier",
                    },
                    "msg_maxlen": {
                        "type": "integer",
                        "default": 120,
                        "description": "Maximum character length for truncated messages",
                    },
                },
                "required": ["chat_id"],
            },
        ),
        Tool(
            name="hippo_get_question_details",
            description=(
                "Get complete details for a specific question in chat history. "
                "Returns full query, response, and source citations."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "description": "Chat session identifier",
                    },
                    "ask_index": {
                        "type": "integer",
                        "description": "Zero-based index of the question (use -1 for latest)",
                    },
                    "show_files": {
                        "type": "boolean",
                        "default": False,
                        "description": "Include list of files that were searched",
                    },
                    "show_source": {
                        "type": "boolean",
                        "default": False,
                        "description": "Include raw source passages and similarity scores",
                    },
                },
                "required": ["chat_id", "ask_index"],
            },
        ),
        Tool(
            name="hippo_delete_chat",
            description=(
                "Delete a chat session and all its conversation history. "
                "This operation cannot be undone."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "description": "Chat session identifier to delete",
                    },
                },
                "required": ["chat_id"],
            },
        ),

        # Account Management Tools
        Tool(
            name="account_get_info",
            description=(
                "Get current account information and metadata. "
                "Returns account ID, name, creation date, and status."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="account_get_usage",
            description=(
                "Get account usage metrics and statistics. "
                "Returns API calls, pages processed, and billing information."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "Account ID (use result from account_get_info)",
                    },
                },
                "required": ["account_id"],
            },
        ),
        Tool(
            name="account_get_plan",
            description=(
                "Get account plan information and limits. "
                "Returns plan type, features, and usage limits."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "Account ID (use result from account_get_info)",
                    },
                },
                "required": ["account_id"],
            },
        ),
        Tool(
            name="account_list_users",
            description=(
                "List all users in the account. "
                "Returns user information including IDs, emails, names, and roles."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="account_get_current_user",
            description=(
                "Get information about the currently authenticated user. "
                "Returns user profile with ID, email, name, and permissions."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


# ============================================================================
# Tool Handlers
# ============================================================================

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool execution."""
    try:
        # Lexa Tools
        if name == "lexa_parse_document":
            return await handle_lexa_parse_document(arguments)
        elif name == "lexa_get_job_status":
            return await handle_lexa_get_job_status(arguments)

        # Hippo - Folder Tools
        elif name == "hippo_create_folder":
            return await handle_hippo_create_folder(arguments)
        elif name == "hippo_list_folders":
            return await handle_hippo_list_folders(arguments)
        elif name == "hippo_get_folder":
            return await handle_hippo_get_folder(arguments)
        elif name == "hippo_delete_folder":
            return await handle_hippo_delete_folder(arguments)

        # Hippo - File Tools
        elif name == "hippo_upload_file_url":
            return await handle_hippo_upload_file_url(arguments)
        elif name == "hippo_list_files":
            return await handle_hippo_list_files(arguments)
        elif name == "hippo_get_file":
            return await handle_hippo_get_file(arguments)
        elif name == "hippo_delete_file":
            return await handle_hippo_delete_file(arguments)

        # Hippo - Chat Tools
        elif name == "hippo_create_chat":
            return await handle_hippo_create_chat(arguments)
        elif name == "hippo_list_chats":
            return await handle_hippo_list_chats(arguments)
        elif name == "hippo_ask_question":
            return await handle_hippo_ask_question(arguments)
        elif name == "hippo_get_chat_history":
            return await handle_hippo_get_chat_history(arguments)
        elif name == "hippo_get_question_details":
            return await handle_hippo_get_question_details(arguments)
        elif name == "hippo_delete_chat":
            return await handle_hippo_delete_chat(arguments)

        # Account Tools
        elif name == "account_get_info":
            return await handle_account_get_info(arguments)
        elif name == "account_get_usage":
            return await handle_account_get_usage(arguments)
        elif name == "account_get_plan":
            return await handle_account_get_plan(arguments)
        elif name == "account_list_users":
            return await handle_account_list_users(arguments)
        elif name == "account_get_current_user":
            return await handle_account_get_current_user(arguments)

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]


# ============================================================================
# Lexa Tool Handlers
# ============================================================================

async def handle_lexa_parse_document(arguments: dict[str, Any]) -> list[TextContent]:
    """Parse a document using Lexa."""
    file_url = arguments["file_url"]
    mode = arguments.get("mode", "default")

    # Convert mode string to ProcessingMode enum
    mode_map = {
        "default": ProcessingMode.DEFAULT,
        "fast": ProcessingMode.FAST,
        "advanced": ProcessingMode.ADVANCED,
    }
    processing_mode = mode_map.get(mode, ProcessingMode.DEFAULT)

    client = await get_lexa_client()

    # Parse the document
    documents = await client.parse_urls(file_url, mode=processing_mode)

    # Format response
    result = {
        "success": True,
        "document_count": len(documents),
        "documents": []
    }

    for doc in documents:
        doc_data = {
            "filename": doc.filename if hasattr(doc, "filename") else "unknown",
            "content_length": len(doc.content) if hasattr(doc, "content") else 0,
            "page_count": len(doc.pages) if hasattr(doc, "pages") else 0,
            "table_count": len(doc.tables) if hasattr(doc, "tables") else 0,
            "content_preview": doc.content[:500] if hasattr(doc, "content") else "",
        }
        result["documents"].append(doc_data)

    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


async def handle_lexa_get_job_status(arguments: dict[str, Any]) -> list[TextContent]:
    """Get status of a Lexa parsing job."""
    request_id = arguments["request_id"]

    client = await get_lexa_client()
    status = client._get_job_status(request_id)

    result = {
        "request_id": request_id,
        "status": status.status.value if hasattr(status.status, "value") else str(status.status),
        "progress": status.progress,
        "total_files": status.total_files,
        "completed_files": status.completed_files,
        "failed_chunks": status.failed_chunks,
        "error": status.error,
    }

    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


# ============================================================================
# Hippo Folder Tool Handlers
# ============================================================================

async def handle_hippo_create_folder(arguments: dict[str, Any]) -> list[TextContent]:
    """Create a new Hippo folder."""
    folder_id = arguments["folder_id"]
    folder_name = arguments["folder_name"]

    client = await get_hippo_client()
    response = await client.create_folder(folder_id, folder_name)

    result = {
        "success": True,
        "folder_id": folder_id,
        "folder_name": folder_name,
        "message": "Folder created successfully"
    }

    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


async def handle_hippo_list_folders(arguments: dict[str, Any]) -> list[TextContent]:
    """List Hippo folders."""
    search_name = arguments.get("search_name")

    client = await get_hippo_client()
    folders = await client.get_folders(search_name=search_name)

    result = {
        "success": True,
        "folder_count": len(folders),
        "folders": [
            {
                "folder_id": f.folder_id,
                "folder_name": f.folder_name,
                "created_at": str(f.created_at) if hasattr(f, "created_at") else None,
                "status": f.status if hasattr(f, "status") else None,
            }
            for f in folders
        ]
    }

    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


async def handle_hippo_get_folder(arguments: dict[str, Any]) -> list[TextContent]:
    """Get folder details."""
    folder_id = arguments["folder_id"]

    client = await get_hippo_client()
    folder = await client.get_folder_by_id(folder_id)

    result = {
        "success": True,
        "folder": {
            "folder_id": folder.folder_id,
            "folder_name": folder.folder_name,
            "created_at": str(folder.created_at) if hasattr(folder, "created_at") else None,
            "status": folder.status if hasattr(folder, "status") else None,
        }
    }

    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


async def handle_hippo_delete_folder(arguments: dict[str, Any]) -> list[TextContent]:
    """Delete a Hippo folder."""
    folder_id = arguments["folder_id"]

    client = await get_hippo_client()
    response = await client.delete_folder(folder_id)

    result = {
        "success": True,
        "folder_id": folder_id,
        "message": "Folder deleted successfully"
    }

    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


# ============================================================================
# Hippo File Tool Handlers
# ============================================================================

async def handle_hippo_upload_file_url(arguments: dict[str, Any]) -> list[TextContent]:
    """Upload file from URL to Hippo folder."""
    folder_id = arguments["folder_id"]
    file_url = arguments["file_url"]
    mode = arguments.get("mode", "default")

    mode_map = {
        "default": ProcessingMode.DEFAULT,
        "advanced": ProcessingMode.ADVANCED,
    }
    processing_mode = mode_map.get(mode, ProcessingMode.DEFAULT)

    client = await get_hippo_client()
    response = await client.upload_file_from_url(
        folder_id=folder_id,
        urls=file_url,
        mode=processing_mode
    )

    result = {
        "success": True,
        "folder_id": folder_id,
        "request_id": response.request_id if hasattr(response, "request_id") else None,
        "message": "File upload initiated successfully"
    }

    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


async def handle_hippo_list_files(arguments: dict[str, Any]) -> list[TextContent]:
    """List files in a Hippo folder."""
    folder_id = arguments["folder_id"]
    search_name = arguments.get("search_name")

    client = await get_hippo_client()
    files = await client.get_files(folder_id, search_name=search_name)

    result = {
        "success": True,
        "folder_id": folder_id,
        "file_count": len(files),
        "files": [
            {
                "file_id": f.file_id,
                "filename": f.filename,
                "status": f.status if hasattr(f, "status") else None,
                "uploaded_at": str(f.uploaded_at) if hasattr(f, "uploaded_at") else None,
            }
            for f in files
        ]
    }

    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


async def handle_hippo_get_file(arguments: dict[str, Any]) -> list[TextContent]:
    """Get file details."""
    folder_id = arguments["folder_id"]
    file_id = arguments["file_id"]

    client = await get_hippo_client()
    file = await client.get_file_by_id(folder_id, file_id)

    result = {
        "success": True,
        "file": {
            "file_id": file.file_id,
            "filename": file.filename,
            "status": file.status if hasattr(file, "status") else None,
            "uploaded_at": str(file.uploaded_at) if hasattr(file, "uploaded_at") else None,
        }
    }

    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


async def handle_hippo_delete_file(arguments: dict[str, Any]) -> list[TextContent]:
    """Delete a file from Hippo folder."""
    folder_id = arguments["folder_id"]
    file_id = arguments["file_id"]

    client = await get_hippo_client()
    response = await client.delete_file_by_id(folder_id, file_id)

    result = {
        "success": True,
        "folder_id": folder_id,
        "file_id": file_id,
        "message": "File deleted successfully"
    }

    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


# ============================================================================
# Hippo Chat Tool Handlers
# ============================================================================

async def handle_hippo_create_chat(arguments: dict[str, Any]) -> list[TextContent]:
    """Create a new chat session."""
    folder_id = arguments["folder_id"]

    client = await get_hippo_client()
    response = await client.create_chat(folder_id)

    result = {
        "success": True,
        "chat_id": response.chat_id,
        "folder_id": folder_id,
        "message": "Chat session created successfully"
    }

    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


async def handle_hippo_list_chats(arguments: dict[str, Any]) -> list[TextContent]:
    """List chat sessions."""
    folder_id = arguments.get("folder_id")

    client = await get_hippo_client()
    chats = await client.get_chats(folder_id=folder_id)

    result = {
        "success": True,
        "chat_count": len(chats),
        "chats": [
            {
                "chat_id": c.chat_id,
                "folder_id": c.folder_id,
                "created_at": str(c.created_at) if hasattr(c, "created_at") else None,
            }
            for c in chats
        ]
    }

    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


async def handle_hippo_ask_question(arguments: dict[str, Any]) -> list[TextContent]:
    """Ask a question in a chat session."""
    chat_id = arguments["chat_id"]
    query = arguments["query"]
    response_type_str = arguments.get("response_type", "answers")
    top_k = arguments.get("top_k")
    reasoning_level_str = arguments.get("reasoning_level", "none")
    mode = arguments.get("mode", "lite")

    # Convert string enums
    response_type = ResponseType(response_type_str)
    reasoning_level = ReasoningLevel(reasoning_level_str)

    client = await get_hippo_client()
    response = await client.submit_ask(
        chat_id=chat_id,
        query=query,
        response_type=response_type,
        top_k=top_k,
        reasoning_level=reasoning_level,
        mode=mode,
    )

    result = {
        "success": True,
        "chat_id": chat_id,
        "query": query,
        "response": response.response if hasattr(response, "response") else None,
        "sources": [
            {
                "filename": s.filename if hasattr(s, "filename") else None,
                "content": s.content if hasattr(s, "content") else None,
            }
            for s in (response.sources if hasattr(response, "sources") and response.sources else [])
        ]
    }

    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


async def handle_hippo_get_chat_history(arguments: dict[str, Any]) -> list[TextContent]:
    """Get chat history."""
    chat_id = arguments["chat_id"]
    msg_maxlen = arguments.get("msg_maxlen", 120)

    client = await get_hippo_client()
    asks = await client.get_asks(chat_id, msg_maxlen=msg_maxlen)

    result = {
        "success": True,
        "chat_id": chat_id,
        "conversation_count": len(asks),
        "conversations": [
            {
                "index": i,
                "query": a.query if hasattr(a, "query") else None,
                "response": a.response if hasattr(a, "response") else None,
            }
            for i, a in enumerate(asks)
        ]
    }

    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


async def handle_hippo_get_question_details(arguments: dict[str, Any]) -> list[TextContent]:
    """Get details of a specific question."""
    chat_id = arguments["chat_id"]
    ask_index = arguments["ask_index"]
    show_files = arguments.get("show_files", False)
    show_source = arguments.get("show_source", False)

    client = await get_hippo_client()
    ask = await client.get_ask_by_index(
        chat_id,
        ask_index,
        show_files=show_files,
        show_source=show_source
    )

    result = {
        "success": True,
        "chat_id": chat_id,
        "ask_index": ask_index,
        "query": ask.query if hasattr(ask, "query") else None,
        "response": ask.response if hasattr(ask, "response") else None,
    }

    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


async def handle_hippo_delete_chat(arguments: dict[str, Any]) -> list[TextContent]:
    """Delete a chat session."""
    chat_id = arguments["chat_id"]

    client = await get_hippo_client()
    response = await client.delete_chat(chat_id)

    result = {
        "success": True,
        "chat_id": chat_id,
        "message": "Chat session deleted successfully"
    }

    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


# ============================================================================
# Account Tool Handlers
# ============================================================================

async def handle_account_get_info(arguments: dict[str, Any]) -> list[TextContent]:
    """Get account information."""
    client = get_account_client()
    account = client.get_account_info()

    result = {
        "success": True,
        "account": {
            "account_id": account.account_id,
            "account_name": account.account_name,
            "created_at": str(account.created_at) if hasattr(account, "created_at") else None,
        }
    }

    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


async def handle_account_get_usage(arguments: dict[str, Any]) -> list[TextContent]:
    """Get account usage metrics."""
    account_id = arguments["account_id"]

    client = get_account_client()
    usage = client.get_account_usage(account_id)

    result = {
        "success": True,
        "account_id": account_id,
        "usage": {
            "api_calls": usage.api_calls if hasattr(usage, "api_calls") else None,
            "pages_processed": usage.pages_processed if hasattr(usage, "pages_processed") else None,
        }
    }

    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


async def handle_account_get_plan(arguments: dict[str, Any]) -> list[TextContent]:
    """Get account plan information."""
    account_id = arguments["account_id"]

    client = get_account_client()
    plan = client.get_account_plan(account_id)

    result = {
        "success": True,
        "account_id": account_id,
        "plan": {
            "plan_type": plan.plan_type if hasattr(plan, "plan_type") else None,
            "features": plan.features if hasattr(plan, "features") else None,
        }
    }

    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


async def handle_account_list_users(arguments: dict[str, Any]) -> list[TextContent]:
    """List account users."""
    client = get_account_client()
    users = client.get_users()

    result = {
        "success": True,
        "user_count": len(users),
        "users": [
            {
                "user_id": u.user_id,
                "email": u.email,
                "name": u.name,
                "role": u.role if hasattr(u, "role") else None,
            }
            for u in users
        ]
    }

    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


async def handle_account_get_current_user(arguments: dict[str, Any]) -> list[TextContent]:
    """Get current user information."""
    client = get_account_client()
    user = client.get_user_me()

    result = {
        "success": True,
        "user": {
            "user_id": user.user_id,
            "email": user.email,
            "name": user.name,
            "role": user.role if hasattr(user, "role") else None,
        }
    }

    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


# ============================================================================
# Main Entry Point
# ============================================================================

async def main():
    """Run the MCP server."""
    logger.info("Starting Cerevox MCP Server...")

    # Verify API key is set
    try:
        get_api_key()
        logger.info("API key found")
    except ValueError as e:
        logger.error(str(e))
        return

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
