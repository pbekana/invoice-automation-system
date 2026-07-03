"""Export utilities for invoices and data."""
import csv
import io
from typing import List, Dict, Any
from datetime import datetime


class CSVExporter:
    """Export data to CSV format."""
    
    @staticmethod
    def export_invoices(invoices: List[Dict[str, Any]]) -> str:
        """
        Export invoices to CSV format.
        
        Args:
            invoices: List of invoice dictionaries
            
        Returns:
            CSV string
        """
        if not invoices:
            return ""
        
        output = io.StringIO()
        
        # Define columns
        fieldnames = [
            "ID",
            "Invoice Number",
            "Company",
            "Vendor ID",
            "Date",
            "Due Date",
            "Amount",
            "Category",
            "Status",
            "Submitter ID",
            "Created At",
            "Approved At",
            "Paid At",
            "Notes"
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for invoice in invoices:
            writer.writerow({
                "ID": invoice.get("id", ""),
                "Invoice Number": invoice.get("invoice_number", ""),
                "Company": invoice.get("company", ""),
                "Vendor ID": invoice.get("vendor_id", ""),
                "Date": invoice.get("date", ""),
                "Due Date": invoice.get("due_date", ""),
                "Amount": invoice.get("total", 0),
                "Category": invoice.get("category", ""),
                "Status": invoice.get("status", ""),
                "Submitter ID": invoice.get("submitter_id", ""),
                "Created At": invoice.get("created_at", ""),
                "Approved At": invoice.get("approved_at", ""),
                "Paid At": invoice.get("paid_at", ""),
                "Notes": invoice.get("notes", "")
            })
        
        return output.getvalue()
    
    @staticmethod
    def export_vendors(vendors: List[Dict[str, Any]]) -> str:
        """
        Export vendors to CSV format.
        
        Args:
            vendors: List of vendor dictionaries
            
        Returns:
            CSV string
        """
        if not vendors:
            return ""
        
        output = io.StringIO()
        
        fieldnames = [
            "ID",
            "Name",
            "Email",
            "Phone",
            "Address",
            "Tax ID",
            "Payment Terms",
            "Default Category",
            "Status",
            "Created At",
            "Notes"
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for vendor in vendors:
            writer.writerow({
                "ID": vendor.get("id", ""),
                "Name": vendor.get("name", ""),
                "Email": vendor.get("email", ""),
                "Phone": vendor.get("phone", ""),
                "Address": vendor.get("address", ""),
                "Tax ID": vendor.get("tax_id", ""),
                "Payment Terms": vendor.get("payment_terms", ""),
                "Default Category": vendor.get("default_category", ""),
                "Status": vendor.get("status", ""),
                "Created At": vendor.get("created_at", ""),
                "Notes": vendor.get("notes", "")
            })
        
        return output.getvalue()
    
    @staticmethod
    def export_audit_log(audit_entries: List[Dict[str, Any]]) -> str:
        """
        Export audit log to CSV format.
        
        Args:
            audit_entries: List of audit entry dictionaries
            
        Returns:
            CSV string
        """
        if not audit_entries:
            return ""
        
        output = io.StringIO()
        
        fieldnames = [
            "ID",
            "Timestamp",
            "Action",
            "Entity Type",
            "Entity ID",
            "User ID",
            "IP Address",
            "Details"
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for entry in audit_entries:
            writer.writerow({
                "ID": entry.get("id", ""),
                "Timestamp": entry.get("timestamp", ""),
                "Action": entry.get("action", ""),
                "Entity Type": entry.get("entity_type", ""),
                "Entity ID": entry.get("entity_id", ""),
                "User ID": entry.get("user_id", ""),
                "IP Address": entry.get("ip_address", ""),
                "Details": str(entry.get("details", {}))
            })
        
        return output.getvalue()


class ReportGenerator:
    """Generate various reports from invoice data."""
    
    @staticmethod
    def generate_spending_summary(invoices: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate spending summary report.
        
        Args:
            invoices: List of invoice dictionaries
            
        Returns:
            Summary statistics
        """
        if not invoices:
            return {
                "total_invoices": 0,
                "total_amount": 0.0,
                "by_category": {},
                "by_status": {},
                "by_month": {}
            }
        
        # Calculate statistics
        total_amount = sum(inv.get("total", 0) for inv in invoices)
        
        # Group by category
        by_category = {}
        for inv in invoices:
            category = inv.get("category", "Unknown")
            if category not in by_category:
                by_category[category] = {"count": 0, "amount": 0.0}
            by_category[category]["count"] += 1
            by_category[category]["amount"] += inv.get("total", 0)
        
        # Group by status
        by_status = {}
        for inv in invoices:
            status = inv.get("status", "Unknown")
            if status not in by_status:
                by_status[status] = {"count": 0, "amount": 0.0}
            by_status[status]["count"] += 1
            by_status[status]["amount"] += inv.get("total", 0)
        
        # Group by month
        by_month = {}
        for inv in invoices:
            date_str = inv.get("date", "")
            if date_str:
                try:
                    month_key = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m")
                    if month_key not in by_month:
                        by_month[month_key] = {"count": 0, "amount": 0.0}
                    by_month[month_key]["count"] += 1
                    by_month[month_key]["amount"] += inv.get("total", 0)
                except ValueError:
                    pass
        
        return {
            "total_invoices": len(invoices),
            "total_amount": round(total_amount, 2),
            "average_amount": round(total_amount / len(invoices), 2) if invoices else 0.0,
            "by_category": by_category,
            "by_status": by_status,
            "by_month": by_month
        }
    
    @staticmethod
    def generate_vendor_spending_report(
        invoices: List[Dict[str, Any]],
        vendors: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate vendor spending report.
        
        Args:
            invoices: List of invoice dictionaries
            vendors: Dictionary of vendor_id -> vendor data
            
        Returns:
            List of vendor spending summaries
        """
        vendor_spending = {}
        
        for inv in invoices:
            vendor_id = inv.get("vendor_id")
            if not vendor_id:
                continue
            
            if vendor_id not in vendor_spending:
                vendor_data = vendors.get(vendor_id, {})
                vendor_spending[vendor_id] = {
                    "vendor_id": vendor_id,
                    "vendor_name": vendor_data.get("name", "Unknown"),
                    "invoice_count": 0,
                    "total_amount": 0.0,
                    "average_amount": 0.0,
                    "statuses": {}
                }
            
            vendor_spending[vendor_id]["invoice_count"] += 1
            vendor_spending[vendor_id]["total_amount"] += inv.get("total", 0)
            
            status = inv.get("status", "Unknown")
            if status not in vendor_spending[vendor_id]["statuses"]:
                vendor_spending[vendor_id]["statuses"][status] = 0
            vendor_spending[vendor_id]["statuses"][status] += 1
        
        # Calculate averages and sort
        result = []
        for vendor_data in vendor_spending.values():
            if vendor_data["invoice_count"] > 0:
                vendor_data["average_amount"] = round(
                    vendor_data["total_amount"] / vendor_data["invoice_count"],
                    2
                )
            vendor_data["total_amount"] = round(vendor_data["total_amount"], 2)
            result.append(vendor_data)
        
        # Sort by total amount descending
        result.sort(key=lambda x: x["total_amount"], reverse=True)
        
        return result
