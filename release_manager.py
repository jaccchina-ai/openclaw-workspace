#!/usr/bin/env python3
"""
Release Manager for OpenClaw Workspace
Manages Git tags and GitHub Releases based on Task Registry versions.

Usage:
    python3 release_manager.py check      # Check for version changes
    python3 release_manager.py tag        # Create tags for new versions
    python3 release_manager.py release    # Create GitHub Releases
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

def run_command(cmd: List[str], capture_output: bool = True) -> Tuple[int, str, str]:
    """Run a shell command and return results."""
    try:
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
    except FileNotFoundError as e:
        return 1, "", str(e)
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"

def get_git_tags() -> List[str]:
    """Get all git tags."""
    returncode, stdout, stderr = run_command(["git", "tag", "--list"])
    if returncode != 0:
        print(f"❌ Failed to get git tags: {stderr}")
        return []
    return [tag.strip() for tag in stdout.split("\n") if tag.strip()]

def get_github_releases() -> List[Dict[str, Any]]:
    """Get existing GitHub releases."""
    returncode, stdout, stderr = run_command(["gh", "release", "list", "--repo", REPO, "--limit", "50", "--json", "tagName,createdAt,name"])
    if returncode != 0:
        print(f"❌ Failed to get GitHub releases: {stderr}")
        return []
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return []

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

def parse_version(version_str: str) -> Tuple[int, int, int]:
    """Parse semantic version string into tuple."""
    match = re.match(r'v?(\d+)\.(\d+)\.(\d+)', version_str)
    if match:
        return tuple(map(int, match.groups()))
    return (0, 0, 0)

def get_task_tags(task_id: str) -> List[str]:
    """Get existing tags for a specific task."""
    all_tags = get_git_tags()
    task_tags = []
    for tag in all_tags:
        if tag.startswith(f"{task_id}/v") or tag.startswith(f"{task_id}-v"):
            task_tags.append(tag)
    return sorted(task_tags, key=parse_version, reverse=True)

def get_latest_task_tag(task_id: str) -> Optional[str]:
    """Get the latest tag for a task."""
    task_tags = get_task_tags(task_id)
    return task_tags[0] if task_tags else None

def create_git_tag(tag_name: str, message: str = "") -> bool:
    """Create a git tag."""
    print(f"🏷️  Creating git tag: {tag_name}")
    
    if not message:
        message = f"Release {tag_name}"
    
    returncode, stdout, stderr = run_command(["git", "tag", "-a", tag_name, "-m", message])
    
    if returncode == 0:
        print(f"✅ Created git tag: {tag_name}")
        return True
    else:
        print(f"❌ Failed to create git tag {tag_name}: {stderr}")
        return False

def push_git_tag(tag_name: str) -> bool:
    """Push a git tag to remote."""
    print(f"📤 Pushing tag to remote: {tag_name}")
    
    returncode, stdout, stderr = run_command(["git", "push", "origin", tag_name])
    
    if returncode == 0:
        print(f"✅ Pushed tag {tag_name} to remote")
        return True
    else:
        print(f"❌ Failed to push tag {tag_name}: {stderr}")
        return False

def create_github_release(tag_name: str, task: Dict[str, Any]) -> bool:
    """Create a GitHub release."""
    print(f"🚀 Creating GitHub release: {tag_name}")
    
    # Prepare release notes
    release_notes = generate_release_notes(tag_name, task)
    
    # Write release notes to temp file
    notes_file = f"/tmp/release_notes_{tag_name}.md"
    with open(notes_file, 'w', encoding='utf-8') as f:
        f.write(release_notes)
    
    # Create release using gh CLI
    cmd = [
        "gh", "release", "create",
        tag_name,
        "--repo", REPO,
        "--title", f"{task['id']} {task.get('version', 'unknown')}",
        "--notes-file", notes_file,
        "--generate-notes"  # Let GitHub generate additional notes
    ]
    
    returncode, stdout, stderr = run_command(cmd, capture_output=False)
    
    if returncode == 0:
        print(f"✅ Created GitHub release: {tag_name}")
        return True
    else:
        print(f"❌ Failed to create GitHub release {tag_name}: {stderr}")
        return False

def generate_release_notes(tag_name: str, task: Dict[str, Any]) -> str:
    """Generate release notes for a task."""
    notes = []
    
    notes.append(f"# {task['id']} {task.get('version', 'unknown')}")
    notes.append("")
    notes.append(f"**Task:** {task.get('name', 'Unnamed task')}")
    notes.append(f"**Release:** {tag_name}")
    notes.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    notes.append("")
    
    # Description
    if task.get('description'):
        notes.append("## Description")
        notes.append(task['description'])
        notes.append("")
    
    # Changes based on version
    if task.get('snapshots'):
        notes.append("## Recent Changes")
        # Get the latest snapshot
        latest_snapshot = max(task['snapshots'], key=lambda x: x.get('created_at', ''))
        notes.append(f"Latest snapshot: {latest_snapshot.get('created_at', 'unknown')}")
        notes.append("")
    
    # Configuration
    if task.get('configuration_file'):
        notes.append("## Configuration")
        notes.append(f"Main configuration file: `{task['configuration_file']}`")
        notes.append("")
    
    # Dependencies
    if task.get('dependencies'):
        notes.append("## Dependencies")
        for dep in task['dependencies']:
            notes.append(f"- {dep}")
        notes.append("")
    
    notes.append("---")
    notes.append("*This release was automatically generated by the OpenClaw Release Manager.*")
    
    return "\n".join(notes)

def check_versions() -> bool:
    """Check for version changes that need tagging."""
    print("🔍 Checking for version changes...")
    
    registry = load_task_registry()
    if not registry:
        return False
    
    tasks = registry.get('tasks', [])
    print(f"📊 Found {len(tasks)} tasks in registry")
    
    needs_tagging = []
    
    for task in tasks:
        task_id = task['id']
        current_version = task.get('version', '0.0.0')
        
        # Get latest tag for this task
        latest_tag = get_latest_task_tag(task_id)
        
        if latest_tag:
            # Extract version from tag
            tag_version_match = re.search(r'v(\d+\.\d+\.\d+)', latest_tag)
            if tag_version_match:
                tag_version = tag_version_match.group(1)
                
                if tag_version != current_version:
                    needs_tagging.append({
                        'task_id': task_id,
                        'current_version': current_version,
                        'tagged_version': tag_version,
                        'latest_tag': latest_tag
                    })
                    print(f"🔄 {task_id}: Version changed from {tag_version} to {current_version}")
                else:
                    print(f"✅ {task_id}: Version {current_version} is already tagged")
            else:
                print(f"⚠️  {task_id}: Could not parse version from tag {latest_tag}")
        else:
            # No existing tag
            needs_tagging.append({
                'task_id': task_id,
                'current_version': current_version,
                'tagged_version': None,
                'latest_tag': None
            })
            print(f"🆕 {task_id}: No existing tag, current version is {current_version}")
    
    # Print summary
    if needs_tagging:
        print(f"\n📋 Summary: {len(needs_tagging)} task(s) need tagging:")
        for item in needs_tagging:
            if item['tagged_version']:
                print(f"  • {item['task_id']}: {item['tagged_version']} → {item['current_version']}")
            else:
                print(f"  • {item['task_id']}: No tag → {item['current_version']}")
        return True
    else:
        print("✅ All tasks are up to date with tags")
        return False

def create_tags() -> bool:
    """Create git tags for tasks with new versions."""
    print("🏷️  Creating tags for new versions...")
    
    registry = load_task_registry()
    if not registry:
        return False
    
    tasks = registry.get('tasks', [])
    success = True
    
    for task in tasks:
        task_id = task['id']
        current_version = task.get('version', '0.0.0')
        
        # Check if tag already exists for this version
        expected_tag = f"{task_id}/v{current_version}"
        existing_tags = get_task_tags(task_id)
        
        tag_exists = any(tag == expected_tag or tag.endswith(f"/v{current_version}") for tag in existing_tags)
        
        if tag_exists:
            print(f"✅ {task_id} v{current_version} is already tagged")
            continue
        
        # Create new tag
        tag_name = f"{task_id}/v{current_version}"
        message = f"{task_id} version {current_version}: {task.get('name', '')}"
        
        if create_git_tag(tag_name, message):
            if push_git_tag(tag_name):
                print(f"✅ Successfully created and pushed tag: {tag_name}")
            else:
                print(f"⚠️  Created tag {tag_name} but failed to push")
                success = False
        else:
            print(f"❌ Failed to create tag: {tag_name}")
            success = False
    
    return success

def create_releases() -> bool:
    """Create GitHub releases for untagged versions."""
    print("🚀 Creating GitHub releases...")
    
    registry = load_task_registry()
    if not registry:
        return False
    
    tasks = registry.get('tasks', [])
    existing_releases = get_github_releases()
    existing_release_tags = {release['tagName'] for release in existing_releases}
    
    success = True
    
    for task in tasks:
        task_id = task['id']
        current_version = task.get('version', '0.0.0')
        
        # Check if release already exists
        expected_tag = f"{task_id}/v{current_version}"
        
        if expected_tag in existing_release_tags:
            print(f"✅ Release already exists for {expected_tag}")
            continue
        
        # Check if tag exists
        task_tags = get_task_tags(task_id)
        has_tag = any(tag == expected_tag for tag in task_tags)
        
        if not has_tag:
            print(f"⚠️  No git tag found for {expected_tag}, creating tag first...")
            if create_git_tag(expected_tag):
                push_git_tag(expected_tag)
            else:
                print(f"❌ Skipping release for {expected_tag} (no tag)")
                success = False
                continue
        
        # Create release
        if create_github_release(expected_tag, task):
            print(f"✅ Created release for {expected_tag}")
        else:
            print(f"❌ Failed to create release for {expected_tag}")
            success = False
    
    return success

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nCommands:")
        print("  check     - Check for version changes needing tags")
        print("  tag       - Create git tags for new versions")
        print("  release   - Create GitHub releases for new tags")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    # Ensure we're in the git repo
    if not os.path.exists(".git"):
        print("❌ Not in a git repository")
        sys.exit(1)
    
    if command == "check":
        needs_update = check_versions()
        sys.exit(0 if not needs_update else 1)
    elif command == "tag":
        success = create_tags()
        sys.exit(0 if success else 1)
    elif command == "release":
        success = create_releases()
        sys.exit(0 if success else 1)
    else:
        print(f"❌ Unknown command: {command}")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()