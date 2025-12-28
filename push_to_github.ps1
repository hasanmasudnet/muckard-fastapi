# PowerShell script to push code to GitHub
# Run this script from the muckard-fastapi directory

Write-Host "Initializing Git repository..." -ForegroundColor Green

# Initialize git if not already initialized
if (-not (Test-Path .git)) {
    git init
    Write-Host "Git repository initialized." -ForegroundColor Green
} else {
    Write-Host "Git repository already initialized." -ForegroundColor Yellow
}

# Check if remote exists
$remoteExists = git remote | Select-String -Pattern "origin"
if (-not $remoteExists) {
    Write-Host "Adding remote repository..." -ForegroundColor Green
    git remote add origin https://github.com/hasanmasudnet/muckard-fastapi.git
} else {
    Write-Host "Remote already exists. Updating URL..." -ForegroundColor Yellow
    git remote set-url origin https://github.com/hasanmasudnet/muckard-fastapi.git
}

# Add all files
Write-Host "Adding all files..." -ForegroundColor Green
git add .

# Check if there are changes to commit
$status = git status --porcelain
if ($status) {
    Write-Host "Committing changes..." -ForegroundColor Green
    git commit -m "Initial commit: FastAPI backend for Muckard"
} else {
    Write-Host "No changes to commit." -ForegroundColor Yellow
}

# Push to GitHub
Write-Host "Pushing to GitHub..." -ForegroundColor Green
git branch -M main
git push -u origin main

Write-Host "Done! Code pushed to GitHub." -ForegroundColor Green

