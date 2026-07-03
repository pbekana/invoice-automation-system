"""Pagination utilities for API responses."""
from typing import List, Dict, Any, Optional, TypeVar, Generic
from math import ceil

T = TypeVar('T')


class PaginatedResponse(Generic[T]):
    """Paginated response wrapper with metadata."""
    
    def __init__(
        self,
        items: List[T],
        total: int,
        page: int,
        per_page: int,
        has_next: bool = False,
        has_prev: bool = False
    ):
        self.items = items
        self.total = total
        self.page = page
        self.per_page = per_page
        self.has_next = has_next
        self.has_prev = has_prev
        self.total_pages = ceil(total / per_page) if per_page > 0 else 0
    
    def to_dict(self, serializer=None) -> Dict[str, Any]:
        """Convert to dictionary for JSON response."""
        if serializer:
            items = [serializer(item) for item in self.items]
        else:
            items = [item.to_json() if hasattr(item, 'to_json') else item for item in self.items]
        
        return {
            "items": items,
            "pagination": {
                "total": self.total,
                "page": self.page,
                "per_page": self.per_page,
                "total_pages": self.total_pages,
                "has_next": self.has_next,
                "has_prev": self.has_prev
            }
        }


class CursorPagination:
    """Cursor-based pagination for better performance on large datasets."""
    
    @staticmethod
    def encode_cursor(value: Any) -> str:
        """Encode a cursor value (timestamp or ID)."""
        import base64
        return base64.b64encode(str(value).encode()).decode()
    
    @staticmethod
    def decode_cursor(cursor: str) -> str:
        """Decode a cursor value."""
        import base64
        try:
            return base64.b64decode(cursor.encode()).decode()
        except Exception:
            return ""
    
    @staticmethod
    def create_response(
        items: List[T],
        limit: int,
        next_cursor: Optional[str] = None,
        prev_cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create cursor-paginated response."""
        return {
            "items": [item.to_json() if hasattr(item, 'to_json') else item for item in items],
            "pagination": {
                "limit": limit,
                "next_cursor": next_cursor,
                "prev_cursor": prev_cursor,
                "has_next": next_cursor is not None,
                "has_prev": prev_cursor is not None
            }
        }


def paginate(
    items: List[T],
    page: int = 1,
    per_page: int = 50,
    max_per_page: int = 200
) -> PaginatedResponse[T]:
    """
    Paginate a list of items.
    
    Args:
        items: List of items to paginate
        page: Page number (1-indexed)
        per_page: Items per page
        max_per_page: Maximum items per page
        
    Returns:
        PaginatedResponse with items and metadata
    """
    # Validate and cap per_page
    per_page = min(max(1, per_page), max_per_page)
    page = max(1, page)
    
    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    
    paginated_items = items[start:end]
    
    has_next = end < total
    has_prev = page > 1
    
    return PaginatedResponse(
        items=paginated_items,
        total=total,
        page=page,
        per_page=per_page,
        has_next=has_next,
        has_prev=has_prev
    )


def get_pagination_params(request_args: Dict[str, Any]) -> Dict[str, int]:
    """
    Extract and validate pagination parameters from request.
    
    Args:
        request_args: Request query parameters
        
    Returns:
        Dictionary with page, per_page, skip, limit
    """
    page = int(request_args.get("page", 1))
    per_page = int(request_args.get("per_page", 50))
    limit = int(request_args.get("limit", per_page))
    skip = int(request_args.get("skip", (page - 1) * per_page))
    
    # Validate
    page = max(1, page)
    per_page = min(max(1, per_page), 200)
    limit = min(max(1, limit), 200)
    skip = max(0, skip)
    
    return {
        "page": page,
        "per_page": per_page,
        "limit": limit,
        "skip": skip
    }
