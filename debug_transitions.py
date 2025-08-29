#!/usr/bin/env python3
"""
Debug script to test Jira transitions.

This script helps debug the issue transition functionality
by showing available transitions for an issue.
"""

import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.infrastructure.jira_client import get_jira_client
from src.core.logging_config import get_logger

logger = get_logger(__name__)

def debug_issue_transitions(issue_key: str):
    """Debug transitions for a specific issue."""
    try:
        print(f"🔍 Debugging transitions for issue: {issue_key}")
        
        # Get Jira client
        jira_client = get_jira_client()
        
        # Test connection
        if not jira_client.test_connection():
            print("❌ Failed to connect to Jira")
            return
        
        print("✅ Connected to Jira successfully")
        
        # Get issue info
        try:
            issue = jira_client.get_issue(issue_key)
            print(f"📋 Issue: {issue.key} - {issue.fields.summary}")
            print(f"📊 Current Status: {issue.fields.status.name}")
            print(f"🏷️ Issue Type: {issue.fields.issuetype.name}")
        except Exception as e:
            print(f"❌ Error getting issue details: {e}")
            return
        
        # Get available transitions
        try:
            transitions = jira_client.get_transitions(issue_key)
            print(f"\n🔄 Available Transitions ({len(transitions)}):")
            
            for i, transition in enumerate(transitions, 1):
                print(f"  {i}. ID: {transition['id']} | Name: '{transition['name']}'")
            
            # Check for Done-like transitions
            done_keywords = [
                'done', 'concluído', 'concluido', 'finished', 'resolved', 
                'fechado', 'complete', 'completo', 'finalizado', 'pronto'
            ]
            
            done_transitions = []
            for transition in transitions:
                transition_name_lower = transition['name'].lower().strip()
                if any(keyword in transition_name_lower for keyword in done_keywords):
                    done_transitions.append(transition)
            
            if done_transitions:
                print(f"\n✅ Found {len(done_transitions)} 'Done-like' transition(s):")
                for transition in done_transitions:
                    print(f"  → ID: {transition['id']} | Name: '{transition['name']}'")
            else:
                print(f"\n⚠️ No 'Done-like' transitions found")
                print(f"Available transitions: {[t['name'] for t in transitions]}")
            
        except Exception as e:
            print(f"❌ Error getting transitions: {e}")
            return
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_transition(issue_key: str, transition_id: str):
    """Test a specific transition."""
    try:
        print(f"🔄 Testing transition {transition_id} on issue {issue_key}")
        
        jira_client = get_jira_client()
        
        # Get current status
        issue = jira_client.get_issue(issue_key)
        current_status = issue.fields.status.name
        print(f"📊 Current Status: {current_status}")
        
        # Attempt transition
        success = jira_client.transition_issue(issue_key, transition_id)
        
        if success:
            print(f"✅ Transition successful!")
            
            # Get new status
            updated_issue = jira_client.get_issue(issue_key)
            new_status = updated_issue.fields.status.name
            print(f"📊 New Status: {new_status}")
        else:
            print(f"❌ Transition failed")
            
    except Exception as e:
        print(f"❌ Error during transition: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_transitions.py <issue_key> [transition_id]")
        print("Example: python debug_transitions.py MS-173")
        print("Example: python debug_transitions.py MS-173 31")
        sys.exit(1)
    
    issue_key = sys.argv[1]
    
    if len(sys.argv) == 3:
        transition_id = sys.argv[2]
        test_transition(issue_key, transition_id)
    else:
        debug_issue_transitions(issue_key)