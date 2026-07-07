"""Invoice number generation utilities."""
from datetime import datetime
from typing import Optional
import random
import string


class InvoiceNumberGenerator:
    """Generate unique invoice numbers with various formats."""
    
    @staticmethod
    def generate_sequential(
        prefix: str = "INV",
        sequence_number: int = 1,
        padding: int = 6
    ) -> str:
        """
        Generate sequential invoice number.
        
        Args:
            prefix: Prefix for invoice number
            sequence_number: Current sequence number
            padding: Zero-padding length
            
        Returns:
            Invoice number like "INV-000001"
        """
        padded_number = str(sequence_number).zfill(padding)
        return f"{prefix}-{padded_number}"
    
    @staticmethod
    def generate_date_based(
        prefix: str = "INV",
        date: Optional[datetime] = None,
        sequence: int = 1
    ) -> str:
        """
        Generate date-based invoice number.
        
        Args:
            prefix: Prefix for invoice number
            date: Date for invoice (default: now)
            sequence: Sequence number for the day
            
        Returns:
            Invoice number like "INV-20260703-001"
        """
        if date is None:
            date = datetime.utcnow()
        
        date_str = date.strftime("%Y%m%d")
        seq_str = str(sequence).zfill(3)
        return f"{prefix}-{date_str}-{seq_str}"
    
    @staticmethod
    def generate_random(
        prefix: str = "INV",
        length: int = 8,
        use_letters: bool = True,
        use_numbers: bool = True
    ) -> str:
        """
        Generate random invoice number.
        
        Args:
            prefix: Prefix for invoice number
            length: Length of random part
            use_letters: Include letters
            use_numbers: Include numbers
            
        Returns:
            Invoice number like "INV-A7B9C2D5"
        """
        chars = ""
        if use_letters:
            chars += string.ascii_uppercase
        if use_numbers:
            chars += string.digits
        
        if not chars:
            chars = string.digits
        
        random_part = ''.join(random.choice(chars) for _ in range(length))
        return f"{prefix}-{random_part}"
    
    @staticmethod
    def generate_vendor_based(
        vendor_name: str,
        sequence: int = 1,
        date: Optional[datetime] = None
    ) -> str:
        """
        Generate vendor-based invoice number.
        
        Args:
            vendor_name: Vendor name
            sequence: Sequence number
            date: Date for invoice
            
        Returns:
            Invoice number like "AMZ-2026-001"
        """
        if date is None:
            date = datetime.utcnow()
        
        # Get first 3 uppercase letters from vendor name
        letters = ''.join(c for c in vendor_name.upper() if c.isalpha())
        prefix = letters[:3] if len(letters) >= 3 else letters.ljust(3, 'X')
        
        year = date.strftime("%Y")
        seq_str = str(sequence).zfill(3)
        
        return f"{prefix}-{year}-{seq_str}"
    
    @staticmethod
    def generate_custom(
        template: str,
        replacements: dict
    ) -> str:
        """
        Generate invoice number from custom template.
        
        Args:
            template: Template string with placeholders
            replacements: Dictionary of placeholder -> value
            
        Returns:
            Invoice number with placeholders replaced
            
        Example:
            template = "{prefix}-{year}-{month}-{seq:04d}"
            replacements = {"prefix": "INV", "year": 2026, "month": 7, "seq": 42}
            Returns: "INV-2026-07-0042"
        """
        try:
            return template.format(**replacements)
        except (KeyError, ValueError) as e:
            # Fallback to simple format
            return f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{replacements.get('seq', 1):04d}"


class SequenceManager:
    """Manage invoice number sequences in database."""
    
    def __init__(self, db):
        self.db = db
        self.sequences_collection = db["sequences"] if db is not None else None
    
    def get_next_sequence(
        self,
        sequence_name: str = "invoice_number",
        initial_value: int = 1
    ) -> int:
        """
        Get next sequence number (atomic operation).
        
        Args:
            sequence_name: Name of the sequence
            initial_value: Initial value if sequence doesn't exist
            
        Returns:
            Next sequence number
        """
        if self.sequences_collection is None:
            return initial_value
        
        try:
            result = self.sequences_collection.find_one_and_update(
                {"_id": sequence_name},
                {"$inc": {"value": 1}},
                upsert=True,
                return_document=True  # Return updated document
            )
            
            return result["value"]
            
        except Exception:
            # Fallback: return timestamp-based sequence
            return int(datetime.utcnow().timestamp() * 1000)
    
    def get_current_sequence(
        self,
        sequence_name: str = "invoice_number"
    ) -> int:
        """
        Get current sequence number without incrementing.
        
        Args:
            sequence_name: Name of the sequence
            
        Returns:
            Current sequence number
        """
        if self.sequences_collection is None:
            return 0
        
        try:
            result = self.sequences_collection.find_one({"_id": sequence_name})
            return result["value"] if result else 0
        except Exception:
            return 0
    
    def reset_sequence(
        self,
        sequence_name: str = "invoice_number",
        value: int = 1
    ) -> bool:
        """
        Reset sequence to specific value.
        
        Args:
            sequence_name: Name of the sequence
            value: New value
            
        Returns:
            True if successful
        """
        if self.sequences_collection is None:
            return False
        
        try:
            self.sequences_collection.update_one(
                {"_id": sequence_name},
                {"$set": {"value": value}},
                upsert=True
            )
            return True
        except Exception:
            return False
