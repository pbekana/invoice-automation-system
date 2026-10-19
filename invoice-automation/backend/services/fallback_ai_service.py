"""
Fallback AI Service - Works without API keys
Uses pattern matching and database queries to provide intelligent responses
"""

import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from logger_config import logger


class FallbackAIService:
    """
    Smart fallback AI assistant that works without external API keys.
    Uses pattern matching and direct database queries.
    """
    
    def __init__(self, db_manager):
        """Initialize the fallback AI service"""
        self.db_manager = db_manager
        logger.info("Fallback AI Service initialized (no API keys required)")
    
    def chat(
        self,
        message: str,
        session_id: str = "default",
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a chat message using pattern matching and database queries
        
        Args:
            message: User's message
            session_id: Session ID (not used in fallback)
            user_id: User ID for logging
        
        Returns:
            Dictionary with response
        """
        try:
            logger.info(f"Fallback AI processing: '{message[:50]}...'")
            
            message_lower = message.lower().strip()
            
            # Pattern: Overdue / late / past due
            if any(word in message_lower for word in ['overdue', 'late', 'past due']):
                return self._handle_overdue_invoices(user_id)

            # Pattern: Duplicate invoices / duplicates
            if any(word in message_lower for word in ['duplicate', 'duplicates']):
                return self._handle_duplicate_invoices(user_id)

            # Pattern: Validation issues / invalid / flagged / discrepancy
            if any(word in message_lower for word in ['validation', 'invalid', 'flagged', 'discrepanc']):
                return self._handle_validation_issues(user_id)

            # Pattern: Purchase orders / PO
            if any(word in message_lower for word in ['purchase order', 'po matching', 'pos']):
                return self._handle_purchase_orders()

            # Pattern: AR aging / receivables
            if any(word in message_lower for word in ['aging', 'receivable', 'receivables', 'ar report']):
                return self._handle_aging_report()

            # Pattern: Total spending / total / spend
            if any(word in message_lower for word in ['total', 'spend', 'spending', 'spent']):
                return self._handle_total_spending(user_id)
            
            # Pattern: Invoices from specific company
            company_match = re.search(r'(?:invoices?\s+(?:from|for|by)\s+)([a-zA-Z0-9\s]+)', message_lower)
            if company_match:
                company = company_match.group(1).strip()
                return self._handle_company_invoices(company, user_id)
            
            # Pattern: Search by category
            if any(word in message_lower for word in ['software', 'transport', 'food', 'supplies']):
                for category in ['Software', 'Transport', 'Food', 'Supplies']:
                    if category.lower() in message_lower:
                        return self._handle_category_search(category, user_id)
            
            # Pattern: Pending / unpaid invoices
            if any(word in message_lower for word in ['pending', 'unpaid', 'waiting', 'outstanding']):
                return self._handle_pending_invoices(user_id)
            
            # Pattern: Paid invoices
            if 'paid' in message_lower and 'unpaid' not in message_lower:
                return self._handle_paid_invoices(user_id)
            
            # Pattern: Recent invoices / latest
            if any(word in message_lower for word in ['recent', 'latest', 'last']):
                return self._handle_recent_invoices(user_id)
            
            # Pattern: Count / how many
            if any(word in message_lower for word in ['how many', 'count', 'number of']):
                return self._handle_invoice_count(user_id)
            
            # Pattern: Vendors / suppliers
            if any(word in message_lower for word in ['vendor', 'supplier', 'company', 'companies']):
                return self._handle_vendors()
            
            # Pattern: Categories / breakdown
            if any(word in message_lower for word in ['categor', 'breakdown', 'distribution']):
                return self._handle_category_breakdown(user_id)
            
            # Pattern: This month / this year
            if 'this month' in message_lower:
                return self._handle_this_month(user_id)
            
            if 'this year' in message_lower:
                return self._handle_this_year(user_id)
            
            # Pattern: Help / what can you do
            if any(word in message_lower for word in ['help', 'what can', 'capabilities', 'can you']):
                return self._handle_help()
            
            # Default response with suggestions
            return {
                "response": self._get_default_response(),
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"Fallback AI error: {e}", exc_info=True)
            return {
                "response": "I had trouble processing that. Try asking about your total spending, recent invoices, or pending payments.",
                "error": str(e)
            }
    
    def _get_user_scope_filter(self, user_id: Optional[str]) -> Dict[str, Any]:
        """Scope queries based on user role: submitters only see their own invoices."""
        if not user_id or not self.db_manager or self.db_manager.db is None:
            return {}
        try:
            from bson import ObjectId
            user = self.db_manager.db["users"].find_one({"_id": ObjectId(user_id)})
            if user:
                roles = user.get("roles", [])
                if "admin" in roles or "approver" in roles:
                    return {}
                if "submitter" in roles:
                    return {"submitter_id": user_id}
        except Exception as e:
            logger.error(f"Error determining user scope filter: {e}")
        return {}

    def _handle_overdue_invoices(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle overdue invoice queries."""
        try:
            from config import Config
            today_str = datetime.utcnow().strftime("%Y-%m-%d")
            query = {
                "due_date": {"$lt": today_str, "$ne": None},
                "status": {"$nin": ["paid", "cancelled", "rejected"]}
            }
            query.update(self._get_user_scope_filter(user_id))
            
            invoices = list(self.db_manager.db[Config.INVOICES_COLLECTION].find(
                query,
                {"_id": 1, "invoice_number": 1, "company": 1, "total": 1, "due_date": 1, "status": 1}
            ).sort("due_date", 1).limit(10))

            if not invoices:
                return {"response": "✅ **Great news!** You have no overdue invoices. All accounts are in good standing!"}

            total_overdue = sum(inv.get('total', 0) for inv in invoices)
            response = f"⚠️ **Overdue Invoices Alert**\n\n"
            response += f"Found **{len(invoices)} overdue invoices** totaling ${total_overdue:,.2f}:\n\n"

            for inv in invoices[:5]:
                inv_num = inv.get("invoice_number") or str(inv.get("_id"))
                response += f"• **{inv.get('company', 'Unknown')}** - ${inv.get('total', 0):,.2f} (Due: {inv.get('due_date')}, #{inv_num})\n"

            if len(invoices) > 5:
                response += f"\n...and {len(invoices) - 5} more overdue invoices."

            return {"response": response, "tools_used": ["database_query"]}
        except Exception as e:
            logger.error(f"Error querying overdue invoices: {e}")
            return {"response": "I couldn't retrieve overdue invoice records."}

    def _handle_duplicate_invoices(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle potential duplicate invoice queries."""
        try:
            from config import Config
            query = {"duplicate_status": {"$in": ["potential_duplicate", "definite_duplicate"]}}
            query.update(self._get_user_scope_filter(user_id))

            duplicates = list(self.db_manager.db[Config.INVOICES_COLLECTION].find(
                query,
                {"_id": 1, "invoice_number": 1, "company": 1, "total": 1, "date": 1, "duplicate_investigation": 1}
            ).limit(10))

            if not duplicates:
                return {"response": "✅ No pending duplicate warnings found. All invoices passed duplicate detection!"}

            response = f"🔍 **Potential Duplicate Invoices Detected**\n\n"
            response += f"Found **{len(duplicates)}** invoices flagged for review:\n\n"
            for dup in duplicates[:5]:
                inv_num = dup.get("invoice_number") or str(dup.get("_id"))
                response += f"• **{dup.get('company', 'Unknown')}** (#{inv_num}) - ${dup.get('total', 0):,.2f} on {dup.get('date')}\n"

            response += "\nPlease review these flagged invoices in the approval queue before approving payments."
            return {"response": response, "tools_used": ["duplicate_detector"]}
        except Exception as e:
            logger.error(f"Error checking duplicates: {e}")
            return {"response": "I couldn't check for duplicate invoices."}

    def _handle_validation_issues(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle validation and discrepancy queries."""
        try:
            from config import Config
            query = {
                "$or": [
                    {"validation.is_valid": False},
                    {"po_match_status": "discrepancy_exception"}
                ]
            }
            query.update(self._get_user_scope_filter(user_id))

            issues = list(self.db_manager.db[Config.INVOICES_COLLECTION].find(
                query,
                {"_id": 1, "invoice_number": 1, "company": 1, "total": 1, "validation": 1, "po_match_status": 1}
            ).limit(10))

            if not issues:
                return {"response": "✅ All invoices have valid mathematical totals, complete fields, and verified PO matches!"}

            response = f"⚠️ **Invoices with Validation or PO Discrepancies**\n\n"
            response += f"Found **{len(issues)}** invoices requiring attention:\n\n"
            for item in issues[:5]:
                inv_num = item.get("invoice_number") or str(item.get("_id"))
                val = item.get("validation", {})
                flags = val.get("flags", [])
                po_status = item.get("po_match_status")
                flag_text = ", ".join(flags) if flags else (f"PO {po_status}" if po_status else "validation error")
                response += f"• **{item.get('company', 'Unknown')}** (#{inv_num}): {flag_text}\n"

            return {"response": response, "tools_used": ["validation_check"]}
        except Exception as e:
            logger.error(f"Error querying validation issues: {e}")
            return {"response": "I couldn't retrieve invoice validation issues."}

    def _handle_purchase_orders(self) -> Dict[str, Any]:
        """Handle purchase order inquiries."""
        try:
            pos = list(self.db_manager.db["purchase_orders"].find(
                {},
                {"_id": 1, "po_number": 1, "vendor_name": 1, "total_amount": 1, "status": 1}
            ).limit(10))

            if not pos:
                return {"response": "No Purchase Orders currently recorded in the procurement system."}

            response = f"📋 **Purchase Orders** (showing {len(pos)}):\n\n"
            for po in pos[:5]:
                response += f"• **{po.get('po_number')}** - {po.get('vendor_name')}: ${po.get('total_amount', 0):,.2f} ({po.get('status', 'open')})\n"
            return {"response": response, "tools_used": ["database_query"]}
        except Exception as e:
            logger.error(f"Error querying purchase orders: {e}")
            return {"response": "I couldn't retrieve purchase orders."}

    def _handle_aging_report(self) -> Dict[str, Any]:
        """Handle Accounts Receivable aging queries."""
        try:
            from services.ar_service import ARService
            ar_service = ARService(self.db_manager.db)
            report = ar_service.get_aging_report()
            buckets = report.get("aging_buckets", {})
            total_ar = report.get("total_outstanding", 0.0)

            response = f"📈 **Accounts Receivable Aging Summary**\n\n"
            response += f"**Total AR Outstanding**: ${total_ar:,.2f}\n\n"
            response += f"• Current (Not Overdue): ${buckets.get('current', 0):,.2f}\n"
            response += f"• 1-30 Days Overdue: ${buckets.get('days_1_30', 0):,.2f}\n"
            response += f"• 31-60 Days Overdue: ${buckets.get('days_31_60', 0):,.2f}\n"
            response += f"• 61-90 Days Overdue: ${buckets.get('days_61_90', 0):,.2f}\n"
            response += f"• 90+ Days Overdue: ${buckets.get('days_90_plus', 0):,.2f}\n"
            return {"response": response, "tools_used": ["ar_aging_engine"]}
        except Exception as e:
            logger.error(f"Error generating AR aging report: {e}")
            return {"response": "I couldn't calculate the AR aging report."}

    def _handle_total_spending(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle total spending queries"""
        try:
            scope = self._get_user_scope_filter(user_id)
            from config import Config
            pipeline = [
                {"$match": {"status": {"$nin": ["cancelled", "rejected"]}, **scope}},
                {"$group": {"_id": None, "total": {"$sum": "$total"}, "count": {"$sum": 1}}}
            ]
            res = list(self.db_manager.db[Config.INVOICES_COLLECTION].aggregate(pipeline))
            total = res[0]['total'] if res else 0.0
            count = res[0]['count'] if res else 0
            
            response = f"📊 **Total Spending**: ${total:,.2f}\n\n"
            response += f"You have **{count} active invoices** in the system.\n\n"
            
            # Category breakdown
            cat_pipeline = [
                {"$match": {"status": {"$nin": ["cancelled", "rejected"]}, **scope}},
                {"$group": {"_id": "$category", "total": {"$sum": "$total"}, "count": {"$sum": 1}}},
                {"$sort": {"total": -1}}
            ]
            cat_res = list(self.db_manager.db[Config.INVOICES_COLLECTION].aggregate(cat_pipeline))
            if cat_res:
                response += "**Breakdown by Category:**\n"
                for item in cat_res:
                    category = item['_id'] or 'General'
                    amount = item['total']
                    c = item['count']
                    pct = (amount / total * 100) if total > 0 else 0
                    response += f"- {category}: ${amount:,.2f} ({c} invoices, {pct:.1f}%)\n"
            
            return {"response": response, "tools_used": ["database_query"]}
        except Exception as e:
            logger.error(f"Error getting total spending: {e}")
            return {"response": "I couldn't retrieve spending data. Please check the database connection."}
    
    def _handle_company_invoices(self, company: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle company-specific invoice queries"""
        try:
            from config import Config
            query = {"company": {"$regex": company, "$options": "i"}}
            query.update(self._get_user_scope_filter(user_id))

            invoices = list(
                self.db_manager.db[Config.INVOICES_COLLECTION].find(
                    query,
                    {"_id": 1, "invoice_number": 1, "company": 1, "total": 1, "status": 1, "date": 1}
                ).limit(10)
            )
            
            if not invoices:
                return {"response": f"No invoices found for **{company}**. Try checking the spelling or search for another company."}
            
            total_amount = sum(inv.get('total', 0) for inv in invoices)
            
            response = f"📄 **Invoices from {company.title()}**\n\n"
            response += f"Found **{len(invoices)}** invoices (total: ${total_amount:,.2f})\n\n"
            
            for inv in invoices[:5]:
                status_emoji = "✅" if inv.get('status') == 'paid' else "⏳" if inv.get('status') == 'pending' else "📝"
                inv_num = inv.get("invoice_number") or str(inv.get("_id"))
                response += f"{status_emoji} #{inv_num} - ${inv.get('total', 0):,.2f} ({inv.get('status', 'unknown')})\n"
            
            if len(invoices) > 5:
                response += f"\n...and {len(invoices) - 5} more"
            
            return {"response": response, "tools_used": ["search_invoices"]}
        except Exception as e:
            logger.error(f"Error searching company invoices: {e}")
            return {"response": f"I couldn't search for invoices from {company}."}
    
    def _handle_category_search(self, category: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle category-specific queries"""
        try:
            from config import Config
            query = {"category": category}
            query.update(self._get_user_scope_filter(user_id))

            invoices = list(
                self.db_manager.db[Config.INVOICES_COLLECTION].find(
                    query,
                    {"_id": 1, "invoice_number": 1, "company": 1, "total": 1, "status": 1}
                ).limit(10)
            )
            
            if not invoices:
                return {"response": f"No **{category}** invoices found."}
            
            total_amount = sum(inv.get('total', 0) for inv in invoices)
            
            response = f"🏷️ **{category} Invoices**\n\n"
            response += f"Found **{len(invoices)}** {category.lower()} invoices totaling ${total_amount:,.2f}\n\n"
            
            for inv in invoices[:5]:
                inv_num = inv.get("invoice_number") or str(inv.get("_id"))
                response += f"• **{inv.get('company', 'Unknown')}** (#{inv_num}) - ${inv.get('total', 0):,.2f}\n"
            
            return {"response": response, "tools_used": ["search_invoices"]}
        except Exception as e:
            logger.error(f"Error searching category: {e}")
            return {"response": f"I couldn't search for {category} invoices."}
    
    def _handle_pending_invoices(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle pending invoice queries"""
        try:
            from config import Config
            query = {"status": {"$in": ["pending", "submitted", "pending_approval", "partially_paid"]}}
            query.update(self._get_user_scope_filter(user_id))

            invoices = list(
                self.db_manager.db[Config.INVOICES_COLLECTION].find(
                    query,
                    {"_id": 1, "invoice_number": 1, "company": 1, "total": 1, "status": 1, "date": 1}
                ).limit(10)
            )
            
            if not invoices:
                return {"response": "✅ **Great news!** You have no pending invoices. Everything is up to date!"}
            
            total_amount = sum(inv.get('total', 0) for inv in invoices)
            
            response = f"⏳ **Pending Invoices**\n\n"
            response += f"You have **{len(invoices)} pending invoices** totaling ${total_amount:,.2f}\n\n"
            
            for inv in invoices[:5]:
                inv_num = inv.get("invoice_number") or str(inv.get("_id"))
                response += f"• **{inv.get('company', 'Unknown')}** (#{inv_num}) - ${inv.get('total', 0):,.2f} ({inv.get('status', 'pending')})\n"
            
            return {"response": response, "tools_used": ["search_invoices"]}
        except Exception as e:
            logger.error(f"Error getting pending invoices: {e}")
            return {"response": "I couldn't retrieve pending invoices."}
    
    def _handle_paid_invoices(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle paid invoice queries"""
        try:
            from config import Config
            query = {"status": "paid"}
            query.update(self._get_user_scope_filter(user_id))

            count = self.db_manager.db[Config.INVOICES_COLLECTION].count_documents(query)
            
            if count == 0:
                return {"response": "No paid invoices found in the system."}
            
            # Get total paid amount
            pipeline = [
                {"$match": query},
                {"$group": {"_id": None, "total": {"$sum": "$total"}}}
            ]
            result = list(self.db_manager.db[Config.INVOICES_COLLECTION].aggregate(pipeline))
            total_paid = result[0]['total'] if result else 0
            
            response = f"✅ **Paid Invoices**\n\n"
            response += f"You have **{count} paid invoices** totaling ${total_paid:,.2f}"
            
            return {"response": response, "tools_used": ["database_query"]}
        except Exception as e:
            logger.error(f"Error getting paid invoices: {e}")
            return {"response": "I couldn't retrieve paid invoice information."}
            
    def _handle_recent_invoices(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle recent invoice queries"""
        try:
            from config import Config
            query = {}
            query.update(self._get_user_scope_filter(user_id))

            invoices = list(
                self.db_manager.db[Config.INVOICES_COLLECTION].find(
                    query,
                    {"_id": 1, "invoice_number": 1, "company": 1, "total": 1, "status": 1, "date": 1}
                ).sort("date", -1).limit(5)
            )
            
            if not invoices:
                return {"response": "No invoices found in the system."}
            
            response = "📅 **Recent Invoices**\n\n"
            
            for inv in invoices:
                status_emoji = "✅" if inv.get('status') == 'paid' else "⏳" if inv.get('status') == 'pending' else "📝"
                inv_num = inv.get("invoice_number") or str(inv.get("_id"))
                response += f"{status_emoji} **{inv.get('company', 'Unknown')}** (#{inv_num}) - ${inv.get('total', 0):,.2f}\n"
                response += f"   Date: {inv.get('date', 'N/A')} | Status: {inv.get('status', 'unknown')}\n\n"
            
            return {"response": response, "tools_used": ["search_invoices"]}
        except Exception as e:
            logger.error(f"Error getting recent invoices: {e}")
            return {"response": "I couldn't retrieve recent invoices."}
    
    def _handle_invoice_count(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle invoice count queries"""
        try:
            from config import Config
            scope = self._get_user_scope_filter(user_id)
            total = self.db_manager.db[Config.INVOICES_COLLECTION].count_documents(scope)
            
            response = f"📊 You have **{total} invoices** in the system.\n\n"
            
            # Add status breakdown
            pipeline = [
                {"$match": scope},
                {"$group": {"_id": "$status", "count": {"$sum": 1}}}
            ]
            statuses = self.db_manager.db[Config.INVOICES_COLLECTION].aggregate(pipeline)
            
            response += "**By Status:**\n"
            for status_doc in statuses:
                status = status_doc['_id'] or 'unknown'
                count = status_doc['count']
                response += f"- {status.title()}: {count}\n"
            
            return {"response": response, "tools_used": ["database_query"]}
        except Exception as e:
            logger.error(f"Error counting invoices: {e}")
            return {"response": "I couldn't count the invoices."}
    
    def _handle_vendors(self) -> Dict[str, Any]:
        """Handle vendor queries"""
        try:
            from config import Config
            vendors = list(
                self.db_manager.db[Config.VENDORS_COLLECTION].find(
                    {},
                    {"_id": 0, "name": 1, "category": 1, "contact_email": 1}
                ).limit(10)
            )
            
            if not vendors:
                return {"response": "No vendors found in the system."}
            
            response = f"🏢 **Vendors** (showing {len(vendors)})\n\n"
            
            for vendor in vendors:
                response += f"• **{vendor.get('name', 'Unknown')}**"
                if vendor.get('category'):
                    response += f" - {vendor.get('category')}"
                response += "\n"
            
            return {"response": response, "tools_used": ["search_vendors"]}
        except Exception as e:
            logger.error(f"Error getting vendors: {e}")
            return {"response": "I couldn't retrieve vendor information."}
    
    def _handle_category_breakdown(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle category breakdown queries"""
        return self._handle_total_spending(user_id)
    
    def _handle_this_month(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle this month queries"""
        try:
            from config import Config
            from datetime import datetime
            
            now = datetime.now()
            month_start = datetime(now.year, now.month, 1).strftime("%Y-%m-%d")
            query = {"date": {"$gte": month_start}}
            query.update(self._get_user_scope_filter(user_id))
            
            count = self.db_manager.db[Config.INVOICES_COLLECTION].count_documents(query)
            
            pipeline = [
                {"$match": query},
                {"$group": {"_id": None, "total": {"$sum": "$total"}}}
            ]
            result = list(self.db_manager.db[Config.INVOICES_COLLECTION].aggregate(pipeline))
            total = result[0]['total'] if result else 0
            
            response = f"📅 **This Month** ({now.strftime('%B %Y')})\n\n"
            response += f"**{count} invoices** totaling ${total:,.2f}"
            
            return {"response": response, "tools_used": ["database_query"]}
        except Exception as e:
            logger.error(f"Error getting this month data: {e}")
            return {"response": "I couldn't retrieve this month's data."}
    
    def _handle_this_year(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle this year queries"""
        try:
            from config import Config
            from datetime import datetime
            
            now = datetime.now()
            year_start = f"{now.year}-01-01"
            query = {"date": {"$gte": year_start}}
            query.update(self._get_user_scope_filter(user_id))
            
            count = self.db_manager.db[Config.INVOICES_COLLECTION].count_documents(query)
            
            pipeline = [
                {"$match": query},
                {"$group": {"_id": None, "total": {"$sum": "$total"}}}
            ]
            result = list(self.db_manager.db[Config.INVOICES_COLLECTION].aggregate(pipeline))
            total = result[0]['total'] if result else 0
            
            response = f"📅 **This Year** ({now.year})\n\n"
            response += f"**{count} invoices** totaling ${total:,.2f}"
            
            return {"response": response, "tools_used": ["database_query"]}
        except Exception as e:
            logger.error(f"Error getting this year data: {e}")
            return {"response": "I couldn't retrieve this year's data."}
    
    def _handle_help(self) -> Dict[str, Any]:
        """Handle help queries"""
        response = """🤖 **Invoice AI Assistant Capabilities:**

**Financial & Analytics:**
- "What's my total spending?"
- "Show me pending invoices"
- "Show overdue invoices"
- "How much did I spend this month / this year?"
- "Show category breakdown"

**Operational Controls & Verification:**
- "Are there any duplicate invoices?"
- "Show validation errors or PO discrepancies"
- "Show purchase orders"
- "Show Accounts Receivable aging report"

**Search & Retrieval:**
- "Show invoices from [Vendor Name]"
- "Find software invoices"
- "What are my recent invoices?"
- "How many invoices do I have?"
- "Show all vendors"

**Security & Reliability:**
- All financial answers are grounded in validated records without hallucinated figures.
- Fallback mode operates completely offline without external API dependencies.
"""
        return {"response": response}
    
    def _get_default_response(self) -> str:
        """Get default response when pattern not matched"""
        return """I'm not sure how to help with that. Try asking:

• "What's my total spending?"
• "Show me pending invoices"
• "Find invoices from [company name]"
• "How many software invoices do I have?"
• "Show recent invoices"

Type **"help"** to see all available commands."""
    
    def clear_history(self, session_id: str):
        """Clear history (no-op for fallback service)"""
        logger.info(f"History clear requested for session {session_id} (fallback service doesn't use history)")


# Singleton instance
fallback_ai_service = None


def initialize_fallback_ai(db_manager):
    """Initialize the fallback AI service"""
    global fallback_ai_service
    fallback_ai_service = FallbackAIService(db_manager)
    return fallback_ai_service


def get_fallback_ai():
    """Get the fallback AI service instance"""
    return fallback_ai_service
