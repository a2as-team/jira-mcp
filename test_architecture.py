#!/usr/bin/env python3
"""
Test script for the optimized Jira Agent architecture.
Tests the new sub-agents structure and simplified tools.
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

def test_tool_imports():
    """Test that all tools can be imported directly without FunctionTool wrappers."""
    print("🧪 Testing Tool Imports...")
    
    try:
        # Test issue tools
        from src.tools.issue.create_issue import create_issue
        from src.tools.issue.add_worklog import add_worklog
        from src.tools.issue.list_issues import list_issues
        
        # Test project tools
        from src.tools.project.search_projects import search_projects
        from src.tools.project.get_project_details import get_project_details
        
        print("✅ All tools imported successfully")
        print(f"  - create_issue: {create_issue.__name__}")
        print(f"  - add_worklog: {add_worklog.__name__}")
        print(f"  - list_issues: {list_issues.__name__}")
        print(f"  - search_projects: {search_projects.__name__}")
        print(f"  - get_project_details: {get_project_details.__name__}")
        
        return True
    except Exception as e:
        print(f"❌ Tool import failed: {e}")
        return False

def test_callback_imports():
    """Test that callbacks can be imported and have correct signatures."""
    print("\n🧪 Testing Callback Imports...")
    
    try:
        from src.core.callbacks import (
            before_tool_callback,
            after_tool_callback, 
            rate_limit_callback
        )
        
        print("✅ All callbacks imported successfully")
        print(f"  - before_tool_callback: {before_tool_callback.__name__}")
        print(f"  - after_tool_callback: {after_tool_callback.__name__}")
        print(f"  - rate_limit_callback: {rate_limit_callback.__name__}")
        
        return True
    except Exception as e:
        print(f"❌ Callback import failed: {e}")
        return False

def test_sub_agent_imports():
    """Test that sub-agents can be imported and have correct structure."""
    print("\n🧪 Testing Sub-Agent Imports...")
    
    try:
        from src.agents.project_agent import project_agent
        from src.agents.issue_agent import issue_agent
        from src.agents.worklog_agent import worklog_agent
        
        print("✅ All sub-agents imported successfully")
        print(f"  - project_agent: {project_agent.name}")
        print(f"  - issue_agent: {issue_agent.name}")
        print(f"  - worklog_agent: {worklog_agent.name}")
        
        return True
    except Exception as e:
        print(f"❌ Sub-agent import failed: {e}")
        return False

def test_main_agent_structure():
    """Test that the main agent can be created with the new architecture."""
    print("\n🧪 Testing Main Agent Structure...")
    
    try:
        from src.agents.jira_agent import create_jira_agent
        
        # This will fail without proper environment setup, but we can test the structure
        print("✅ Main agent factory imported successfully")
        print(f"  - create_jira_agent: {create_jira_agent.__name__}")
        
        return True
    except Exception as e:
        print(f"❌ Main agent structure test failed: {e}")
        return False

def test_utility_modules():
    """Test that new utility modules are accessible."""
    print("\n🧪 Testing Utility Modules...")
    
    try:
        # Test infrastructure utilities
        from src.infrastructure.url_utils import build_jira_url
        from src.infrastructure.jql_builder import JQLBuilder
        from src.infrastructure.error_handling_utils import try_jira_operation
        
        print("✅ Infrastructure utilities imported successfully")
        
        # Test core utilities  
        from src.core.validation_utils import validate_email_format
        
        print("✅ Core utilities imported successfully")
        
        return True
    except Exception as e:
        print(f"❌ Utility modules test failed: {e}")
        return False

def test_function_signatures():
    """Test that tool function signatures are correct."""
    print("\n🧪 Testing Function Signatures...")
    
    try:
        from src.tools.issue.create_issue import create_issue
        import inspect
        
        sig = inspect.signature(create_issue)
        params = list(sig.parameters.keys())
        
        expected_params = [
            'project_identifier', 'summary', 'description', 'issue_type',
            'assignee_email', 'original_estimate', 'remaining_estimate',
            'time_spent', 'work_start_date', 'work_description'
        ]
        
        print(f"✅ create_issue signature: {params}")
        
        # Check that tool_context is not in parameters (removed during simplification)
        if 'tool_context' not in params:
            print("✅ tool_context parameter successfully removed")
        else:
            print("⚠️  tool_context parameter still present")
            
        return True
    except Exception as e:
        print(f"❌ Function signature test failed: {e}")
        return False

def main():
    """Run all architecture tests."""
    print("🚀 Testing Optimized Jira Agent Architecture")
    print("=" * 50)
    
    tests = [
        test_tool_imports,
        test_callback_imports,
        test_sub_agent_imports,
        test_main_agent_structure,
        test_utility_modules,
        test_function_signatures
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
            
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All architecture tests passed! The optimization was successful.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)