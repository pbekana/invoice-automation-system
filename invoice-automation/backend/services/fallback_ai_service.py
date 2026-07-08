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
            
            # Pattern: Total spending / total / spend
            if any(word in message_lower for word in ['total', 'spend', 'spending', 'spent']):
                return self._handle_total_spending()
            
            # Pattern: Invoices from specific company
            company_match = re.search(r'(?:invoices?\s+(?:from|for|by)\s+)([a-zA-Z0-9\s]+)', message_lower)
            if company_match:
                company = company_match.group(1).strip()
                return self._handle_company_invoices(company)
            
            # Pattern: Search by category
            if any(word in message_lower for word in ['software', 'transport', 'food', 'supplies']):
                for category in ['Software', 'Transport', 'Food', 'Supplies']:
                    if category.lower() in message_lower:
                        return self._handle_category_search(category)
            
            # Pattern: Pending / unpaid invoices
            if any(word in message_lower for word in ['pending', 'unpaid', 'waiting', 'outstanding']):
                return self._handle_pending_invoices()
            
            # Pattern: Paid invoices
            if 'paid' in message_lower and 'unpaid' not in message_lower:
                return self._handle_paid_invoices()
            
            # Pattern: Recent invoices / latest
            if any(word in message_lower for word in ['recent', 'latest', 'last']):
                return self._handle_recent_invoices()
            
            # Pattern: Count / how many
            if any(word in message_lower for word in ['how many', 'count', 'number of']):
                return self._handle_invoice_count()
            
            # Pattern: Vendors / suppliers
            if any(word in message_lower for word in ['vendor', 'supplier', 'company', 'companies']):
                return self._handle_vendors()
            
            # Pattern: Categories / breakdown
            if any(word in message_lower for word in ['categor', 'breakdown', 'distribution']):
                return self._handle_category_breakdown()
            
            # Pattern: This month / this year
            if 'this month' in message_lower:
                return self._handle_this_month()
            
            if 'this year' in message_lower:
                return self._handle_this_year()
            
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
    
    def _handle_total_spending(self) -> Dict[str, Any]:
        """Handle total spending queries"""
        try:
            stats = self.db_manager.get_dashboard_summary()
            total = stats.get('grand_total', 0)
            count = stats.get('total_invoices', 0)
            
            response = f"📊 **Total Spending**: ${total:,.2f}\n\n"
            response += f"You have **{count} invoices** in the system.\n\n"
            
            # Add category breakdown if available
            categories = stats.get('categories', {})
            if categories:
                response += "**Breakdown by Category:**\n"
                # Sort by total amount descending
                sorted_categories = sorted(
                    categories.items(),
                    key=lambda x: x[1].get('total', 0) if isinstance(x[1], dict) else 0,
                    reverse=True
                )
                for category, data in sorted_categories:
                    if isinstance(data, dict):
                        amount = data.get('total', 0)
                        count = data.get('count', 0)
                        percentage = (amount / total * 100) if total > 0 else 0
                        response += f"- {category}: ${amount:,.2f} ({count} invoices, {percentage:.1f}%)\n"
            
            return {"response": response, "tools_used": ["database_query"]}
        except Exception as e:
            logger.error(f"Error getting total spending: {e}")
            return {"response": "I couldn't retrieve spending data. Please check the database connection."}
    
    def _handle_company_invoices(self, company: str) -> Dict[str, Any]:
        """Handle company-specific invoice queries"""
        try:
            from config import Config
            invoices = list(
                self.db_manager.db[Config.INVOICES_COLLECTION].find(
                    {"company": {"$regex": company, "$options": "i"}},
                    {"_id": 0, "invoice_id": 1, "company": 1, "total": 1, "status": 1, "date": 1}
                ).limit(10)
            )
            
            if not invoices:
                return {"response": f"No invoices found for **{company}**. Try checking the spelling or search for another company."}
            
            total_amount = sum(inv.get('total', 0) for inv in invoices)
            
            response = f"📄 **Invoices from {company.title()}**\n\n"
            response += f"Found **{len(invoices)}** invoices (total: ${total_amount:,.2f})\n\n"
            
            for inv in invoices[:5]:
                status_emoji = "✅" if inv.get('status') == 'paid' else "⏳" if inv.get('status') == 'pending' else "📝"
                response += f"{status_emoji} {inv.get('invoice_id', 'N/A')} - ${inv.get('total', 0):,.2f} ({inv.get('status', 'unknown')})\n"
            
            if len(invoices) > 5:
                response += f"\n...and {len(invoices) - 5} more"
            
            return {"response": response, "tools_used": ["search_invoices"]}
        except Exception as e:
            logger.error(f"Error searching company invoices: {e}")
            return {"response": f"I couldn't search for invoices from {company}."}
    
    def _handle_category_search(self, category: str) -> Dict[str, Any]:
        """Handle category-specific queries"""
        try:
            from config import Config
            invoices = list(
                self.db_manager.db[Config.INVOICES_COLLECTION].find(
                    {"category": category},
                    {"_id": 0, "invoice_id": 1, "company": 1, "total": 1, "status": 1}
                ).limit(10)
            )
            
            if not invoices:
                return {"response": f"No **{category}** invoices found."}
            
            total_amount = sum(inv.get('total', 0) for inv in invoices)
            
            response = f"🏷️ **{category} Invoices**\n\n"
            response += f"Found **{len(invoices)}** {category.lower()} invoices totaling ${total_amount:,.2f}\n\n"
            
            for inv in invoices[:5]:
                response += f"• {inv.get('company', 'Unknown')} - ${inv.get('total', 0):,.2f}\n"
            
            return {"response": response, "tools_used": ["search_invoices"]}
        except Exception as e:
            logger.error(f"Error searching category: {e}")
            return {"response": f"I couldn't search for {category} invoices."}
    
    def _handle_pending_invoices(self) -> Dict[str, Any]:
        """Handle pending invoice queries"""
        try:
            from config import Config
            invoices = list(
                self.db_manager.db[Config.INVOICES_COLLECTION].find(
                    {"status": {"$in": ["pending", "submitted", "pending_approval"]}},
                    {"_id": 0, "invoice_id": 1, "company": 1, "total": 1, "status": 1, "date": 1}
                ).limit(10)
            )
            
            if not invoices:
                return {"response": "✅ **Great news!** You have no pending invoices. Everything is up to date!"}
            
            total_amount = sum(inv.get('total', 0) for inv in invoices)
            
            response = f"⏳ **Pending Invoices**\n\n"
            response += f"You have **{len(invoices)} pending invoices** totaling ${total_amount:,.2f}\n\n"
            
            for inv in invoices[:5]:
                response += f"• {inv.get('company', 'Unknown')} - ${inv.get('total', 0):,.2f} ({inv.get('status', 'pending')})\n"
            
            return {"response": response, "tools_used": ["search_invoices"]}
        except Exception as e:
            logger.error(f"Error getting pending invoices: {e}")
            return {"response": "I couldn't retrieve pending invoices."}
    
    def _handle_paid_invoices(self) -> Dict[str, Any]:
        """Handle paid invoice queries"""
        try:
            from config import Config
            count = self.db_manager.db[Config.INVOICES_COLLECTION].count_documents({"status": "paid"})
            
            if count == 0:
                return {"response": "No paid invoices found in the system."}
            
            # Get total paid amount
            pipeline = [
                {"$match": {"status": "paid"}},
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
    
    def _handle_recent_invoices(self) -> Dict[str, Any]:
        """Handle recent invoice queries"""
        try:
            from config import Config
            invoices = list(
                self.db_manager.db[Config.INVOICES_COLLECTION].find(
                    {},
                    {"_id": 0, "invoice_id": 1, "company": 1, "total": 1, "status": 1, "date": 1}
                ).sort("date", -1).limit(5)
            )
            
            if not invoices:
                return {"response": "No invoices found in the system."}
            
            response = "📅 **Recent Invoices**\n\n"
            
            for inv in invoices:
                status_emoji = "✅" if inv.get('status') == 'paid' else "⏳" if inv.get('status') == 'pending' else "📝"
                date_str = inv.get('date', 'No date')
                response += f"{status_emoji} **{inv.get('company', 'Unknown')}** - ${inv.get('total', 0):,.2f}\n"
                response += f"   ID: {inv.get('invoice_id', 'N/A')} | Status: {inv.get('status', 'unknown')}\n\n"
            
            return {"response": response, "tools_used": ["search_invoices"]}
        except Exception as e:
            logger.error(f"Error getting recent invoices: {e}")
            return {"response": "I couldn't retrieve recent invoices."}
    
    def _handle_invoice_count(self) -> Dict[str, Any]:
        """Handle invoice count queries"""
        try:
            stats = self.db_manager.get_dashboard_summary()
            total = stats.get('total_invoices', 0)
            
            response = f"📊 You have **{total} invoices** in the system.\n\n"
            
            # Add status breakdown
            from config import Config
            statuses = self.db_manager.db[Config.INVOICES_COLLECTION].aggregate([
                {"$group": {"_id": "$status", "count": {"$sum": 1}}}
            ])
            
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
    
    def _handle_category_breakdown(self) -> Dict[str, Any]:
        """Handle category breakdown queries"""
        return self._handle_total_spending()  # Same as total spending with breakdown
    
    def _handle_this_month(self) -> Dict[str, Any]:
        """Handle this month queries"""
        try:
            from config import Config
            from datetime import datetime
            
            # Get start of current month
            now = datetime.now()
            month_start = datetime(now.year, now.month, 1)
            
            count = self.db_manager.db[Config.INVOICES_COLLECTION].count_documents({
                "date": {"$gte": month_start.strftime("%Y-%m-%d")}
            })
            
            # Get total for this month
            pipeline = [
                {"$match": {"date": {"$gte": month_start.strftime("%Y-%m-%d")}}},
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
    
    def _handle_this_year(self) -> Dict[str, Any]:
        """Handle this year queries"""
        try:
            from config import Config
            from datetime import datetime
            
            now = datetime.now()
            year_start = f"{now.year}-01-01"
            
            count = self.db_manager.db[Config.INVOICES_COLLECTION].count_documents({
                "date": {"$gte": year_start}
            })
            
            # Get total for this year
            pipeline = [
                {"$match": {"date": {"$gte": year_start}}},
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
        response = """🤖 **I can help you with:**

**Financial Queries:**
- "What's my total spending?"
- "Show me pending invoices"
- "How much did I spend this month?"

**Search Queries:**
- "Show invoices from Amazon"
- "Find software invoices"
- "What are my recent invoices?"

**Information:**
- "How many invoices do I have?"
- "Show me all vendors"
- "Category breakdown"

**Tip:** I work without API keys using smart pattern matching and database queries!
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
