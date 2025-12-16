"""
Gradual Git Commit Script
Commits 5-6 files per day until all files are committed.
Automatically stops when complete.
"""

import os
import subprocess
import json
from datetime import datetime

# Configuration
FILES_PER_DAY = 15  # Increased to finish in ~4 days (Total ~55 files)
PROJECT_DIR = r"c:\Users\shind\Downloads\To Move Files\llm-council-master"
STATE_FILE = os.path.join(PROJECT_DIR, ".commit_state.json")
# Update this with your actual repo URL
REMOTE_URL = "https://github.com/Gandharv2323/llm-council-enhanced.git"

# Files to commit (in order)
ALL_FILES = [
    # Batch 1: Project Setup & Docs (Day 1)
    "README.md",
    "CONTRIBUTING.md",
    ".gitignore",
    "pyproject.toml",
    "uv.lock",
    "Dockerfile",
    "docker-compose.yml",
    "railway.toml",
    "nixpacks.toml",
    "render.yaml",
    "Procfile",
    ".github/workflows/ci.yml",
    "backend/__init__.py",
    "backend/main.py",
    "backend/config.py",
    
    # Batch 2: Core Backend Logic (Day 2)
    "backend/council.py",
    "backend/council_enhanced.py",
    "Dockerfile.backend",
    "backend/schemas.py",
    "backend/evaluation.py",
    "backend/calibration.py",
    "backend/claims.py",
    "backend/openrouter.py",
    "backend/database.py",
    "backend/resilience.py",
    "backend/benchmark.py",
    "backend/storage.py",
    
    # Batch 3: Core Frontend Setup (Day 3)
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/vite.config.js",
    "frontend/index.html",
    "frontend/Dockerfile",
    "frontend/.eslintrc.cjs",
    "frontend/src/main.jsx",
    "frontend/src/App.jsx",
    "frontend/src/App.css",
    "frontend/src/index.css",
    "frontend/src/api.js",
    
    # Batch 4: UI Components & Polish (Day 4)
    "frontend/src/components/EpistemicPanel.jsx",
    "frontend/src/components/EpistemicPanel.css",
    "frontend/src/components/CostEstimator.jsx",
    "frontend/src/components/CostEstimator.css",
    "frontend/src/components/DisagreementExplorer.jsx",
    "frontend/src/components/DisagreementExplorer.css",
    "frontend/src/hooks/useStreaming.js",
    "frontend/src/assets/react.svg",
    "frontend/public/vite.svg",
    "STREAK_LOG.md",
    "gradual_backup.py",
    "DAILY_BACKUP.bat"
]

# Professional Commit Messages map (based on Batch)
COMMIT_MESSAGES = {
    1: "chore: initial project setup, ci/cd config, and deployment files",
    2: "feat(backend): implement enhanced council with bradley-terry scoring and calibration",
    3: "feat(frontend): setup react app structure and core api integration",
    4: "feat(ui): add epistemic panels, cost estimator, and visualization components"
}

def load_state():
    """Load commit state from file."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"committed_count": 0, "completed": False, "batch": 1}

def save_state(state):
    """Save commit state to file."""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def run_git(args):
    """Run a git command."""
    result = subprocess.run(
        ["git"] + args,
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True
    )
    return result.returncode == 0, result.stdout + result.stderr

def init_repo():
    """Initialize git repo if not exists."""
    git_dir = os.path.join(PROJECT_DIR, ".git")
    if not os.path.exists(git_dir):
        print("Initializing git repository...")
        run_git(["init"])
        run_git(["remote", "add", "origin", REMOTE_URL])
        run_git(["branch", "-M", "main"])
        return True
    return False

def main():
    os.chdir(PROJECT_DIR)
    
    # Load state
    state = load_state()
    
    if state["completed"]:
        print("=" * 50)
        print("ALL FILES ALREADY COMMITTED!")
        print("Project successfully uploaded.")
        print("=" * 50)
        return
    
    # Initialize repo if needed
    init_repo()
    
    # Calculate which files to commit today
    start_idx = state["committed_count"]
    end_idx = min(start_idx + FILES_PER_DAY, len(ALL_FILES))
    
    if start_idx >= len(ALL_FILES):
        state["completed"] = True
        save_state(state)
        print("All files committed!")
        return
    
    files_today = ALL_FILES[start_idx:end_idx]
    current_batch = state["batch"]
    today = datetime.now().strftime("%Y-%m-%d")
    
    print("=" * 50)
    print(f"BATCH {current_batch} - {today}")
    print(f"Processing {len(files_today)} files...")
    print("=" * 50)
    
    # Add files
    for file in files_today:
        filepath = os.path.join(PROJECT_DIR, file)
        if os.path.exists(filepath):
            run_git(["add", file])
            print(f"  + {file}")
        else:
            print(f"  ! {file} (not found, skipping)")
    
    # Add metadata files
    if os.path.exists("STREAK_LOG.md"): run_git(["add", "STREAK_LOG.md"])
    if os.path.exists("gradual_backup.py"): run_git(["add", "gradual_backup.py"])
    if os.path.exists("DAILY_BACKUP.bat"): run_git(["add", "DAILY_BACKUP.bat"])
    
    # Commit with professional message
    # Use the batch number to get the message, default to a generic one if out of range
    message = COMMIT_MESSAGES.get(current_batch, f"feat: incremental update batch {current_batch}")
    
    success, output = run_git(["commit", "-m", message])
    
    if success:
        print(f"\nCommit successful: '{message}'")
        
        # Push
        success, output = run_git(["push", "-u", "origin", "main"])
        if success:
            print("Pushed to GitHub!")
        else:
            print(f"Push output: {output}")
            # Try force push if first time (ensure clean history)
            if current_batch == 1:
                run_git(["push", "-u", "origin", "main", "--force"])
    else:
        print(f"Commit output: {output}")
    
    # Update state
    state["committed_count"] = end_idx
    state["batch"] += 1
    
    if end_idx >= len(ALL_FILES):
        state["completed"] = True
        print("\n" + "=" * 50)
        print("ALL FILES COMMITTED! Project upload complete!")
        print("=" * 50)
    
    save_state(state)
    
    remaining = len(ALL_FILES) - end_idx
    if remaining > 0:
        print(f"\nRemaining: {remaining} files")

if __name__ == "__main__":
    main()
