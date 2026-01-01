# Instructions to Push to GitHub

## Option 1: Using the Batch Script (Windows)
1. Open Command Prompt or PowerShell
2. Navigate to the `muckard-fastapi` directory
3. Run: `push_to_github.bat`

## Option 2: Using PowerShell Script
1. Open PowerShell
2. Navigate to the `muckard-fastapi` directory
3. Run: `.\push_to_github.ps1`

## Option 3: Manual Git Commands

Run these commands in sequence from the `muckard-fastapi` directory:

```bash
# Initialize git (if not already initialized)
git init

# Add remote repository
git remote add origin https://github.com/hasanmasudnet/muckard-fastapi.git
# OR if remote already exists:
git remote set-url origin https://github.com/hasanmasudnet/muckard-fastapi.git

# Add all files
git add .

# Commit changes
git commit -m "Initial commit: FastAPI backend for Muckard"

# Set main branch and push
git branch -M main
git push -u origin main
```

## Note
- Make sure you have Git installed and configured
- You may need to authenticate with GitHub (use personal access token if 2FA is enabled)
- The `.gitignore` file will exclude `venv/`, `__pycache__/`, `.env`, etc.




