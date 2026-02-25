#!/usr/bin/env python3
"""
GitHub Issues Synchronization for OpenClaw Workspace
Synchronizes Task Registry tasks with GitHub Issues for better visibility and tracking.

Usage:
    python3 sync_issues.py sync      # Full synchronization
    python3 sync_issues.py check     # Check sync status
    python3 sync_issues.py cleanup   # Close issues for removed tasks
"""

import json
import os
import sys
import subprocess
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Configuration
REPO = "jaccchina-ai/openclaw-workspace"
TASK_REGISTRY_PATH = "task_registry.json"
ISSUE_LABELS = ["task", "automation", "financial-strategies"]
ISSUE_PREFIX = "[Task]"

def run_gh_command(args: List[str], capture_output: bool = True) -> Tuple[int, str, str]:
    """Run a gh CLI command and return results."""
    try:
        cmd = ["gh"] + args
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            timeout=30
        )
        if capture_output:
            return result.returncode, result.stdout, result.stderr
        else:
            return result.returncode, "", ""
    except FileNotFoundError:
        print("❌ Error: GitHub CLI (gh) not found. Please install gh CLI.")
        return 1, "", "gh not found"
    except subprocess.TimeoutExpired:
        print("❌ Error: GitHub CLI command timed out.")
        return 1, "", "timeout"

def get_existing_issues() -> List[Dict[str, Any]]:
    """Get all existing issues from the repository."""
    print("📋 Fetching existing GitHub issues...")
    
    returncode, stdout, stderr = run_gh_command([
        "issue", "list",
        "--repo", REPO,
        "--limit", "100",
        "--json", "number,title,state,labels,body"
    ])
    
    if returncode != 0:
        print(f"❌ Failed to fetch issues: {stderr}")
        return []
    
    try:
        issues = json.loads(stdout)
        print(f"✅ Found {len(issues)} existing issues")
        return issues
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse issues JSON: {e}")
        return []

def find_task_issue(issues: List[Dict[str, Any]], task_id: str) -> Optional[Dict[str, Any]]:
    """Find an issue for a specific task ID."""
    for issue in issues:
        # Check if issue title contains task ID
        if f"{task_id}:" in issue.get("title", "") or f"[{task_id}]" in issue.get("title", ""):
            return issue
        
        # Check if issue body contains task ID
        body = issue.get("body", "")
        if f"**Task ID:** {task_id}" in body or f"Task ID: {task_id}" in body:
            return issue
        
        # Check labels
        labels = [label.get("name", "") for label in issue.get("labels", [])]
        if f"task:{task_id}" in labels or task_id in labels:
            return issue
    
    return None

def create_issue_body(task: Dict[str, Any]) -> str:
    """Create issue body from task data."""
    body_parts = []
    
    # Task metadata
    body_parts.append(f"**Task ID:** {task['id']}")
    body_parts.append(f"**Version:** {task.get('version', 'N/A')}")
    body_parts.append(f"**Status:** {task.get('status', 'unknown')}")
    body_parts.append(f"**Location:** {task.get('location', 'N/A')}")
    body_parts.append(f"**Created:** {task.get('created_date', 'N/A')}")
    body_parts.append(f"**Last Updated:** {task.get('last_updated', 'N/A')}")
    
    if task.get('schedule'):
        body_parts.append(f"**Schedule:** {task['schedule']}")
    
    # Description
    body_parts.append("\n## Description")
    body_parts.append(task.get('description', 'No description provided.'))
    
    # Dependencies
    if task.get('dependencies'):
        body_parts.append("\n## Dependencies")
        body_parts.append(", ".join(task['dependencies']))
    
    # Configuration
    if task.get('configuration_file'):
        body_parts.append(f"\n## Configuration File")
        body_parts.append(f"`{task['configuration_file']}`")
    
    # Entry point
    if task.get('entry_point'):
        body_parts.append(f"\n## Entry Point")
        body_parts.append(f"`{task['entry_point']}`")
    
    # Documentation
    if task.get('documentation'):
        body_parts.append(f"\n## Documentation")
        body_parts.append(f"`{task['documentation']}`")
    
    # Tags
    if task.get('tags'):
        body_parts.append(f"\n## Tags")
        body_parts.append(", ".join(task['tags']))
    
    # Automatically managed notice
    body_parts.append("\n---")
    body_parts.append("*This issue is automatically managed by the OpenClaw Task Registry.*")
    body_parts.append("*Do not edit this issue manually - changes will be overwritten.*")
    
    return "\n".join(body_parts)

def create_issue(task: Dict[str, Any]) -> bool:
    """Create a new GitHub issue for a task."""
    print(f"📝 Creating issue for task {task['id']}...")
    
    title = f"{ISSUE_PREFIX} {task['id']}: {task['name']}"
    body = create_issue_body(task)
    
    # Build labels
    labels = ISSUE_LABELS.copy()
    labels.append(f"task:{task['id']}")
    labels.append(f"status:{task.get('status', 'active')}")
    
    if task.get('tags'):
        for tag in task['tags']:
            labels.append(tag.lower().replace(" ", "-"))
    
    # Create issue using gh CLI
    cmd = [
        "issue", "create",
        "--repo", REPO,
        "--title", title,
        "--body", body,
        "--label", ",".join(labels)
    ]
    
    returncode, stdout, stderr = run_gh_command(cmd)
    
    if returncode == 0:
        print(f"✅ Created issue for task {task['id']}")
        return True
    else:
        print(f"❌ Failed to create issue for task {task['id']}: {stderr}")
        return False

def update_issue(issue_number: int, task: Dict[str, Any]) -> bool:
    """Update an existing GitHub issue."""
    print(f"📝 Updating issue #{issue_number} for task {task['id']}...")
    
    title = f"{ISSUE_PREFIX} {task['id']}: {task['name']}"
    body = create_issue_body(task)
    
    # Update issue using gh CLI (only title and body, labels are set at creation)
    cmd = [
        "issue", "edit",
        str(issue_number),
        "--repo", REPO,
        "--title", title,
        "--body", body
    ]
    
    returncode, stdout, stderr = run_gh_command(cmd)
    
    if returncode == 0:
        print(f"✅ Updated issue #{issue_number} for task {task['id']}")
        
        # Note: Issue state updates are not supported via gh issue edit
        # State can be managed manually or via gh issue close/reopen commands
        # For now, we skip automatic state updates to avoid errors
        return True
    else:
        print(f"❌ Failed to update issue #{issue_number}: {stderr}")
        return False

def close_issue(issue_number: int, reason: str = "Task removed from registry") -> bool:
    """Close a GitHub issue."""
    print(f"🗑️  Closing issue #{issue_number}...")
    
    cmd = [
        "issue", "close",
        str(issue_number),
        "--repo", REPO,
        "--comment", f"Closed: {reason}"
    ]
    
    returncode, stdout, stderr = run_gh_command(cmd, capture_output=False)
    
    if returncode == 0:
        print(f"✅ Closed issue #{issue_number}")
        return True
    else:
        print(f"❌ Failed to close issue #{issue_number}")
        return False

def load_task_registry() -> Optional[Dict[str, Any]]:
    """Load the task registry file."""
    try:
        with open(TASK_REGISTRY_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Task registry file not found: {TASK_REGISTRY_PATH}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse task registry JSON: {e}")
        return None

def sync_issues() -> bool:
    """Main synchronization function."""
    print("🔄 Starting GitHub Issues synchronization...")
    print(f"📦 Repository: {REPO}")
    
    # Load task registry
    registry = load_task_registry()
    if not registry:
        return False
    
    tasks = registry.get('tasks', [])
    print(f"📊 Found {len(tasks)} tasks in registry")
    
    # Get existing issues
    existing_issues = get_existing_issues()
    
    # Track processed task IDs
    processed_tasks = set()
    success = True
    
    # Sync each task
    for task in tasks:
        task_id = task['id']
        processed_tasks.add(task_id)
        
        # Find existing issue for this task
        existing_issue = find_task_issue(existing_issues, task_id)
        
        if existing_issue:
            # Update existing issue
            if not update_issue(existing_issue['number'], task):
                success = False
        else:
            # Create new issue
            if not create_issue(task):
                success = False
    
    # Close issues for tasks no longer in registry
    for issue in existing_issues:
        issue_number = issue['number']
        issue_title = issue.get('title', '')
        
        # Check if this is a task issue
        if ISSUE_PREFIX in issue_title:
            # Extract task ID from issue
            task_id_match = re.search(r'\[Task\]\s*(\w+):', issue_title)
            if task_id_match:
                task_id = task_id_match.group(1)
                if task_id not in processed_tasks:
                    if not close_issue(issue_number, f"Task {task_id} removed from registry"):
                        success = False
    
    if success:
        print("✅ GitHub Issues synchronization completed successfully")
    else:
        print("⚠️  GitHub Issues synchronization completed with warnings")
    
    return success

def check_sync_status() -> bool:
    """Check synchronization status without making changes."""
    print("🔍 Checking GitHub Issues synchronization status...")
    
    # Load task registry
    registry = load_task_registry()
    if not registry:
        return False
    
    tasks = registry.get('tasks', [])
    print(f"📊 Found {len(tasks)} tasks in registry")
    
    # Get existing issues
    existing_issues = get_existing_issues()
    
    # Check each task
    out_of_sync = []
    
    for task in tasks:
        task_id = task['id']
        existing_issue = find_task_issue(existing_issues, task_id)
        
        if not existing_issue:
            out_of_sync.append(f"❌ Task {task_id}: No GitHub issue found")
        else:
            issue_state = existing_issue.get('state', 'unknown')
            task_status = task.get('status', 'unknown')
            
            # Check if state matches
            if task_status == 'active' and issue_state != 'OPEN':
                out_of_sync.append(f"⚠️  Task {task_id}: Status 'active' but issue state is '{issue_state}'")
            elif task_status != 'active' and issue_state != 'CLOSED':
                out_of_sync.append(f"⚠️  Task {task_id}: Status '{task_status}' but issue state is '{issue_state}'")
    
    # Check for orphaned issues
    for issue in existing_issues:
        issue_title = issue.get('title', '')
        if ISSUE_PREFIX in issue_title:
            task_id_match = re.search(r'\[Task\]\s*(\w+):', issue_title)
            if task_id_match:
                task_id = task_id_match.group(1)
                # Check if task exists in registry
                task_exists = any(task['id'] == task_id for task in tasks)
                if not task_exists:
                    out_of_sync.append(f"🗑️  Orphaned issue #{issue['number']}: Task {task_id} not in registry")
    
    # Print results
    if out_of_sync:
        print("\n📋 Synchronization Status:")
        for status in out_of_sync:
            print(f"  {status}")
        print(f"\n📊 Summary: {len(out_of_sync)} item(s) need attention")
        return False
    else:
        print("✅ All tasks are synchronized with GitHub Issues")
        return True

def cleanup_issues() -> bool:
    """Close all task issues (for cleanup or reset)."""
    print("🧹 Cleaning up GitHub Issues...")
    
    # Get existing issues
    existing_issues = get_existing_issues()
    
    # Close all task issues
    closed_count = 0
    for issue in existing_issues:
        issue_title = issue.get('title', '')
        if ISSUE_PREFIX in issue_title:
            if close_issue(issue['number'], "Cleanup: All task issues closed"):
                closed_count += 1
    
    print(f"✅ Closed {closed_count} task issues")
    return True

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nCommands:")
        print("  sync      - Synchronize tasks with GitHub Issues")
        print("  check     - Check synchronization status")
        print("  cleanup   - Close all task issues (use with caution)")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "sync":
        success = sync_issues()
        sys.exit(0 if success else 1)
    elif command == "check":
        success = check_sync_status()
        sys.exit(0 if success else 1)
    elif command == "cleanup":
        confirm = input("⚠️  This will close ALL task issues. Type 'yes' to confirm: ")
        if confirm.lower() == 'yes':
            success = cleanup_issues()
            sys.exit(0 if success else 1)
        else:
            print("❌ Cleanup cancelled")
            sys.exit(1)
    else:
        print(f"❌ Unknown command: {command}")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()