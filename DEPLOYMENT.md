# Version Control & Deployment Guide

## Overview
- **Development Branch**: `development` - Test changes locally
- **Production Branch**: `main` - Deployed to web (Render.com)
- **Current Version**: 1.0

## Branches

### Development Branch
- **Purpose**: Test new features locally before deploying
- **Location**: Your computer only
- **Use for**: Bug fixes, new features, experiments

### Main Branch (Production)
- **Purpose**: Stable version deployed to the web
- **Location**: GitHub + Render.com
- **URL**: https://chess-analyzer-fd9x.onrender.com/

## Workflow

### Working on New Features (Local Development)

```powershell
# 1. Switch to development branch
git checkout development

# 2. Make your changes to the code
# Edit files as needed...

# 3. Test locally
python chess_game.py
# Test at http://localhost:5000

# 4. Commit changes
git add .
git commit -m "Description of changes"
```

### Deploying to Web (When Ready)

```powershell
# 1. Make sure you're on development branch
git checkout development

# 2. Update version in version.py
# Change __version__ = "1.0" to "1.1" (or next version)

# 3. Commit version update
git add version.py
git commit -m "Bump version to 1.1"

# 4. Switch to main branch
git checkout main

# 5. Merge development into main
git merge development

# 6. Tag the new version
git tag v1.1 -m "Version 1.1 - Description of changes"

# 7. Push to GitHub (triggers automatic deployment)
git push origin main
git push origin --tags

# 8. Wait 3-5 minutes for Render to deploy
# Check: https://dashboard.render.com/
```

### Rolling Back (If Something Goes Wrong)

```powershell
# 1. Find the last good version
git tag

# 2. Checkout that version
git checkout v1.0

# 3. Create a new branch from it
git checkout -b hotfix

# 4. Push to main
git checkout main
git reset --hard v1.0
git push origin main --force
```

## Version History

### v1.0 (Current)
- Session persistence (game survives page refresh)
- Fast bot responses (0.3-0.8 seconds)
- 60-second timeout for analysis
- Auto-play mode
- Two difficulty levels (Easy & Strong)
- Undo moves
- Move history tracking

## Quick Reference

### Check Current Branch
```powershell
git branch
```

### Switch Branches
```powershell
# To development
git checkout development

# To production (main)
git checkout main
```

### View Version History
```powershell
git tag
git log --oneline
```

### See What Changed
```powershell
git diff development main
```

## Important Notes

⚠️ **Never push directly to main** - Always test in development first
⚠️ **Always update version.py** before deploying
⚠️ **Tag every release** for easy rollback
✅ **Test locally** before deploying to web
✅ **Keep development branch synced** with main after deployment
