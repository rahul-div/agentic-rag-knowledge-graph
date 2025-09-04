# Git & GitHub Beginner's Complete Guide

## 🎯 **Table of Contents**
1. [Essential Terminology](#essential-terminology)
2. [Understanding Branches](#understanding-branches)
3. [Basic Git Commands](#basic-git-commands)
4. [Feature Branch Workflow](#feature-branch-workflow)
5. [Pull Requests Explained](#pull-requests-explained)
6. [Common Scenarios](#common-scenarios)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## 📚 **Essential Terminology**

### **Core Concepts**

| Term | Definition | Example |
|------|------------|---------|
| **Repository (Repo)** | Your project folder with all files and change history | `agentic-rag-knowledge-graph/` |
| **Commit** | A snapshot of your changes with a descriptive message | `"feat: add multi-tenant support"` |
| **Branch** | A separate timeline of development | `main`, `feature/user-auth` |
| **Remote** | The version of your repo stored online (GitHub) | `origin` (your GitHub repo) |
| **Local** | The version of your repo on your computer | Your laptop's copy |
| **Clone** | Download a copy of a repo from GitHub to your computer | `git clone <url>` |
| **Fork** | Create your own copy of someone else's repo | Used for contributing to open source |

### **Key Actions**

| Action | What it Does | When to Use |
|--------|--------------|-------------|
| **Stage** | Mark files to be included in next commit | Before committing changes |
| **Commit** | Save a snapshot of staged changes | After completing a logical unit of work |
| **Push** | Upload your local commits to GitHub | To backup work or share with team |
| **Pull** | Download and merge changes from GitHub | To get latest updates from team |
| **Merge** | Combine changes from one branch into another | To add completed features to main |
| **Pull Request** | Request to merge your branch into another | To propose changes for review |

---

## 🌿 **Understanding Branches**

### **What Are Branches?**

Think of branches as **parallel universes** for your code:

```
main branch:     A---B---C---D---E
                  \
feature branch:    F---G---H
                    \
another feature:     I---J
```

### **Why Use Branches?**

- 🛡️ **Safety**: Keep main branch stable
- 🔄 **Parallel Work**: Multiple features at once
- 👥 **Collaboration**: Team members don't interfere
- 🎯 **Focus**: One feature per branch
- 🔙 **Rollback**: Easy to abandon bad ideas

### **Branch Types**

| Branch Type | Purpose | Example Name |
|-------------|---------|--------------|
| **main** | Stable, production-ready code | `main` |
| **feature** | New features or improvements | `feature/multi-tenant` |
| **bugfix** | Fix specific bugs | `bugfix/login-error` |
| **hotfix** | Urgent production fixes | `hotfix/security-patch` |
| **release** | Prepare for new release | `release/v1.2.0` |

---

## 💻 **Basic Git Commands**

### **Setup & Configuration**

```bash
# First-time setup
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Check current settings
git config --list
```

### **Repository Management**

```bash
# Clone a repository from GitHub
git clone https://github.com/username/repo-name.git

# Initialize a new repository
git init

# Check status of your files
git status

# See what changed
git diff
```

### **Making Changes**

```bash
# Stage specific files
git add filename.txt
git add folder/

# Stage all changes
git add .

# Commit with message
git commit -m "Add new feature"

# Stage and commit in one step
git commit -am "Fix bug in login"
```

### **Branch Operations**

```bash
# List all branches
git branch

# Create new branch
git branch feature/new-feature

# Switch to branch
git checkout feature/new-feature

# Create and switch in one command
git checkout -b feature/new-feature

# Delete branch (after merging)
git branch -d feature/new-feature
```

### **Remote Operations**

```bash
# See remote repositories
git remote -v

# Push to remote branch
git push origin branch-name

# Pull latest changes
git pull origin main

# Push new branch and set tracking
git push -u origin feature/new-feature
```

---

## 🔄 **Feature Branch Workflow (Industry Standard)**

This is how **professional teams** work with Git. Let's walk through the complete process:

### **Step 1: Start a New Feature**

```bash
# Make sure you're on main and it's up to date
git checkout main
git pull origin main

# Create and switch to feature branch
git checkout -b feature/user-authentication

# Verify you're on the right branch
git branch
# * feature/user-authentication  ← You're here
#   main
```

### **Step 2: Work on Your Feature**

```bash
# Make changes to files
# ... edit code, add files, etc. ...

# Check what changed
git status
git diff

# Stage your changes
git add .

# Commit with descriptive message
git commit -m "feat: add user login functionality

- Implement JWT authentication
- Add login/logout endpoints
- Create user session management
- Add password hashing with bcrypt"

# Push to GitHub (first time)
git push -u origin feature/user-authentication

# Subsequent pushes
git push
```

### **Step 3: Keep Your Branch Updated**

If working for a long time, sync with main regularly:

```bash
# Switch to main
git checkout main

# Get latest changes
git pull origin main

# Switch back to your feature
git checkout feature/user-authentication

# Merge main into your feature (keeps it up to date)
git merge main
```

### **Step 4: Create Pull Request**

When your feature is ready:

1. **Push final changes:**
   ```bash
   git push origin feature/user-authentication
   ```

2. **Go to GitHub** → Your repository

3. **Click "Compare & pull request"** (or create manually)

4. **Fill out PR details:**
   ```
   Title: Add User Authentication System
   
   Description:
   ## What does this PR do?
   - Implements JWT-based authentication
   - Adds secure login/logout endpoints
   - Includes password hashing and validation
   
   ## How to test:
   1. Start the server: `python main.py`
   2. Go to `/docs` endpoint
   3. Test login with: username=test, password=test123
   
   ## Checklist:
   - [x] Tests pass
   - [x] Documentation updated
   - [x] No security vulnerabilities
   ```

### **Step 5: Code Review Process**

**Reviewer actions:**
- Review code changes
- Test functionality
- Suggest improvements
- Approve or request changes

**Author actions:**
- Address feedback
- Make requested changes
- Push updates (automatically updates PR)

### **Step 6: Merge the PR**

**Merge options:**

1. **Merge commit** (preserves branch history):
   ```
   main: A---B---C-------M
              \         /
   feature:    D---E---F
   ```

2. **Squash and merge** (clean single commit):
   ```
   main: A---B---C---S
   ```
   Where S contains all changes from D, E, F

3. **Rebase and merge** (linear history):
   ```
   main: A---B---C---D---E---F
   ```

### **Step 7: Clean Up and Sync**

```bash
# Switch to main
git checkout main

# Pull the merged changes
git pull origin main

# Delete local feature branch
git branch -d feature/user-authentication

# Delete remote branch (if not done automatically)
git push origin --delete feature/user-authentication

# Verify your changes are in main
git log --oneline -5
```

---

## 🔍 **Pull Requests Explained**

### **What is a Pull Request (PR)?**

A Pull Request is a **formal way to propose changes**. Think of it as saying:

> *"Hey team, I've completed this feature. Please review my changes and merge them into main if they look good."*

### **PR Lifecycle**

```
1. Create PR → 2. Review → 3. Discuss → 4. Approve → 5. Merge → 6. Deploy
```

### **PR Components**

#### **1. Title & Description**
```markdown
Title: Add Multi-Tenant RAG System

Description:
## Overview
This PR implements a complete multi-tenant RAG system with strict data isolation.

## Changes Made
- Added Neon PostgreSQL with Row-Level Security (RLS)
- Implemented Graphiti integration with group_id namespacing
- Created FastAPI endpoints with JWT authentication
- Added comprehensive deployment documentation

## Testing
- [x] Unit tests pass
- [x] Integration tests pass
- [x] Manual testing completed
- [x] Security review completed

## Breaking Changes
None

## Documentation
- Updated README.md
- Added deployment_guide.md
- Added API documentation
```

#### **2. File Changes (Diff)**
GitHub shows exactly what changed:
```diff
+ // New line added
- // Old line removed
  // Unchanged line
```

#### **3. Review Process**
- **Comment**: General feedback
- **Approve**: Ready to merge
- **Request Changes**: Needs fixes before merge

#### **4. Conversation**
- Discuss implementation decisions
- Ask questions about code
- Suggest improvements
- Share knowledge

### **Best PR Practices**

| ✅ Good | ❌ Avoid |
|---------|----------|
| Small, focused changes | Massive PRs with many features |
| Clear, descriptive title | Vague titles like "Fix stuff" |
| Detailed description | No description |
| Tests included | No tests |
| Documentation updated | Outdated docs |
| Self-review done | Submit without checking |

---

## 🎯 **Common Scenarios**

### **Scenario 1: Working Alone on Main**

If you're the only developer:

```bash
# Simple workflow
git add .
git commit -m "Add new feature"
git push origin main
```

**Pros:** Simple, fast
**Cons:** No safety net, no code review

### **Scenario 2: Team with Feature Branches**

Professional team workflow:

```bash
# Create feature branch
git checkout -b feature/my-feature

# Work and commit
git add .
git commit -m "Implement feature"
git push -u origin feature/my-feature

# Create PR on GitHub
# After approval, merge via GitHub
# Clean up locally
git checkout main
git pull origin main
git branch -d feature/my-feature
```

**Pros:** Safe, reviewable, collaborative
**Cons:** More steps, requires discipline

### **Scenario 3: Contributing to Open Source**

Contributing to someone else's project:

```bash
# 1. Fork the repository on GitHub
# 2. Clone your fork
git clone https://github.com/yourusername/their-project.git

# 3. Add original repo as upstream
git remote add upstream https://github.com/originalowner/their-project.git

# 4. Create feature branch
git checkout -b feature/my-contribution

# 5. Make changes and commit
git add .
git commit -m "Add awesome feature"

# 6. Push to your fork
git push origin feature/my-contribution

# 7. Create PR from your fork to their main
# 8. Respond to feedback and iterate
```

### **Scenario 4: Fixing Conflicts**

When two people change the same code:

```bash
# You'll see this when pulling/merging
git pull origin main
# Auto-merging file.py
# CONFLICT (content): Merge conflict in file.py

# Open the file and look for conflict markers
```

Conflict markers look like this:
```python
def function():
<<<<<<< HEAD
    return "your changes"
=======
    return "their changes"
>>>>>>> branch-name
```

Fix by choosing the correct version:
```python
def function():
    return "correct version combining both"
```

Then complete the merge:
```bash
git add file.py
git commit -m "Resolve merge conflict"
```

---

## 🏆 **Best Practices**

### **Commit Messages**

Follow the **Conventional Commits** format:

```
type(scope): description

feat(auth): add JWT authentication
fix(api): resolve database connection timeout
docs(readme): update installation instructions
style(css): fix button alignment
refactor(utils): simplify date formatting
test(auth): add login endpoint tests
chore(deps): update dependencies
```

### **Branch Naming**

Use descriptive, consistent names:

```bash
# Good examples
feature/user-authentication
feature/multi-tenant-support
bugfix/login-timeout
hotfix/security-vulnerability
release/v1.2.0

# Avoid
feature/stuff
fix
new-branch
branch1
```

### **Workflow Rules**

1. **Never work directly on main** (except for small personal projects)
2. **Always pull before starting work** to get latest changes
3. **Create small, focused commits** rather than giant ones
4. **Write descriptive commit messages** that explain WHY, not just WHAT
5. **Test your changes** before creating PR
6. **Review your own PR** before asking others to review
7. **Delete merged branches** to keep repo clean
8. **Use draft PRs** for work-in-progress

### **File Management**

```bash
# Always check what you're committing
git status
git diff

# Don't commit these files
echo "node_modules/" >> .gitignore
echo ".env" >> .gitignore
echo "*.log" >> .gitignore
echo "__pycache__/" >> .gitignore

# Commit the .gitignore file
git add .gitignore
git commit -m "Add .gitignore file"
```

---

## 🚨 **Troubleshooting**

### **Common Problems & Solutions**

#### **1. "I committed to the wrong branch!"**

```bash
# If you haven't pushed yet
# Move commits to correct branch
git checkout correct-branch
git cherry-pick commit-hash

# Remove from wrong branch
git checkout wrong-branch
git reset --hard HEAD~1  # Remove last commit
```

#### **2. "I want to undo my last commit!"**

```bash
# Keep changes, just undo commit
git reset --soft HEAD~1

# Undo commit and changes
git reset --hard HEAD~1

# If already pushed (creates new commit)
git revert HEAD
```

#### **3. "My branch is behind main!"**

```bash
# Update your branch with latest main
git checkout main
git pull origin main
git checkout your-branch
git merge main
```

#### **4. "I have merge conflicts!"**

```bash
# 1. See which files have conflicts
git status

# 2. Open each file and fix conflicts
# Look for <<<<<<< ======= >>>>>>> markers

# 3. After fixing, stage the files
git add filename.py

# 4. Complete the merge
git commit -m "Resolve merge conflicts"
```

#### **5. "I want to start over!"**

```bash
# Discard all local changes
git checkout .

# Remove untracked files
git clean -fd

# Reset to match remote exactly
git reset --hard origin/main
```

### **Emergency Commands**

```bash
# See commit history
git log --oneline

# See what changed in a commit
git show commit-hash

# Compare branches
git diff main..feature-branch

# Stash changes temporarily
git stash
git stash pop

# Create backup branch before risky operation
git checkout -b backup-branch
```

---

## 🎓 **Learning Path**

### **Beginner Level**
1. Learn basic commands: `add`, `commit`, `push`, `pull`
2. Understand what branches are
3. Practice creating and switching branches
4. Make your first Pull Request

### **Intermediate Level**
1. Master the feature branch workflow
2. Learn to resolve merge conflicts
3. Understand different merge strategies
4. Practice code reviews

### **Advanced Level**
1. Learn rebasing and history manipulation
2. Understand Git internals
3. Master complex workflows (GitFlow, GitHub Flow)
4. Set up automated CI/CD with Git hooks

---

## 📖 **Additional Resources**

### **Essential Reading**
- [Git Official Documentation](https://git-scm.com/doc)
- [GitHub Guides](https://guides.github.com/)
- [Atlassian Git Tutorials](https://www.atlassian.com/git/tutorials)

### **Visual Tools**
- **GitKraken**: Visual Git client
- **SourceTree**: Free Git GUI
- **VS Code**: Built-in Git integration
- **GitHub Desktop**: Simple GitHub integration

### **Practice Platforms**
- [Learn Git Branching](https://learngitbranching.js.org/) (Interactive tutorial)
- [Git Immersion](http://gitimmersion.com/) (Hands-on tutorial)
- [GitHub Skills](https://skills.github.com/) (GitHub-specific tutorials)

---

## 🎯 **Quick Reference**

### **Daily Commands**
```bash
git status              # Check what's changed
git add .               # Stage all changes
git commit -m "message" # Commit with message
git push                # Upload to GitHub
git pull                # Download latest changes
git checkout -b branch  # Create and switch to branch
```

### **Branch Workflow**
```bash
git checkout main       # Switch to main
git pull origin main    # Get latest
git checkout -b feature # Create feature branch
# ... work and commit ...
git push -u origin feature # Push feature branch
# ... create PR on GitHub ...
# ... after merge ...
git checkout main       # Back to main
git pull origin main    # Get merged changes
git branch -d feature   # Delete local branch
```

---

## 🏁 **Conclusion**

Git and GitHub are **essential tools** for any developer. The feature branch workflow we've covered is used by:

- 🏢 **Every major tech company** (Google, Microsoft, Apple, Meta)
- 🌟 **All successful open source projects** (Linux, React, VS Code)
- 👥 **Professional development teams** worldwide

**Key Takeaways:**
1. **Branches keep you safe** - never break main
2. **Pull Requests enable collaboration** - review before merging
3. **Small, frequent commits** are better than large ones
4. **Good commit messages** help your future self
5. **Practice makes perfect** - start with simple workflows

Start with the basics, practice regularly, and gradually adopt more advanced workflows as you become comfortable. Remember: every expert was once a beginner! 🚀

---

*Happy coding and collaborating! 🎉*
