#!/usr/bin/env python3
"""
MCP Server for pgvector Collection Management

Model Context Protocol server that provides tools for managing PostgreSQL collections
with pgvector extension. Supports collection management, document processing, and
vector search operations.
"""

import asyncio
import json
import os
import sys
from typing import Any, Dict, List, Optional, Sequence, Union
from pathlib import Path

from mcp.server.fastmcp import FastMCP, Context
from mcp.types import Resource, Tool

# Ensure cross-platform compatibility
if sys.platform.startswith("win"):
    # Windows-specific configurations
    import pathlib

    pathlib.PosixPath = pathlib.WindowsPath

from .config import get_settings
from .database import get_db_session
from .services import CollectionService, VectorService, DocumentService, EmbeddingService
from .utils import validate_collection_name, validate_dimension
from .exceptions import CollectionError, DatabaseError, PgvectorCLIError

# Initialize FastMCP server
mcp = FastMCP("pgvector-azure-openai-mcp-server")


@mcp.tool()
def status() -> Dict[str, Any]:
    """
    Check system status and database connectivity.

    Returns:
        Dictionary with comprehensive status information including database
        connection, pgvector extension, embedding service, and system info.
    """
    import datetime
    import platform
    from sqlalchemy import text

    status_info = {
        "timestamp": datetime.datetime.now().isoformat(),
        "success": True,
        "database": {},
        "embedding_service": {},
        "collections": {},
        "system": {},
    }

    # Check database connection and pgvector extension
    try:
        with get_db_session() as session:
            # Basic connection test
            session.execute(text("SELECT 1"))
            status_info["database"]["connected"] = True

            # Get database URL (mask password)
            settings = get_settings()
            db_url = settings.database_url
            if "@" in db_url:
                # Mask password in URL for security
                parts = db_url.split("@")
                user_pass = parts[0].split("://")[1]
                if ":" in user_pass:
                    user = user_pass.split(":")[0]
                    masked_url = db_url.replace(user_pass, f"{user}:***")
                    status_info["database"]["url"] = masked_url
                else:
                    status_info["database"]["url"] = db_url
            else:
                status_info["database"]["url"] = db_url

            # Check pgvector extension
            try:
                result = session.execute(
                    text("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector'")
                ).first()
                if result:
                    status_info["database"]["pgvector_installed"] = True
                    status_info["database"]["pgvector_version"] = result[1]
                else:
                    status_info["database"]["pgvector_installed"] = False
                    status_info["database"]["pgvector_version"] = None
            except Exception as e:
                status_info["database"]["pgvector_error"] = str(e)
                status_info["database"]["pgvector_installed"] = False

            # Get collection statistics
            try:
                collection_service = CollectionService(session)
                vector_service = VectorService(session)
                collections = collection_service.get_collections()

                total_vectors = 0
                for collection in collections:
                    total_vectors += vector_service.get_vector_count(collection.id)

                status_info["collections"] = {
                    "total": len(collections),
                    "total_vectors": total_vectors,
                }
            except Exception as e:
                status_info["collections"]["error"] = str(e)

    except Exception as e:
        status_info["success"] = False
        status_info["database"]["connected"] = False
        status_info["database"]["error"] = str(e)

    # Check embedding service
    try:
        embedding_service = EmbeddingService()
        embedding_service.check_api_status()
        status_info["embedding_service"]["available"] = True
        status_info["embedding_service"]["api_key_configured"] = True
        status_info["embedding_service"]["dimension"] = 1536
        status_info["embedding_service"]["provider"] = "Azure OpenAI"
    except Exception as e:
        status_info["embedding_service"]["error"] = str(e)
        status_info["embedding_service"]["available"] = False

    # System information
    try:
        import importlib.metadata
        import sqlalchemy

        status_info["system"] = {
            "python_version": platform.python_version(),
            "platform": platform.system(),
            "platform_version": platform.release(),
            "mcp_version": importlib.metadata.version("mcp"),
            "sqlalchemy_version": sqlalchemy.__version__,
            "pgvector_version": importlib.metadata.version("pgvector"),
            "working_directory": str(Path.cwd()),
        }
    except Exception as e:
        status_info["system"]["error"] = str(e)

    return status_info


@mcp.tool()
def create_collection(name: str, description: str = "", dimension: int = 1536) -> Dict[str, Any]:
    """
    Create a new vector collection.

    Args:
        name: Unique name for the collection
        description: Optional description of the collection
        dimension: Vector dimension (fixed at 1536)

    Returns:
        Dictionary with collection details
    """
    try:
        # Validate inputs
        validate_collection_name(name)
        validate_dimension(dimension)

        with get_db_session() as session:
            collection_service = CollectionService(session)

            # Check if collection already exists
            existing = collection_service.get_collection_by_name(name)
            if existing:
                raise CollectionError(f"Collection '{name}' already exists")

            # Create new collection
            collection = collection_service.create_collection(name, dimension, description)

            return {
                "success": True,
                "collection": {
                    "id": collection.id,
                    "name": collection.name,
                    "description": collection.description,
                    "dimension": collection.dimension,
                    "created_at": collection.created_at.isoformat(),
                    "total_vectors": 0,
                },
            }

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def list_collections() -> Dict[str, Any]:
    """
    List all active collections.

    Returns:
        Dictionary with list of collections
    """
    try:
        with get_db_session() as session:
            collection_service = CollectionService(session)
            vector_service = VectorService(session)

            collections = collection_service.get_collections()
            result = []

            for collection in collections:
                # Get vector count for each collection
                vector_count = vector_service.get_vector_count(collection.id)

                result.append(
                    {
                        "id": collection.id,
                        "name": collection.name,
                        "description": collection.description,
                        "dimension": collection.dimension,
                        "created_at": collection.created_at.isoformat()
                        if collection.created_at
                        else None,
                        "updated_at": collection.updated_at.isoformat()
                        if collection.updated_at
                        else None,
                        "total_vectors": vector_count,
                    }
                )

            return {"success": True, "collections": result, "total": len(result)}

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def show_collection(
    name: str, include_stats: bool = True, include_files: bool = False
) -> Dict[str, Any]:
    """
    Show details for a specific collection.

    Args:
        name: Name of the collection
        include_stats: Whether to include statistics
        include_files: Whether to include file list and file statistics

    Returns:
        Dictionary with collection details, statistics, and optionally file information
    """
    try:
        with get_db_session() as session:
            collection_service = CollectionService(session)
            vector_service = VectorService(session)

            collection = collection_service.get_collection_by_name(name)
            if not collection:
                return {"success": False, "error": f"Collection '{name}' not found"}

            result = {
                "id": collection.id,
                "name": collection.name,
                "description": collection.description,
                "dimension": collection.dimension,
                "created_at": collection.created_at.isoformat() if collection.created_at else None,
                "updated_at": collection.updated_at.isoformat() if collection.updated_at else None,
            }

            if include_stats:
                vector_count = vector_service.get_vector_count(collection.id)
                result["statistics"] = {
                    "total_vectors": vector_count,
                    "table_name": f"vectors_{collection.name}",
                }

            if include_files:
                # Get file list and summary
                files = vector_service.get_files_in_collection(collection.id)
                file_summary = vector_service.get_file_summary(collection.id)

                result["files"] = files
                result["file_summary"] = file_summary

            return {"success": True, "collection": result}

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def rename_collection(old_name: str, new_name: str) -> Dict[str, Any]:
    """
    Rename an existing collection.

    Args:
        old_name: Current name of the collection
        new_name: New name for the collection

    Returns:
        Dictionary with rename operation result
    """
    try:
        # Validate inputs
        if not old_name or not old_name.strip():
            return {"success": False, "error": "old_name cannot be empty"}

        if not new_name or not new_name.strip():
            return {"success": False, "error": "new_name cannot be empty"}

        # Validate new name format
        validate_collection_name(new_name)

        with get_db_session() as session:
            collection_service = CollectionService(session)

            # Perform atomic rename operation
            collection = collection_service.rename_collection(old_name, new_name)

            return {
                "success": True,
                "message": f"Collection successfully renamed from '{old_name}' to '{new_name}'",
                "collection": {
                    "id": collection.id,
                    "name": collection.name,
                    "description": collection.description,
                    "dimension": collection.dimension,
                    "created_at": collection.created_at.isoformat()
                    if collection.created_at
                    else None,
                    "updated_at": collection.updated_at.isoformat()
                    if collection.updated_at
                    else None,
                },
            }

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def delete_collection(name: str, confirm: bool = False) -> Dict[str, Any]:
    """
    Delete a collection and all its vectors.

    Args:
        name: Name of the collection to delete
        confirm: Confirmation flag (required for safety)

    Returns:
        Dictionary with deletion result
    """
    try:
        if not confirm:
            return {
                "success": False,
                "error": "Deletion requires confirmation. Set confirm=True to proceed.",
            }

        with get_db_session() as session:
            collection_service = CollectionService(session)

            collection = collection_service.get_collection_by_name(name)
            if not collection:
                return {"success": False, "error": f"Collection '{name}' not found"}

            # Delete collection (soft delete with cleanup)
            collection_service.delete_collection(collection.id)

            return {"success": True, "message": f"Collection '{name}' has been deleted"}

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def add_text(collection_name: str, text: str, metadata: Any = None) -> Dict[str, Any]:
    """
    Add text content to a collection as a vector.

    Args:
        collection_name: Name of the target collection
        text: Text content to vectorize and add
        metadata: Optional metadata as dict or JSON string
                 Examples:
                 - {"key": "value", "type": "test"}
                 - '{"key": "value", "type": "test"}'

    Returns:
        Dictionary with the created vector record details
    """
    try:
        if not text.strip():
            return {"success": False, "error": "Text content cannot be empty"}

        # Parse metadata if it's a string
        parsed_metadata = {}
        if metadata is not None:
            if isinstance(metadata, str):
                try:
                    parsed_metadata = json.loads(metadata)
                    if not isinstance(parsed_metadata, dict):
                        return {"success": False, "error": "Metadata JSON must be an object/dict"}
                except json.JSONDecodeError as e:
                    return {"success": False, "error": f"Invalid JSON in metadata: {str(e)}"}
            elif isinstance(metadata, dict):
                parsed_metadata = metadata
            else:
                return {"success": False, "error": "Metadata must be a dict or JSON string"}

        with get_db_session() as session:
            collection_service = CollectionService(session)
            vector_service = VectorService(session)

            collection = collection_service.get_collection_by_name(collection_name)
            if not collection:
                return {"success": False, "error": f"Collection '{collection_name}' not found"}

            # Create vector record
            vector_record = vector_service.create_vector_record(
                collection.id, text, parsed_metadata
            )

            return {
                "success": True,
                "vector": {
                    "id": vector_record.id,
                    "content": vector_record.content,
                    "metadata": vector_record.extra_metadata,
                    "created_at": vector_record.created_at.isoformat(),
                },
            }

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def search_collection(collection_name: str, query: str, limit: int = 10) -> Dict[str, Any]:
    """
    Search for similar vectors in a collection.

    Args:
        collection_name: Name of the collection to search
        query: Search query text
        limit: Maximum number of results (default: 10)

    Returns:
        Dictionary with search results
    """
    try:
        if not query.strip():
            return {"success": False, "error": "Query cannot be empty"}

        if limit <= 0 or limit > 100:
            return {"success": False, "error": "Limit must be between 1 and 100"}

        with get_db_session() as session:
            collection_service = CollectionService(session)
            vector_service = VectorService(session)

            collection = collection_service.get_collection_by_name(collection_name)
            if not collection:
                return {"success": False, "error": f"Collection '{collection_name}' not found"}

            # Perform vector search
            results = vector_service.search_vectors(collection.id, query, limit)

            # Filter by similarity threshold and format results
            filtered_results = []
            min_similarity = 0.0
            for vector_record, similarity in results:
                if similarity >= min_similarity:
                    filtered_results.append(
                        {
                            "id": vector_record.id,
                            "content": vector_record.content,
                            "metadata": vector_record.extra_metadata,
                            "similarity_score": float(similarity),
                            "created_at": vector_record.created_at.isoformat(),
                        }
                    )

            return {
                "success": True,
                "query": query,
                "collection": collection_name,
                "total_results": len(filtered_results),
                "results": filtered_results,
            }

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def add_document(
    collection_name: str,
    file_path: str,
    metadata: Any = None,
    duplicate_action: str = "smart",
    ctx: Optional[Context] = None,
) -> Dict[str, Any]:
    """
    Process a document file and add its contents to a collection with progress reporting.

    Args:
        collection_name: Name of the target collection
        file_path: Path to the document file (PDF, CSV, TXT, etc.)
        metadata: Optional metadata dictionary
        duplicate_action: How to handle duplicate files. Options:
            - "smart": Compare file modification time, skip if unchanged, overwrite if changed
            - "skip": Skip if file already exists
            - "overwrite": Always overwrite existing file vectors
            - "append": Add new vectors without removing old ones
        ctx: MCP context for progress reporting

    Returns:
        Dictionary with processing results and duplicate handling information
    """
    import time
    import logging

    logger = logging.getLogger("mcp_server.add_document")
    start_time = time.time()

    try:
        logger.info(
            f"Starting document processing - file: {file_path}, collection: {collection_name}"
        )

        # Parse metadata if it's a string
        parsed_metadata = {}
        if metadata is not None:
            if isinstance(metadata, str):
                try:
                    parsed_metadata = json.loads(metadata)
                    if not isinstance(parsed_metadata, dict):
                        return {"success": False, "error": "Metadata JSON must be an object/dict"}
                except json.JSONDecodeError as e:
                    return {"success": False, "error": f"Invalid JSON in metadata: {str(e)}"}
            elif isinstance(metadata, dict):
                parsed_metadata = metadata
            elif metadata is not None:
                return {"success": False, "error": "Metadata must be a dict or JSON string"}

        # Stage 1: Document parsing and validation (0-25%)
        if ctx:
            await ctx.report_progress(progress=0, total=100, message="Starting document parsing...")

        # Ensure cross-platform path handling
        file_path_obj = Path(file_path).resolve()
        if not file_path_obj.exists():
            return {"success": False, "error": f"File not found: {file_path_obj}"}

        with get_db_session() as session:
            collection_service = CollectionService(session)
            vector_service = VectorService(session)
            document_service = DocumentService()  # DocumentService doesn't need session

            collection = collection_service.get_collection_by_name(collection_name)
            if not collection:
                return {"success": False, "error": f"Collection '{collection_name}' not found"}

            if ctx:
                await ctx.report_progress(
                    progress=15, total=100, message="Validating collection and file..."
                )

            # Stage 1.5: Duplicate detection and handling (15-25%)
            if ctx:
                await ctx.report_progress(
                    progress=15, total=100, message="Checking for file duplicates..."
                )

            # Validate duplicate_action parameter
            valid_actions = ["smart", "skip", "overwrite", "append"]
            if duplicate_action not in valid_actions:
                return {
                    "success": False,
                    "error": f"Invalid duplicate_action '{duplicate_action}'. Must be one of: {', '.join(valid_actions)}",
                }

            # Check if file already exists
            existing_file_info = vector_service.check_file_exists(collection.id, str(file_path_obj))
            action_taken = "added"  # Default action
            file_status = {
                "existed": False,
                "file_changed": False,
                "previous_vectors": 0,
                "vectors_deleted": 0,
            }

            if existing_file_info:
                file_status["existed"] = True
                file_status["previous_vectors"] = existing_file_info["vector_count"]

                # Get file modification times for smart detection
                current_file_mtime = vector_service.get_file_modification_time(str(file_path_obj))

                if duplicate_action == "skip":
                    logger.info(
                        f"File already exists, skipping processing - file: {str(file_path_obj)}, existing_vectors: {existing_file_info['vector_count']}"
                    )
                    return {
                        "success": True,
                        "action_taken": "skipped",
                        "file_status": file_status,
                        "message": f"File already exists, skipping processing. Existing vector count: {existing_file_info['vector_count']}",
                        "file_path": str(file_path_obj),
                        "collection": collection_name,
                        "vectors_created": 0,
                        "existing_file_info": existing_file_info,
                    }

                elif duplicate_action == "smart":
                    # Compare modification times for smart detection
                    if current_file_mtime:
                        # For smart mode, we need to compare with stored metadata if available
                        # For now, we'll use a simple heuristic: if file exists, assume it might have changed
                        # In future, we could store file mtime in metadata for exact comparison
                        logger.info(
                            f"Smart detection mode: File already exists, will overwrite - file: {str(file_path_obj)}, mtime: {current_file_mtime.isoformat() if current_file_mtime else None}"
                        )
                        file_status["file_changed"] = True
                        action_taken = "overwrite"
                    else:
                        logger.info(
                            f"Cannot get file modification time, skipping processing - file: {str(file_path_obj)}"
                        )
                        return {
                            "success": False,
                            "error": f"Cannot access file modification time for smart detection: {file_path_obj}",
                        }

                elif duplicate_action == "overwrite":
                    logger.info(
                        f"Force overwrite mode: deleting existing vectors - file: {str(file_path_obj)}, existing_vectors: {existing_file_info['vector_count']}"
                    )
                    action_taken = "overwrite"
                    file_status["file_changed"] = True

                elif duplicate_action == "append":
                    logger.info(
                        f"Append mode: keeping existing vectors, adding new vectors - file: {str(file_path_obj)}, existing_vectors: {existing_file_info['vector_count']}"
                    )
                    action_taken = "append"
                    # Don't delete existing vectors in append mode

                # Delete existing vectors for overwrite and smart modes
                if action_taken in ["overwrite"] or (
                    action_taken == "overwrite" and duplicate_action == "smart"
                ):
                    if ctx:
                        await ctx.report_progress(
                            progress=20,
                            total=100,
                            message=f"Deleting {existing_file_info['vector_count']} existing vectors...",
                        )

                    deleted_count = vector_service.delete_file_vectors(
                        collection.id, str(file_path_obj)
                    )
                    file_status["vectors_deleted"] = deleted_count
                    logger.info(f"Deleted existing vectors - count: {deleted_count}")

            if ctx:
                await ctx.report_progress(
                    progress=25,
                    total=100,
                    message="Duplicate detection complete, starting document processing...",
                )

            # Stage 2: Text chunking (25-50%)
            chunking_start = time.time()
            if ctx:
                await ctx.report_progress(
                    progress=25, total=100, message="Processing document into chunks..."
                )

            # Process document with default chunking parameters
            chunks = document_service.process_document(
                str(file_path_obj), chunk_size=500, overlap=150
            )

            if not chunks:
                return {"success": False, "error": "No content extracted from document"}

            chunking_time = time.time() - chunking_start
            logger.info(
                f"Document chunking complete - chunks: {len(chunks)}, time: {chunking_time:.2f}s"
            )

            if ctx:
                await ctx.report_progress(
                    progress=50, total=100, message=f"Generated {len(chunks)} document chunks"
                )

            # Stage 3: Vector generation (50-90%) - True batch processing with single transaction
            vector_start = time.time()
            if ctx:
                await ctx.report_progress(
                    progress=60, total=100, message="Preparing batch vector generation..."
                )

            # Prepare all batch data at once for maximum efficiency
            all_batch_data = []
            for chunk in chunks:
                # Merge chunk metadata with user metadata
                combined_metadata = {**chunk.metadata, **parsed_metadata}
                all_batch_data.append(
                    {"content": chunk.content, "extra_metadata": combined_metadata}
                )

            if ctx:
                await ctx.report_progress(
                    progress=70,
                    total=100,
                    message=f"Starting processing of {len(all_batch_data)} document chunks (batch mode)...",
                )

            logger.info(f"Starting batch vector generation - batch_size: {len(all_batch_data)}")

            # Process all chunks in single batch operation (API calls: 10 texts per batch internally)
            # Database: Single transaction for all vectors
            results = vector_service.create_vector_records_batch(collection.id, all_batch_data)

            vector_time = time.time() - vector_start
            logger.info(
                f"Batch vector generation complete - vectors_created: {len(results)}, time: {vector_time:.2f}s"
            )

            if ctx:
                await ctx.report_progress(
                    progress=85,
                    total=100,
                    message=f"Completed batch processing, generated {len(results)} vectors",
                )

            # Stage 4: Database storage completion (90-100%)
            if ctx:
                await ctx.report_progress(
                    progress=90, total=100, message="Completing vector storage..."
                )
                await ctx.report_progress(progress=100, total=100, message="Processing complete")

            total_time = time.time() - start_time
            logger.info(
                f"Document processing complete - total_time: {total_time:.2f}s, vectors_created: {len(results)}, chunks_processed: {len(chunks)}, avg_time_per_vector: {total_time / len(results):.3f}s"
                if results
                else "N/A"
            )

            # Update file_status with final counts
            file_status["vectors_created"] = len(results)

            # Generate appropriate message based on action taken
            if action_taken == "append":
                message = f"Append mode: kept {file_status['previous_vectors']} existing vectors, added {len(results)} new vectors"
            elif action_taken == "overwrite":
                message = f"Overwrite mode: deleted {file_status['vectors_deleted']} old vectors, added {len(results)} new vectors"
            else:
                message = f"Successfully processed document, created {len(results)} vectors"

            return {
                "success": True,
                "action_taken": action_taken,
                "file_status": file_status,
                "message": message,
                "file_path": str(file_path_obj),
                "collection": collection_name,
                "vectors_created": len(results),
                "processing_stats": {
                    "total_time_seconds": f"{total_time:.2f}",
                    "chunking_time_seconds": f"{chunking_time:.2f}",
                    "vector_generation_time_seconds": f"{vector_time:.2f}",
                    "chunks_processed": len(chunks),
                    "avg_time_per_vector": f"{total_time / len(results):.3f}" if results else "N/A",
                },
                # 简化返回内容，只提供关键统计信息
                "summary": {
                    "vector_id_range": f"{results[0].id}-{results[-1].id}" if results else None,
                    "total_vectors": len(results),
                    "status": "completed",
                },
            }

    except Exception as e:
        total_time = time.time() - start_time
        logger.error(
            f"Document processing failed - error: {str(e)}, time: {total_time:.2f}s, file: {file_path}, collection: {collection_name}"
        )
        if ctx:
            await ctx.report_progress(progress=0, total=100, message=f"Processing failed: {str(e)}")
        return {"success": False, "error": str(e)}


@mcp.tool()
def delete_vectors(
    collection_name: str,
    file_path: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    preview_only: bool = False,
    confirm: bool = False,
) -> Dict[str, Any]:
    """
    Delete vectors from a collection with flexible filtering options.

    Args:
        collection_name: Name of the target collection
        file_path: Delete all vectors from a specific file (optional)
        start_date: Start date for date range deletion in YYYY-MM-DD format (optional)
        end_date: End date for date range deletion in YYYY-MM-DD format (optional)
        preview_only: Only preview what would be deleted, don't actually delete
        confirm: Required confirmation for actual deletion (ignored if preview_only=True)

    Returns:
        Dictionary with deletion results or preview information
    """
    try:
        # Parameter validation
        if file_path and (start_date or end_date):
            return {
                "success": False,
                "error": "Cannot specify both file_path and date range. Choose one deletion method.",
            }

        if start_date and not end_date:
            return {
                "success": False,
                "error": "Both start_date and end_date are required for date range deletion",
            }

        if not preview_only and not confirm:
            return {
                "success": False,
                "error": "Deletion requires confirmation. Set confirm=True or use preview_only=True to preview first.",
            }

        with get_db_session() as session:
            collection_service = CollectionService(session)

            collection = collection_service.get_collection_by_name(collection_name)
            if not collection:
                return {"success": False, "error": f"Collection '{collection_name}' not found"}

            # Build query conditions
            from sqlalchemy import text, and_
            from .models.vector_record import VectorRecord

            conditions = [VectorRecord.collection_id == collection.id]
            deletion_method = ""
            deletion_criteria = {}

            if file_path:
                # Delete by file path - try both absolute and relative paths
                file_path_input = str(file_path)
                file_path_abs = str(Path(file_path_input).resolve())
                file_name = Path(file_path_input).name

                # Use OR condition to match file_path, absolute path, or file name
                conditions.append(
                    text(
                        "(extra_metadata->>'file_path' = :file_path_exact OR extra_metadata->>'file_path' = :file_path_abs OR extra_metadata->>'file_name' = :file_name)"
                    )
                )
                deletion_method = "file_path"
                deletion_criteria = {
                    "file_path": file_path_input,
                    "file_path_abs": file_path_abs,
                    "file_name": file_name,
                }

            elif start_date and end_date:
                # Delete by date range
                import datetime

                try:
                    start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
                    end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d") + datetime.timedelta(
                        days=1
                    )

                    conditions.append(
                        and_(VectorRecord.created_at >= start_dt, VectorRecord.created_at < end_dt)
                    )
                    deletion_method = "date_range"
                    deletion_criteria = {"start_date": start_date, "end_date": end_date}

                except ValueError:
                    return {
                        "success": False,
                        "error": "Invalid date format. Use YYYY-MM-DD format (e.g., '2025-08-25')",
                    }

            # Execute query to find matching vectors
            if deletion_method == "file_path":
                # For file path queries, use raw SQL with parameters
                query = (
                    session.query(VectorRecord)
                    .filter(VectorRecord.collection_id == collection.id)
                    .filter(
                        text(
                            "(extra_metadata->>'file_path' = :file_path_exact OR extra_metadata->>'file_path' = :file_path_abs OR extra_metadata->>'file_name' = :file_name)"
                        )
                    )
                    .params(
                        file_path_exact=file_path_input,
                        file_path_abs=file_path_abs,
                        file_name=file_name,
                    )
                )
            else:
                # For date range queries, use standard SQLAlchemy
                query = session.query(VectorRecord).filter(and_(*conditions))

            matching_vectors = query.all()

            if not matching_vectors:
                return {
                    "success": True,
                    "message": "No vectors found matching the specified criteria",
                    "deletion_method": deletion_method,
                    "criteria": deletion_criteria,
                    "matched_count": 0,
                }

            # Preview mode - return information without deleting
            if preview_only:
                preview_samples = []
                for vector in matching_vectors[:3]:  # Show up to 3 samples
                    preview_samples.append(
                        {
                            "id": vector.id,
                            "content_preview": vector.content[:100] + "..."
                            if len(vector.content) > 100
                            else vector.content,
                            "created_at": vector.created_at.isoformat()
                            if vector.created_at
                            else None,
                            "file_info": {
                                "file_name": vector.extra_metadata.get("file_name"),
                                "file_path": vector.extra_metadata.get("file_path"),
                                "source": vector.extra_metadata.get("source"),
                            },
                        }
                    )

                return {
                    "success": True,
                    "preview": True,
                    "deletion_method": deletion_method,
                    "criteria": deletion_criteria,
                    "matched_count": len(matching_vectors),
                    "preview_samples": preview_samples,
                    "message": f"Preview: {len(matching_vectors)} vectors would be deleted. Use confirm=True to proceed with deletion.",
                }

            # Actual deletion
            deleted_ids = [vector.id for vector in matching_vectors]

            # Perform deletion
            deleted_count = query.delete(synchronize_session="fetch")
            session.commit()

            return {
                "success": True,
                "deleted": True,
                "deletion_method": deletion_method,
                "criteria": deletion_criteria,
                "deleted_count": deleted_count,
                "deleted_vector_ids": deleted_ids[:10]
                if len(deleted_ids) <= 10
                else deleted_ids[:10] + [f"... and {len(deleted_ids) - 10} more"],
                "message": f"Successfully deleted {deleted_count} vectors from collection '{collection_name}'",
            }

    except Exception as e:
        return {"success": False, "error": str(e)}


def main() -> None:
    """Main entry point for the MCP server."""
    mcp.run()


# Run the server
if __name__ == "__main__":
    main()
