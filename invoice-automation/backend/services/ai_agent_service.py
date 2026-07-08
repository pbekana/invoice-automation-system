"""
AI Agent Service - Production-ready LangChain Agent for Invoice Automation
Supports Claude and OpenAI with tool-calling, memory, and structured outputs
"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

# LangChain imports
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

from config import Config
from logger_config import logger


# ============================================================================
# STRUCTURED OUTPUT MODELS
# ============================================================================

class InvoiceInfo(BaseModel):
    """Information about a specific invoice"""
    invoice_id: Optional[str] = Field(None, description="Invoice ID if found")
    company: Optional[str] = Field(None, description="Company name")
    total: Optional[float] = Field(None, description="Invoice total amount")
    status: Optional[str] = Field(None, description="Invoice status")
    category: Optional[str] = Field(None, description="Invoice category")


class AgentResponse(BaseModel):
    """Structured response from the AI agent"""
    response: str = Field(..., description="The main response message")
    confidence: float = Field(..., description="Confidence score between 0 and 1")
    suggested_actions: List[str] = Field(default_factory=list, description="Suggested next actions")
    referenced_invoices: List[InvoiceInfo] = Field(default_factory=list, description="Invoices mentioned")
    tools_used: List[str] = Field(default_factory=list, description="Tools that were called")
    requires_clarification: bool = Field(False, description="Whether the query needs clarification")


# ============================================================================
# AI AGENT SERVICE
# ============================================================================

class AIAgentService:
    """
    Production AI Agent for Invoice Automation
    - Multi-provider support (Claude/OpenAI)
    - Tool-calling architecture
    - Conversation memory
    - Structured outputs
    """
    
    def __init__(self, db_manager=None):
        """Initialize the AI agent with configurable LLM provider"""
        self.db_manager = db_manager
        self.llm = self._initialize_llm()
        self.tools = self._create_tools()
        self.agent = None
        self.agent_executor = None
        self.session_histories = {}  # In-memory conversation storage
        self.use_fallback = False
        
        if self.llm:
            try:
                self._build_agent()
                logger.info(f"AI Agent initialized with provider: {Config.LLM_PROVIDER}")
            except Exception as e:
                logger.error(f"Failed to build agent: {e}. Using fallback mode.")
                self.use_fallback = True
        else:
            logger.warning("AI Agent LLM not initialized - using fallback mode (no API keys required)")
            self.use_fallback = True
        
        # Initialize fallback service
        if self.use_fallback:
            from services.fallback_ai_service import FallbackAIService
            self.fallback_service = FallbackAIService(db_manager)
    
    def _initialize_llm(self):
        """Initialize LLM based on configuration"""
        provider = getattr(Config, 'LLM_PROVIDER', 'anthropic').lower()
        
        logger.info(f"Initializing LLM with provider: {provider}")
        
        if provider == 'anthropic':
            if not Config.ANTHROPIC_API_KEY:
                logger.error("ANTHROPIC_API_KEY not configured")
                return None
            
            logger.info("Using Anthropic Claude 3.5 Sonnet")
            try:
                return ChatAnthropic(
                    model="claude-3-5-sonnet-20241022",
                    anthropic_api_key=Config.ANTHROPIC_API_KEY,
                    temperature=0.3,
                    max_tokens=2000
                )
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic: {e}")
                return None
                
        elif provider == 'openai':
            if not Config.OPENAI_API_KEY:
                logger.error("OPENAI_API_KEY not configured")
                return None
            
            logger.info("Using OpenAI GPT-4o-mini")
            try:
                return ChatOpenAI(
                    model="gpt-4o-mini",
                    openai_api_key=Config.OPENAI_API_KEY,
                    temperature=0.3,
                    max_tokens=2000
                )
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI: {e}")
                return None
        else:
            logger.error(f"LLM provider '{provider}' not supported")
            return None
    
    def _create_tools(self):
        """Create tools for the agent"""
        
        @tool
        def search_invoices(query: str, limit: int = 10) -> str:
            """
            Search for invoices by company name, category, or status.
            Use this tool when the user asks about specific invoices.
            
            Args:
                query: Search term (company name, category, or status)
                limit: Maximum number of results to return (default 10)
            
            Returns:
                JSON string of matching invoices
            """
            if not self.db_manager:
                return "Database not available"
            
            try:
                # Search across multiple fields
                search_filter = {
                    "$or": [
                        {"company": {"$regex": query, "$options": "i"}},
                        {"category": {"$regex": query, "$options": "i"}},
                        {"status": {"$regex": query, "$options": "i"}}
                    ]
                }
                
                invoices = list(
                    self.db_manager.db[Config.INVOICES_COLLECTION]
                    .find(search_filter, {"_id": 0})
                    .limit(limit)
                )
                
                if not invoices:
                    return f"No invoices found matching '{query}'"
                
                import json
                return json.dumps(invoices, default=str, indent=2)
            except Exception as e:
                logger.error(f"Invoice search error: {e}")
                return f"Error searching invoices: {str(e)}"
        
        @tool
        def get_invoice_by_id(invoice_id: str) -> str:
            """
            Get detailed information about a specific invoice by its ID.
            
            Args:
                invoice_id: The invoice ID to look up
            
            Returns:
                JSON string of the invoice details
            """
            if not self.db_manager:
                return "Database not available"
            
            try:
                invoice = self.db_manager.db[Config.INVOICES_COLLECTION].find_one(
                    {"invoice_id": invoice_id},
                    {"_id": 0}
                )
                
                if not invoice:
                    return f"Invoice '{invoice_id}' not found"
                
                import json
                return json.dumps(invoice, default=str, indent=2)
            except Exception as e:
                logger.error(f"Invoice lookup error: {e}")
                return f"Error looking up invoice: {str(e)}"
        
        @tool
        def get_spending_analytics(period: str = "all") -> str:
            """
            Get spending analytics and statistics.
            Use this when the user asks about spending, totals, or financial summaries.
            
            Args:
                period: Time period for analytics ('all', 'month', 'year')
            
            Returns:
                JSON string with analytics data
            """
            if not self.db_manager:
                return "Database not available"
            
            try:
                stats = self.db_manager.get_dashboard_summary()
                import json
                return json.dumps(stats, indent=2)
            except Exception as e:
                logger.error(f"Analytics error: {e}")
                return f"Error retrieving analytics: {str(e)}"
        
        @tool
        def search_vendors(query: str, limit: int = 10) -> str:
            """
            Search for vendors by name, category, or contact information.
            
            Args:
                query: Search term for vendor name or details
                limit: Maximum number of results
            
            Returns:
                JSON string of matching vendors
            """
            if not self.db_manager:
                return "Database not available"
            
            try:
                search_filter = {
                    "$or": [
                        {"name": {"$regex": query, "$options": "i"}},
                        {"category": {"$regex": query, "$options": "i"}},
                        {"contact_email": {"$regex": query, "$options": "i"}}
                    ]
                }
                
                vendors = list(
                    self.db_manager.db[Config.VENDORS_COLLECTION]
                    .find(search_filter, {"_id": 0})
                    .limit(limit)
                )
                
                if not vendors:
                    return f"No vendors found matching '{query}'"
                
                import json
                return json.dumps(vendors, default=str, indent=2)
            except Exception as e:
                logger.error(f"Vendor search error: {e}")
                return f"Error searching vendors: {str(e)}"
        
        @tool
        def detect_duplicate_invoices(company: str, total: float, tolerance: float = 0.01) -> str:
            """
            Check for potential duplicate invoices from the same company with similar amounts.
            
            Args:
                company: Company name to check
                total: Invoice total amount
                tolerance: Amount tolerance for matching (default 0.01 = 1%)
            
            Returns:
                JSON string with potential duplicates
            """
            if not self.db_manager:
                return "Database not available"
            
            try:
                min_amount = total * (1 - tolerance)
                max_amount = total * (1 + tolerance)
                
                duplicates = list(
                    self.db_manager.db[Config.INVOICES_COLLECTION].find({
                        "company": {"$regex": company, "$options": "i"},
                        "total": {"$gte": min_amount, "$lte": max_amount}
                    }, {"_id": 0}).limit(10)
                )
                
                if not duplicates:
                    return f"No potential duplicates found for {company} with amount ${total}"
                
                import json
                return json.dumps({
                    "potential_duplicates": len(duplicates),
                    "invoices": duplicates
                }, default=str, indent=2)
            except Exception as e:
                logger.error(f"Duplicate detection error: {e}")
                return f"Error detecting duplicates: {str(e)}"
        
        return [
            search_invoices,
            get_invoice_by_id,
            get_spending_analytics,
            search_vendors,
            detect_duplicate_invoices
        ]
    
    def _build_agent(self):
        """Build the LangChain agent with tools"""
        
        # Create system prompt
        system_prompt = """You are an intelligent AI assistant for an Invoice Automation SaaS platform.
You help users with invoice management, financial analysis, vendor management, and business operations.

Your capabilities:
- Search and retrieve invoice information
- Analyze spending patterns and financial data
- Find and manage vendor information
- Detect duplicate or anomalous invoices
- Provide financial insights and recommendations
- Guide users through the application

Guidelines:
1. Always use the provided tools to fetch real data - never make up information
2. Be concise and professional in your responses
3. Use markdown formatting for readability (bold, lists, tables)
4. When showing numbers, format currency as $X,XXX.XX
5. If you don't have enough information, ask clarifying questions
6. If a query is ambiguous, suggest specific ways the user can rephrase it
7. Prioritize accuracy over speed - always verify data with tools
8. When analyzing trends, base conclusions on actual data
9. Suggest actionable next steps when appropriate
10. If an operation might affect multiple invoices, confirm before proceeding

Current date: {current_date}
"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create agent with tools
        self.agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        
        # Create agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=False,
            max_iterations=5,
            max_execution_time=30,
            handle_parsing_errors=True,
            return_intermediate_steps=True
        )
    
    def _get_session_history(self, session_id: str) -> ChatMessageHistory:
        """Get or create conversation history for a session"""
        if session_id not in self.session_histories:
            self.session_histories[session_id] = ChatMessageHistory()
        return self.session_histories[session_id]
    
    def chat(
        self,
        message: str,
        session_id: str = "default",
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a chat message and return AI response
        
        Args:
            message: User's message
            session_id: Session ID for conversation history
            user_id: Optional user ID for logging
        
        Returns:
            Dictionary with response and metadata
        """
        # Use fallback service if LLM not available
        if self.use_fallback:
            logger.info("Using fallback AI service (no API keys)")
            return self.fallback_service.chat(message, session_id, user_id)
        
        if not self.agent_executor:
            logger.error("AI agent executor not initialized")
            return {
                "response": "AI agent is not configured. Please configure ANTHROPIC_API_KEY or OPENAI_API_KEY.",
                "error": "not_configured"
            }
        
        try:
            logger.info(f"Processing chat message: '{message[:50]}...' for session {session_id}")
            
            # Add conversation memory
            agent_with_history = RunnableWithMessageHistory(
                self.agent_executor,
                self._get_session_history,
                input_messages_key="input",
                history_messages_key="chat_history",
            )
            
            # Execute agent
            logger.debug(f"Invoking agent executor for session {session_id}")
            result = agent_with_history.invoke(
                {
                    "input": message,
                    "current_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                config={"configurable": {"session_id": session_id}}
            )
            
            logger.debug(f"Agent execution result: {result}")
            
            # Extract tools used
            tools_used = []
            if "intermediate_steps" in result:
                for step in result["intermediate_steps"]:
                    if len(step) > 0 and hasattr(step[0], 'tool'):
                        tools_used.append(step[0].tool)
            
            response = {
                "response": result.get("output", ""),
                "tools_used": list(set(tools_used)),
                "session_id": session_id
            }
            
            logger.info(f"AI agent response generated successfully for user {user_id}")
            return response
            
        except Exception as e:
            logger.error(f"AI agent error: {e}", exc_info=True)
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error details: {str(e)}")
            
            # Fall back to fallback service on error
            logger.warning("Falling back to fallback service due to error")
            if hasattr(self, 'fallback_service'):
                return self.fallback_service.chat(message, session_id, user_id)
            
            return {
                "response": "I encountered an error processing your request. Please try rephrasing your question or contact support if the issue persists.",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def clear_history(self, session_id: str):
        """Clear conversation history for a session"""
        if session_id in self.session_histories:
            del self.session_histories[session_id]
            logger.info(f"Cleared conversation history for session: {session_id}")


# Singleton instance (initialized in app.py)
ai_agent_service = None


def initialize_ai_agent(db_manager) -> AIAgentService:
    """Initialize the AI agent service"""
    global ai_agent_service
    ai_agent_service = AIAgentService(db_manager)
    return ai_agent_service


def get_ai_agent() -> Optional[AIAgentService]:
    """Get the AI agent service instance"""
    return ai_agent_service
