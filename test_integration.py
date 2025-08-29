#!/usr/bin/env python3
"""
Integration test script for the optimized Jira Agent.
Tests the actual functionality with mock data (no external dependencies).
"""

def test_function_signatures():
    """Test that tool functions have the correct signatures after optimization."""
    print("🧪 Testing Function Signatures...")
    
    try:
        # Mock the dependencies to test function signatures
        import sys
        import types
        
        # Create mock modules
        jira_mock = types.ModuleType('jira')
        pydantic_mock = types.ModuleType('pydantic')
        google_mock = types.ModuleType('google')
        google_adk_mock = types.ModuleType('google.adk')
        
        sys.modules['jira'] = jira_mock
        sys.modules['pydantic'] = pydantic_mock
        sys.modules['google'] = google_mock
        sys.modules['google.adk'] = google_adk_mock
        sys.modules['google.adk.agents'] = types.ModuleType('google.adk.agents')
        sys.modules['google.adk.tools'] = types.ModuleType('google.adk.tools')
        sys.modules['google.genai'] = types.ModuleType('google.genai')
        sys.modules['google.genai.types'] = types.ModuleType('google.genai.types')
        
        # Mock required classes and functions
        class MockAgent:
            def __init__(self, **kwargs):
                self.name = kwargs.get('name', 'test')
                self.tools = kwargs.get('tools', [])
                self.sub_agents = kwargs.get('sub_agents', [])
        
        class MockBaseModel:
            pass
            
        class MockContent:
            def __init__(self, **kwargs):
                pass
                
        class MockPart:
            def __init__(self, **kwargs):
                pass
                
        class MockLlmResponse:
            def __init__(self, **kwargs):
                pass
                
        class MockBaseTool:
            pass
            
        class MockToolContext:
            pass
        
        # Inject mocks
        google_adk_mock.agents = types.ModuleType('agents')
        google_adk_mock.agents.Agent = MockAgent
        google_adk_mock.tools = types.ModuleType('tools')
        google_adk_mock.tools.BaseTool = MockBaseTool
        google_adk_mock.tools.ToolContext = MockToolContext
        
        pydantic_mock.BaseModel = MockBaseModel
        pydantic_mock.Field = lambda **kwargs: None
        
        google_mock.genai = types.ModuleType('genai')
        google_mock.genai.types = types.ModuleType('types')
        google_mock.genai.types.Content = MockContent
        google_mock.genai.types.Part = MockPart
        google_mock.genai.types.LlmResponse = MockLlmResponse
        
        # Now test imports
        sys.path.insert(0, '.')
        
        from src.tools.issue.create_issue import create_issue
        from src.tools.issue.add_worklog import add_worklog
        from src.tools.project.search_projects import search_projects
        
        print("✅ Tool functions imported with mocks")
        
        # Test signatures
        import inspect
        
        # Test create_issue signature
        sig = inspect.signature(create_issue)
        params = list(sig.parameters.keys())
        
        print(f"  create_issue parameters: {params}")
        
        expected_params = [
            'project_identifier', 'summary', 'description', 'issue_type',
            'assignee_email', 'original_estimate', 'remaining_estimate', 
            'time_spent', 'work_start_date', 'work_description'
        ]
        
        # Check that all expected params are present and no tool_context
        has_all_params = all(param in params for param in expected_params)
        no_tool_context = 'tool_context' not in params
        
        print(f"  ✅ Has all expected params: {has_all_params}")
        print(f"  ✅ No tool_context param: {no_tool_context}")
        
        return has_all_params and no_tool_context
        
    except Exception as e:
        print(f"❌ Function signature test failed: {e}")
        return False

def test_agent_structure():
    """Test that agents can be instantiated with mocks."""
    print("\n🧪 Testing Agent Structure with Mocks...")
    
    try:
        # Agents should be importable now with mocks in place
        from src.agents.project_agent import project_agent
        from src.agents.issue_agent import issue_agent
        from src.agents.worklog_agent import worklog_agent
        
        print("✅ Sub-agents imported successfully")
        print(f"  - project_agent: {project_agent.name}")
        print(f"  - issue_agent: {issue_agent.name}")
        print(f"  - worklog_agent: {worklog_agent.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent structure test failed: {e}")
        return False

def test_callback_structure():
    """Test callback functions with mocks."""
    print("\n🧪 Testing Callback Structure...")
    
    try:
        from src.core.callbacks import (
            before_tool_callback,
            after_tool_callback,
            rate_limit_callback
        )
        
        print("✅ Callbacks imported successfully")
        
        # Test that callbacks have correct signatures
        import inspect
        
        # before_tool_callback should accept tool, args, tool_context
        sig = inspect.signature(before_tool_callback)
        params = list(sig.parameters.keys())
        expected = ['tool', 'args', 'tool_context']
        
        has_correct_sig = all(param in params for param in expected)
        print(f"  before_tool_callback signature: {has_correct_sig}")
        
        return has_correct_sig
        
    except Exception as e:
        print(f"❌ Callback structure test failed: {e}")
        return False

def main():
    """Run integration tests with mocks."""
    print("🚀 Integration Tests with Mocks")
    print("=" * 40)
    
    tests = [
        test_function_signatures,
        test_agent_structure,
        test_callback_structure
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 40)
    print(f"📊 Integration Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed!")
        print("\n🚀 Ready for production testing!")
        print("\n📋 Production Test Steps:")
        print("1. Install: pip install google-adk jira python-dotenv")
        print("2. Configure .env with Jira credentials") 
        print("3. Test with ADK: adk web")
        print("4. Or test programmatically with main.py")
    else:
        print("⚠️  Some integration issues found.")
    
    return passed == total

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)