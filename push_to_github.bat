@echo off
REM Batch script to push code to GitHub
REM Run this script from the muckard-fastapi directory

echo Initializing Git repository...

REM Initialize git if not already initialized
if not exist .git (
    git init
    echo Git repository initialized.
) else (
    echo Git repository already initialized.
)

REM Check if remote exists and add/update it
git remote remove origin 2>nul
git remote add origin https://github.com/hasanmasudnet/muckard-fastapi.git

REM Add all files
echo Adding all files...
git add .

REM Commit changes
echo Committing changes...
git commit -m "Initial commit: FastAPI backend for Muckard"

REM Push to GitHub
echo Pushing to GitHub...
git branch -M main
git push -u origin main

echo Done! Code pushed to GitHub.
pause

