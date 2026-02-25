#!/usr/bin/env python3
"""
GitHub Wiki Synchronization for OpenClaw Workspace
Synchronizes documentation files to GitHub Wiki.

Usage:
    python3 wiki_sync.py sync      # Sync documentation to wiki
    python3 wiki_sync.py check     # Check sync status
    python3 wiki_sync.py init      # Initialize wiki repository
"""

import os
import sys
import json
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configuration
REPO = "jaccchina-ai/openclaw-workspace"
WIKI_REPO_URL = f"https://github.com/{REPO}.wiki.git"
WORKSPACE_ROOT = os.path.dirname(os.path.abspath(__file__))
WIKI_CLONE_DIR = os.path.join(WORKSPACE_ROOT, ".wiki-temp")

# Mapping of workspace files to wiki pages
WIKI_MAPPING = [
    {
        "source": "AGENTS.md",
        "wiki_page": "Workspace-Guide.md",
        "title": "Workspace Guide",
        "category": "Guides"
    },
    {
        "source": "SOUL.md",
        "wiki_page": "Agent-Personality.md",
        "title": "Agent Personality",
        "category": "Guides"
    },
    {
        "source": "USER.md",
        "wiki_page": "User-Profile.md",
        "title": "User Profile",
        "category": "Guides"
    },
    {
        "source": "MEMORY.md",
        "wiki_page": "Project-History.md",
        "title": "Project History",
        "category": "History"
    },
    {
        "source": "task_registry.json",
        "wiki_page": "Task-Registry.md",
        "title": "Task Registry",
        "category": "Tasks",
        "transform": "json_to_md"
    },
    {
        "source": "tasks/T01/README.md",
        "wiki_page": "T01-Limit-Up-Strategy.md",
        "title": "T01: Limit Up Strategy",
        "category": "Tasks/T01"
    },
    {
        "source": "tasks/T01/USER_GUIDE.md",
        "wiki_page": "T01-User-Guide.md",
        "title": "T01 User Guide",
        "category": "Tasks/T01"
    },
    {
        "source": "skills/a-share-short-decision/README.md",
        "wiki_page": "T99-Review-Task.md",
        "title": "T99: Review Task",
        "category": "Tasks/T99"
    },
    {
        "source": "skills/macro-monitor/TASK.md",
        "wiki_page": "T100-Macro-Monitor.md",
        "title": "T100: Macro Monitor",
        "category": "Tasks/T100"
    }
]

def run_command(cmd: List[str], cwd: Optional[str] = None, capture_output: bool = True) -> Tuple[int, str, str]:
    """Run a shell command and return results."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=capture_output,
            text=True,
            timeout=60
        )
        if capture_output:
            return result.returncode, result.stdout, result.stderr
        else:
            return result.returncode, "", ""
    except FileNotFoundError as e:
        return 1, "", str(e)
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"

def check_wiki_exists() -> bool:
    """Check if the wiki repository exists."""
    print("🔍 Checking if wiki exists...")
    
    # First check if wiki is enabled via GitHub API
    returncode, stdout, stderr = run_command([
        "gh", "api",
        f"repos/{REPO}"
    ])
    
    if returncode != 0:
        print(f"❌ Failed to check repository info: {stderr[:100]}")
        return False
    
    try:
        import json
        repo_info = json.loads(stdout)
        has_wiki = repo_info.get('has_wiki', False)
        
        if not has_wiki:
            print("❌ Wiki is not enabled for this repository")
            return False
        
        print("✅ Wiki is enabled for repository")
        
        # Try to access the wiki repository to see if it's initialized
        # Use token authentication for git operations
        token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
        if token:
            # Use token-authenticated URL
            auth_url = f"https://{token}@github.com/{REPO}.wiki.git"
            returncode, stdout, stderr = run_command([
                "git", "ls-remote",
                auth_url,
                "HEAD"
            ], capture_output=False)
        else:
            # Try without authentication (may work for public repos)
            returncode, stdout, stderr = run_command([
                "git", "ls-remote",
                WIKI_REPO_URL,
                "HEAD"
            ], capture_output=False)
        
        if returncode == 0:
            print("✅ Wiki repository is initialized and accessible")
            return True
        else:
            print("ℹ️  Wiki is enabled but repository may not be initialized yet")
            print("   This is normal - the wiki will be initialized on first sync")
            return True  # Return True because wiki is enabled, just not initialized yet
            
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse repository info: {e}")
        return False

def clone_wiki() -> bool:
    """Clone or initialize the wiki repository."""
    print("📥 Setting up wiki repository...")
    
    # Clean up existing clone
    if os.path.exists(WIKI_CLONE_DIR):
        shutil.rmtree(WIKI_CLONE_DIR)
    
    os.makedirs(WIKI_CLONE_DIR, exist_ok=True)
    
    # Try to clone with token authentication
    token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
    if token:
        auth_url = f"https://{token}@github.com/{REPO}.wiki.git"
        returncode, stdout, stderr = run_command([
            "git", "clone",
            auth_url,
            WIKI_CLONE_DIR
        ], capture_output=False)
    else:
        returncode, stdout, stderr = run_command([
            "git", "clone",
            WIKI_REPO_URL,
            WIKI_CLONE_DIR
        ], capture_output=False)
    
    if returncode == 0:
        print("✅ Wiki repository cloned")
        return True
    else:
        # If clone failed, wiki may not be initialized yet
        # Initialize an empty git repository locally
        print("ℹ️  Wiki repository not found, initializing empty wiki...")
        
        # Initialize empty git repo
        returncode, stdout, stderr = run_command([
            "git", "init"
        ], cwd=WIKI_CLONE_DIR, capture_output=False)
        
        if returncode != 0:
            print(f"❌ Failed to initialize git repository: {stderr}")
            return False
        
        # Set up remote
        remote_url = f"https://github.com/{REPO}.wiki.git"
        if token:
            remote_url = f"https://{token}@github.com/{REPO}.wiki.git"
        
        returncode, stdout, stderr = run_command([
            "git", "remote", "add", "origin", remote_url
        ], cwd=WIKI_CLONE_DIR, capture_output=False)
        
        if returncode != 0:
            print(f"❌ Failed to add remote: {stderr}")
            return False
        
        print("✅ Initialized empty wiki repository")
        return True

def transform_json_to_md(source_path: str, mapping: Dict[str, Any]) -> str:
    """Transform JSON file to markdown."""
    try:
        with open(source_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        md_parts = []
        
        # Title
        md_parts.append(f"# {mapping.get('title', 'Data Export')}")
        md_parts.append(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        md_parts.append("")
        
        # Basic info
        if isinstance(data, dict):
            md_parts.append("## Overview")
            for key, value in data.items():
                if key not in ['tasks', 'snapshots', 'rollback_history']:
                    if isinstance(value, list):
                        md_parts.append(f"- **{key}**: {', '.join(str(v) for v in value[:5])}")
                        if len(value) > 5:
                            md_parts.append(f"  *(and {len(value) - 5} more)*")
                    else:
                        md_parts.append(f"- **{key}**: {value}")
            md_parts.append("")
            
            # Tasks section
            if 'tasks' in data:
                md_parts.append("## Tasks")
                for task in data['tasks']:
                    md_parts.append(f"### {task.get('id', 'Unknown')}: {task.get('name', 'Unnamed')}")
                    md_parts.append(f"- **Version**: {task.get('version', 'N/A')}")
                    md_parts.append(f"- **Status**: {task.get('status', 'unknown')}")
                    md_parts.append(f"- **Location**: {task.get('location', 'N/A')}")
                    md_parts.append(f"- **Description**: {task.get('description', 'No description')[:200]}...")
                    md_parts.append("")
        
        return "\n".join(md_parts)
    
    except Exception as e:
        print(f"❌ Failed to transform JSON: {e}")
        return f"# Error\n\nFailed to process {source_path}: {e}"

def update_wiki_page(mapping: Dict[str, Any]) -> bool:
    """Update a single wiki page."""
    source_path = os.path.join(WORKSPACE_ROOT, mapping['source'])
    wiki_page = mapping['wiki_page']
    wiki_path = os.path.join(WIKI_CLONE_DIR, wiki_page)
    
    # Check if source file exists
    if not os.path.exists(source_path):
        print(f"⚠️  Source file not found: {source_path}")
        return False
    
    print(f"📝 Updating wiki page: {wiki_page}")
    
    # Read source content
    try:
        if mapping.get('transform') == 'json_to_md':
            content = transform_json_to_md(source_path, mapping)
        else:
            with open(source_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Add header with title
            header = f"# {mapping.get('title', wiki_page.replace('-', ' ').replace('.md', ''))}\n\n"
            content = header + content
    except Exception as e:
        print(f"❌ Failed to read source file {source_path}: {e}")
        return False
    
    # Write to wiki
    os.makedirs(os.path.dirname(wiki_path), exist_ok=True)
    try:
        with open(wiki_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Updated {wiki_page}")
        return True
    except Exception as e:
        print(f"❌ Failed to write wiki page {wiki_path}: {e}")
        return False

def commit_and_push_wiki() -> bool:
    """Commit and push changes to wiki."""
    print("💾 Committing wiki changes...")
    
    # Check if there are any changes
    returncode, stdout, stderr = run_command([
        "git", "status", "--porcelain"
    ], cwd=WIKI_CLONE_DIR)
    
    if not stdout.strip():
        print("✅ No changes to commit")
        return True
    
    print("Changes to commit:")
    print(stdout)
    
    # Add all files
    returncode, stdout, stderr = run_command([
        "git", "add", "."
    ], cwd=WIKI_CLONE_DIR, capture_output=False)
    
    if returncode != 0:
        print(f"❌ Failed to add files: {stderr}")
        return False
    
    # Commit
    commit_message = f"Update wiki from workspace - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    returncode, stdout, stderr = run_command([
        "git", "commit", "-m", commit_message
    ], cwd=WIKI_CLONE_DIR, capture_output=False)
    
    if returncode != 0 and "nothing to commit" not in stderr.lower():
        print(f"❌ Failed to commit: {stderr}")
        return False
    
    # Push - use --set-upstream for initial push
    print("📤 Pushing wiki changes...")
    returncode, stdout, stderr = run_command([
        "git", "push", "--set-upstream", "origin", "master"
    ], cwd=WIKI_CLONE_DIR, capture_output=True)
    
    if returncode == 0:
        print("✅ Wiki changes pushed successfully")
        return True
    else:
        print(f"❌ Failed to push wiki changes: {stderr}")
        
        # Try alternative: maybe the branch is called 'main'
        print("🔄 Trying with 'main' branch...")
        returncode, stdout, stderr = run_command([
            "git", "branch", "-m", "main"
        ], cwd=WIKI_CLONE_DIR, capture_output=False)
        
        if returncode == 0:
            returncode, stdout, stderr = run_command([
                "git", "push", "--set-upstream", "origin", "main"
            ], cwd=WIKI_CLONE_DIR, capture_output=True)
            
            if returncode == 0:
                print("✅ Wiki changes pushed successfully to 'main' branch")
                return True
        
        return False

def create_home_page() -> bool:
    """Create or update the wiki home page."""
    home_page_path = os.path.join(WIKI_CLONE_DIR, "Home.md")
    
    print("🏠 Creating wiki home page...")
    
    content = """# OpenClaw Workspace Wiki

Welcome to the OpenClaw Workspace wiki! This wiki contains documentation for the financial strategy automation system.

## Overview

OpenClaw Workspace is a comprehensive system for automating financial investment strategies, including:

- **T01**: Limit Up Strategy (龙头战法) for A-share stock selection
- **T99**: Review and optimization task for strategy performance analysis
- **T100**: Macro monitoring for economic data and market sentiment

## Quick Links

### Guides
- [[Workspace-Guide]] - How to use the workspace
- [[Agent-Personality]] - The AI assistant's personality and principles
- [[User-Profile]] - User information and preferences

### Tasks
- [[Task-Registry]] - Overview of all registered tasks
- [[T01-Limit-Up-Strategy]] - T01 task documentation
- [[T01-User-Guide]] - T01 user guide
- [[T99-Review-Task]] - T99 task documentation
- [[T100-Macro-Monitor]] - T100 task documentation

### History
- [[Project-History]] - Project timeline and significant events

## Automation Features

This workspace includes several automation features:

1. **Automatic Git commits** - Critical configuration files are auto-staged
2. **GitHub Issues synchronization** - Tasks are synchronized with GitHub Issues
3. **CI/CD pipeline** - Automatic validation on push
4. **Release management** - Automated version tagging and releases
5. **Wiki synchronization** - This wiki is automatically updated from workspace files

## Getting Started

1. Review the [[Workspace-Guide]] for basic usage
2. Check the [[Task-Registry]] for available tasks
3. Explore task-specific documentation for details

---

*This wiki is automatically synchronized from the OpenClaw workspace. Last updated: {timestamp}*
""".format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    try:
        with open(home_page_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Created home page")
        return True
    except Exception as e:
        print(f"❌ Failed to create home page: {e}")
        return False

def sync_wiki() -> bool:
    """Main synchronization function."""
    print("🔄 Synchronizing workspace to GitHub Wiki...")
    
    # Check if wiki exists
    if not check_wiki_exists():
        print("⚠️  Wiki does not exist. You may need to enable the wiki in repository settings.")
        print("   To enable wiki: Go to repository Settings → Features → Wiki → check 'Restrict editing to collaborators only'")
        return False
    
    # Clone wiki
    if not clone_wiki():
        return False
    
    # Update wiki pages
    success = True
    for mapping in WIKI_MAPPING:
        if not update_wiki_page(mapping):
            success = False
    
    # Create home page
    if not create_home_page():
        success = False
    
    # Commit and push
    if success:
        if not commit_and_push_wiki():
            success = False
    
    # Cleanup
    if os.path.exists(WIKI_CLONE_DIR):
        shutil.rmtree(WIKI_CLONE_DIR)
    
    if success:
        print("✅ Wiki synchronization completed successfully")
        return True
    else:
        print("⚠️  Wiki synchronization completed with warnings")
        return False

def check_sync_status() -> bool:
    """Check synchronization status."""
    print("🔍 Checking wiki synchronization status...")
    
    if not check_wiki_exists():
        print("❌ Wiki does not exist")
        return False
    
    # Clone wiki temporarily
    if not clone_wiki():
        return False
    
    # Check each mapping
    out_of_sync = []
    for mapping in WIKI_MAPPING:
        source_path = os.path.join(WORKSPACE_ROOT, mapping['source'])
        wiki_page = mapping['wiki_page']
        wiki_path = os.path.join(WIKI_CLONE_DIR, wiki_page)
        
        if not os.path.exists(source_path):
            out_of_sync.append(f"❌ Source file missing: {mapping['source']}")
        elif not os.path.exists(wiki_path):
            out_of_sync.append(f"❌ Wiki page missing: {wiki_page}")
        else:
            # TODO: Compare content
            pass
    
    # Cleanup
    if os.path.exists(WIKI_CLONE_DIR):
        shutil.rmtree(WIKI_CLONE_DIR)
    
    if out_of_sync:
        print("📋 Out of sync items:")
        for item in out_of_sync:
            print(f"  {item}")
        return False
    else:
        print("✅ Wiki appears to be in sync")
        return True

def init_wiki() -> bool:
    """Initialize wiki (enable if not already enabled)."""
    print("🚀 Initializing GitHub Wiki...")
    
    # Check current wiki status
    if check_wiki_exists():
        print("✅ Wiki is already enabled")
        return True
    
    print("ℹ️  Wiki is not enabled. Please enable it manually:")
    print("   1. Go to https://github.com/jaccchina-ai/openclaw-workspace/settings")
    print("   2. Navigate to 'Features' section")
    print("   3. Find 'Wiki' and check 'Restrict editing to collaborators only'")
    print("   4. Save changes")
    print("")
    print("After enabling, run 'python3 wiki_sync.py sync' to populate the wiki.")
    
    return False

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nCommands:")
        print("  sync      - Synchronize documentation to wiki")
        print("  check     - Check synchronization status")
        print("  init      - Initialize wiki repository")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "sync":
        success = sync_wiki()
        sys.exit(0 if success else 1)
    elif command == "check":
        success = check_sync_status()
        sys.exit(0 if success else 1)
    elif command == "init":
        success = init_wiki()
        sys.exit(0 if success else 1)
    else:
        print(f"❌ Unknown command: {command}")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()