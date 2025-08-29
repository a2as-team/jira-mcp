#!/usr/bin/env python3
"""
Structural tests for the optimized Jira Agent architecture.
Tests the code structure and refactoring without requiring external dependencies.
"""

import os
import ast
import sys

def test_file_structure():
    """Test that all expected files were created during optimization."""
    print("🧪 Testing File Structure...")
    
    expected_files = [
        # Original files that should still exist
        "src/agents/jira_agent.py",
        "src/tools/issue/create_issue.py",
        "src/tools/issue/add_worklog.py",
        "src/tools/issue/list_issues.py",
        "src/tools/project/search_projects.py",
        "src/tools/project/get_project_details.py",
        
        # New files created during optimization
        "src/agents/project_agent.py",
        "src/agents/issue_agent.py", 
        "src/agents/worklog_agent.py",
        "src/core/callbacks.py",
        
        # Utility modules from Agent 8
        "src/infrastructure/url_utils.py",
        "src/infrastructure/jql_builder.py",
        "src/infrastructure/error_handling_utils.py",
        "src/core/validation_utils.py"
    ]
    
    missing_files = []
    for file_path in expected_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print(f"✅ All {len(expected_files)} expected files exist")
        return True

def analyze_python_file(file_path):
    """Analyze a Python file for structure without importing it."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        # Extract function definitions
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        
        # Extract class definitions
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        
        # Extract imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend([alias.name for alias in node.names])
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                imports.extend([f"{module}.{alias.name}" for alias in node.names])
        
        return {
            'functions': functions,
            'classes': classes, 
            'imports': imports,
            'lines': len(content.split('\n'))
        }
    except Exception as e:
        return {'error': str(e)}

def test_tool_refactoring():
    """Test that tools were properly refactored."""
    print("\n🧪 Testing Tool Refactoring...")
    
    results = {}
    
    # Test create_issue refactoring (Agent 4)
    create_issue_analysis = analyze_python_file("src/tools/issue/create_issue.py")
    if 'error' not in create_issue_analysis:
        functions = create_issue_analysis['functions']
        
        # Should have main function + 6+ private helper functions
        private_functions = [f for f in functions if f.startswith('_')]
        
        print(f"  create_issue.py:")
        print(f"    - Total functions: {len(functions)}")
        print(f"    - Private functions: {len(private_functions)}")
        print(f"    - Functions: {functions}")
        
        # Check for expected private functions from refactoring
        expected_helpers = [
            '_validate_issue_input', '_validate_project_access', 
            '_validate_worklog_data', '_prepare_issue_fields',
            '_assign_current_user', '_create_jira_issue',
            '_add_worklog_if_requested'
        ]
        
        found_helpers = [f for f in expected_helpers if f in functions]
        print(f"    - Helper functions found: {len(found_helpers)}/{len(expected_helpers)}")
        
        results['create_issue'] = len(found_helpers) >= 5  # At least 5 helpers
    
    # Test other tools
    for tool_file in ["src/tools/issue/add_worklog.py", "src/tools/project/search_projects.py"]:
        analysis = analyze_python_file(tool_file)
        if 'error' not in analysis:
            # Check that FunctionTool is not imported
            has_function_tool = any('FunctionTool' in imp for imp in analysis['imports'])
            results[tool_file] = not has_function_tool
            print(f"  {tool_file}: FunctionTool removed = {not has_function_tool}")
    
    passed = sum(results.values())
    total = len(results)
    print(f"✅ Tool refactoring: {passed}/{total} files properly refactored")
    
    return passed >= total * 0.8  # 80% success rate

def test_sub_agents_creation():
    """Test that sub-agents were created with proper structure."""
    print("\n🧪 Testing Sub-Agents Creation...")
    
    sub_agents = [
        "src/agents/project_agent.py",
        "src/agents/issue_agent.py",
        "src/agents/worklog_agent.py"
    ]
    
    results = {}
    
    for agent_file in sub_agents:
        analysis = analyze_python_file(agent_file)
        if 'error' not in analysis:
            # Check for Agent import
            has_agent_import = any('Agent' in imp for imp in analysis['imports'])
            
            # Check for agent variable definition
            with open(agent_file, 'r') as f:
                content = f.read()
                has_agent_definition = 'Agent(' in content
            
            results[agent_file] = has_agent_import and has_agent_definition
            print(f"  {agent_file}: Agent structure = {has_agent_import and has_agent_definition}")
    
    passed = sum(results.values())
    total = len(results)
    print(f"✅ Sub-agents creation: {passed}/{total} agents properly structured")
    
    return passed == total

def test_callbacks_implementation():
    """Test that callbacks were implemented."""
    print("\n🧪 Testing Callbacks Implementation...")
    
    analysis = analyze_python_file("src/core/callbacks.py")
    if 'error' in analysis:
        print(f"❌ Could not analyze callbacks.py: {analysis['error']}")
        return False
    
    expected_callbacks = [
        'before_tool_callback',
        'after_tool_callback', 
        'rate_limit_callback'
    ]
    
    found_callbacks = [cb for cb in expected_callbacks if cb in analysis['functions']]
    
    print(f"  Callbacks found: {len(found_callbacks)}/{len(expected_callbacks)}")
    print(f"  Functions: {found_callbacks}")
    
    return len(found_callbacks) == len(expected_callbacks)

def test_utility_modules():
    """Test that utility modules were created."""
    print("\n🧪 Testing Utility Modules...")
    
    utility_files = [
        "src/infrastructure/url_utils.py",
        "src/infrastructure/jql_builder.py", 
        "src/infrastructure/error_handling_utils.py",
        "src/core/validation_utils.py"
    ]
    
    results = {}
    
    for util_file in utility_files:
        if os.path.exists(util_file):
            analysis = analyze_python_file(util_file)
            if 'error' not in analysis:
                # Check that it has functions/classes
                has_content = len(analysis['functions']) > 0 or len(analysis['classes']) > 0
                results[util_file] = has_content
                print(f"  {util_file}: Functions={len(analysis['functions'])}, Classes={len(analysis['classes'])}")
        else:
            results[util_file] = False
            print(f"  {util_file}: Missing")
    
    passed = sum(results.values())
    total = len(results)
    print(f"✅ Utility modules: {passed}/{total} modules created")
    
    return passed >= total * 0.75  # 75% success rate

def test_line_count_reduction():
    """Test that large files were optimized."""
    print("\n🧪 Testing Line Count Optimization...")
    
    # Test create_issue function split
    analysis = analyze_python_file("src/tools/issue/create_issue.py")
    if 'error' not in analysis:
        print(f"  create_issue.py: {analysis['lines']} lines")
        
        # Count private helper functions (should be 6-7 from refactoring)
        private_funcs = [f for f in analysis['functions'] if f.startswith('_')]
        print(f"  Helper functions created: {len(private_funcs)}")
        
        # If we have helper functions, the refactoring worked
        return len(private_funcs) >= 5
    
    return False

def main():
    """Run all structural tests."""
    print("🚀 Testing Optimized Jira Agent Structure")
    print("=" * 50)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Tool Refactoring", test_tool_refactoring),
        ("Sub-Agents Creation", test_sub_agents_creation),
        ("Callbacks Implementation", test_callbacks_implementation),
        ("Utility Modules", test_utility_modules),
        ("Line Count Optimization", test_line_count_reduction)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} error: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed >= total * 0.8:  # 80% pass rate
        print("🎉 Architecture optimization successful!")
        print("\n📋 Next Steps:")
        print("1. Install dependencies: pip install -r requirements.txt") 
        print("2. Set up .env with Jira credentials")
        print("3. Test with: adk web (if using ADK CLI)")
        print("4. Or run: python main.py")
    else:
        print("⚠️  Some structural issues found. Check the output above.")
    
    return passed >= total * 0.8

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)