"""Advanced filtering utilities for queries."""
from typing import Dict, Any, Optional, List
from datetime import datetime


class QueryBuilder:
    """Build MongoDB queries from request parameters."""
    
    def __init__(self):
        self.query = {}
    
    def add_exact_match(self, field: str, value: Any) -> 'QueryBuilder':
        """Add exact match filter."""
        if value is not None:
            self.query[field] = value
        return self
    
    def add_in_list(self, field: str, values: List[Any]) -> 'QueryBuilder':
        """Add 'in list' filter."""
        if values:
            self.query[field] = {"$in": values}
        return self
    
    def add_date_range(
        self,
        field: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> 'QueryBuilder':
        """Add date range filter."""
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date
            if date_query:
                self.query[field] = date_query
        return self
    
    def add_amount_range(
        self,
        field: str,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None
    ) -> 'QueryBuilder':
        """Add amount range filter."""
        if min_amount is not None or max_amount is not None:
            amount_query = {}
            if min_amount is not None:
                amount_query["$gte"] = min_amount
            if max_amount is not None:
                amount_query["$lte"] = max_amount
            if amount_query:
                self.query[field] = amount_query
        return self
    
    def add_text_search(
        self,
        fields: List[str],
        search_term: str,
        case_sensitive: bool = False
    ) -> 'QueryBuilder':
        """Add text search across multiple fields."""
        if search_term:
            options = "" if case_sensitive else "i"
            or_conditions = [
                {field: {"$regex": search_term, "$options": options}}
                for field in fields
            ]
            
            if "$or" in self.query:
                # Combine with existing OR conditions
                self.query["$and"] = [
                    {"$or": self.query["$or"]},
                    {"$or": or_conditions}
                ]
                del self.query["$or"]
            else:
                self.query["$or"] = or_conditions
        return self
    
    def add_custom(self, custom_query: Dict[str, Any]) -> 'QueryBuilder':
        """Add custom query conditions."""
        self.query.update(custom_query)
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build and return the final query."""
        return self.query


def parse_invoice_filters(request_args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse invoice filter parameters from request.
    
    Args:
        request_args: Request query parameters
        
    Returns:
        MongoDB query dictionary
    """
    builder = QueryBuilder()
    
    # Status filter
    status = request_args.get("status")
    if status:
        builder.add_exact_match("status", status)
    
    # Submitter filter
    submitter_id = request_args.get("submitter_id")
    if submitter_id:
        builder.add_exact_match("submitter_id", submitter_id)
    
    # Vendor filter
    vendor_id = request_args.get("vendor_id")
    if vendor_id:
        builder.add_exact_match("vendor_id", vendor_id)
    
    # Category filter
    category = request_args.get("category")
    if category:
        builder.add_exact_match("category", category)
    
    # Date range filter
    start_date = request_args.get("start_date")
    end_date = request_args.get("end_date")
    builder.add_date_range("date", start_date, end_date)
    
    # Amount range filter
    min_amount = request_args.get("min_amount")
    max_amount = request_args.get("max_amount")
    if min_amount or max_amount:
        try:
            min_amt = float(min_amount) if min_amount else None
            max_amt = float(max_amount) if max_amount else None
            builder.add_amount_range("total", min_amt, max_amt)
        except ValueError:
            pass
    
    # Search term
    search = request_args.get("search")
    if search:
        builder.add_text_search(["company", "invoice_number", "notes"], search)
    
    return builder.build()


def parse_vendor_filters(request_args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse vendor filter parameters from request.
    
    Args:
        request_args: Request query parameters
        
    Returns:
        MongoDB query dictionary
    """
    builder = QueryBuilder()
    
    # Status filter
    status = request_args.get("status")
    if status:
        builder.add_exact_match("status", status)
    
    # Search term
    search = request_args.get("search")
    if search:
        builder.add_text_search(
            ["name", "normalized_name", "email", "tax_id"],
            search
        )
    
    return builder.build()


def parse_sort_params(request_args: Dict[str, Any]) -> List[tuple]:
    """
    Parse sort parameters from request.
    
    Args:
        request_args: Request query parameters
        
    Returns:
        List of (field, direction) tuples for MongoDB sort
    """
    sort_by = request_args.get("sort_by", "created_at")
    sort_order = request_args.get("sort_order", "desc")
    
    # Map to MongoDB sort direction
    direction = -1 if sort_order.lower() == "desc" else 1
    
    return [(sort_by, direction)]


def validate_date_format(date_string: str) -> bool:
    """
    Validate date string format (YYYY-MM-DD).
    
    Args:
        date_string: Date string to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        datetime.strptime(date_string, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False
