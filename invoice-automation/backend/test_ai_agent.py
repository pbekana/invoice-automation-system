"""Test script for AI agent"""
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

print("=== Testing AI Agent ===\n")

# Check environment variables
from config import Config
print(f"LLM_PROVIDER: {Config.LLM_PROVIDER}")
print(f"ANTHROPIC_API_KEY: {'SET' if Config.ANTHROPIC_API_KEY else 'NOT SET'}")
print(f"OPENAI_API_KEY: {'SET' if Config.OPENAI_API_KEY else 'NOT SET'}")
print()

# Test database connection
print("Testing database connection...")
from db import db_manager
try:
    stats = db_manager.get_dashboard_summary()
    print(f"✅ Database connected. Total invoices: {stats.get('total_invoices', 0)}")
except Exception as e:
    print(f"❌ Database error: {e}")
print()

# Test AI agent initialization
print("Testing AI agent initialization...")
try:
    from services.ai_agent_service import AIAgentService
    
    agent = AIAgentService(db_manager)
    
    if agent.llm:
        print(f"✅ LLM initialized: {type(agent.llm).__name__}")
    else:
        print("❌ LLM not initialized")
    
    if agent.agent_executor:
        print(f"✅ Agent executor initialized with {len(agent.tools)} tools")
    else:
        print("❌ Agent executor not initialized")
    
    print()
    
    # Test a simple query
    if agent.agent_executor or agent.use_fallback:
        print("Testing chat with: 'What is my total spending?'")
        result = agent.chat("What is my total spending?", session_id="test_session")
        
        if "error" in result:
            print(f"❌ Error: {result.get('error')}")
            print(f"   Error type: {result.get('error_type')}")
        else:
            print(f"✅ Response: {result.get('response', '')[:200]}...")
            print(f"   Tools used: {result.get('tools_used', [])}")
    
except Exception as e:
    print(f"❌ Failed to test agent: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Test Complete ===")
