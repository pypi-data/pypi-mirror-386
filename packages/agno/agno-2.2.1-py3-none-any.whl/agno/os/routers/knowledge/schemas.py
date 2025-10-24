from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ContentStatus(str, Enum):
    """Enumeration of possible content processing statuses."""

    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ContentStatusResponse(BaseModel):
    """Response model for content status endpoint."""

    status: ContentStatus = Field(..., description="Current processing status of the content")
    status_message: str = Field("", description="Status message or error details")


class ContentResponseSchema(BaseModel):
    id: str = Field(..., description="Unique identifier for the content")
    name: Optional[str] = Field(None, description="Name of the content")
    description: Optional[str] = Field(None, description="Description of the content")
    type: Optional[str] = Field(None, description="MIME type of the content")
    size: Optional[str] = Field(None, description="Size of the content in bytes")
    linked_to: Optional[str] = Field(None, description="ID of related content if linked")
    metadata: Optional[dict] = Field(None, description="Additional metadata as key-value pairs")
    access_count: Optional[int] = Field(None, description="Number of times content has been accessed", ge=0)
    status: Optional[ContentStatus] = Field(None, description="Processing status of the content")
    status_message: Optional[str] = Field(None, description="Status message or error details")
    created_at: Optional[datetime] = Field(None, description="Timestamp when content was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when content was last updated")

    @classmethod
    def from_dict(cls, content: Dict[str, Any]) -> "ContentResponseSchema":
        status = content.get("status")
        if isinstance(status, str):
            try:
                status = ContentStatus(status.lower())
            except ValueError:
                # Handle legacy or unknown statuses gracefully
                if "failed" in status.lower():
                    status = ContentStatus.FAILED
                elif "completed" in status.lower():
                    status = ContentStatus.COMPLETED
                else:
                    status = ContentStatus.PROCESSING
        elif status is None:
            status = ContentStatus.PROCESSING  # Default for None values

        # Helper function to safely parse timestamps
        def parse_timestamp(timestamp_value):
            if timestamp_value is None:
                return None
            try:
                # If it's already a datetime object, return it
                if isinstance(timestamp_value, datetime):
                    return timestamp_value
                # If it's a string, try to parse it as ISO format first
                if isinstance(timestamp_value, str):
                    try:
                        return datetime.fromisoformat(timestamp_value.replace("Z", "+00:00"))
                    except ValueError:
                        # Try to parse as float/int timestamp
                        timestamp_value = float(timestamp_value)
                # If it's a number, use fromtimestamp
                return datetime.fromtimestamp(timestamp_value, tz=timezone.utc)
            except (ValueError, TypeError, OSError):
                # If all parsing fails, return None
                return None

        return cls(
            id=content.get("id"),  # type: ignore
            name=content.get("name"),
            description=content.get("description"),
            type=content.get("file_type"),
            size=str(content.get("size")) if content.get("size") else "0",
            metadata=content.get("metadata"),
            status=status,
            status_message=content.get("status_message"),
            created_at=parse_timestamp(content.get("created_at")),
            updated_at=parse_timestamp(content.get("updated_at")),
            # TODO: These fields are not available in the Content class. Fix the inconsistency
            access_count=None,
            linked_to=None,
        )


class ContentUpdateSchema(BaseModel):
    """Schema for updating content."""

    name: Optional[str] = Field(None, description="Content name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Content description", max_length=1000)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Content metadata as key-value pairs")
    reader_id: Optional[str] = Field(None, description="ID of the reader to use for processing", min_length=1)


class ReaderSchema(BaseModel):
    id: str = Field(..., description="Unique identifier for the reader")
    name: Optional[str] = Field(None, description="Name of the reader")
    description: Optional[str] = Field(None, description="Description of the reader's capabilities")
    chunkers: Optional[List[str]] = Field(None, description="List of supported chunking strategies")


class ChunkerSchema(BaseModel):
    key: str = Field(..., description="Unique key for the chunker")
    name: Optional[str] = Field(None, description="Name of the chunker")
    description: Optional[str] = Field(None, description="Description of the chunking strategy")


class VectorDbSchema(BaseModel):
    id: str = Field(..., description="Unique identifier for the vector database")
    name: Optional[str] = Field(None, description="Name of the vector database")
    description: Optional[str] = Field(None, description="Description of the vector database")
    search_types: Optional[List[str]] = Field(
        None, description="List of supported search types (vector, keyword, hybrid)"
    )


class VectorSearchResult(BaseModel):
    """Schema for search result documents."""

    id: str = Field(..., description="Unique identifier for the search result document")
    content: str = Field(..., description="Content text of the document")
    name: Optional[str] = Field(None, description="Name of the document")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="Metadata associated with the document")
    usage: Optional[Dict[str, Any]] = Field(None, description="Usage statistics (e.g., token counts)")
    reranking_score: Optional[float] = Field(None, description="Reranking score for relevance", ge=0.0, le=1.0)
    content_id: Optional[str] = Field(None, description="ID of the source content")
    content_origin: Optional[str] = Field(None, description="Origin URL or source of the content")
    size: Optional[int] = Field(None, description="Size of the content in bytes", ge=0)

    @classmethod
    def from_document(cls, document) -> "VectorSearchResult":
        """Convert a Document object to a serializable VectorSearchResult."""
        return cls(
            id=document.id,
            content=document.content,
            name=getattr(document, "name", None),
            meta_data=getattr(document, "meta_data", None),
            usage=getattr(document, "usage", None),
            reranking_score=getattr(document, "reranking_score", None),
            content_id=getattr(document, "content_id", None),
            content_origin=getattr(document, "content_origin", None),
            size=getattr(document, "size", None),
        )


class VectorSearchRequestSchema(BaseModel):
    """Schema for vector search request."""

    class Meta(BaseModel):
        """Inline metadata schema for pagination."""

        limit: int = Field(20, description="Number of results per page", ge=1, le=100)
        page: int = Field(1, description="Page number", ge=1)

    query: str = Field(..., description="The search query text")
    db_id: Optional[str] = Field(None, description="The content database ID to search in")
    vector_db_ids: Optional[List[str]] = Field(None, description="List of vector database IDs to search in")
    search_type: Optional[str] = Field(None, description="The type of search to perform (vector, keyword, hybrid)")
    max_results: Optional[int] = Field(None, description="The maximum number of results to return", ge=1, le=1000)
    filters: Optional[Dict[str, Any]] = Field(None, description="Filters to apply to the search results")
    meta: Optional[Meta] = Field(
        None, description="Pagination metadata. Limit and page number to return a subset of results."
    )


class ConfigResponseSchema(BaseModel):
    readers: Optional[Dict[str, ReaderSchema]] = Field(None, description="Available content readers")
    readersForType: Optional[Dict[str, List[str]]] = Field(None, description="Mapping of content types to reader IDs")
    chunkers: Optional[Dict[str, ChunkerSchema]] = Field(None, description="Available chunking strategies")
    filters: Optional[List[str]] = Field(None, description="Available filter tags")
    vector_dbs: Optional[List[VectorDbSchema]] = Field(None, description="Configured vector databases")
