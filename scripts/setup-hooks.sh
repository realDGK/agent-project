#!/bin/bash
# Script to set up git hooks for the project

set -e

echo "Setting up Git hooks..."
echo "======================="

# Check if we're in a git repository
if [ ! -d .git ]; then
    echo "Error: Not in a git repository. Please run this from the project root."
    exit 1
fi

# Configure git to use our hooks directory
git config core.hooksPath .githooks

echo "✅ Git hooks configured successfully!"
echo ""
echo "The following hooks are now active:"
echo "  - pre-push: Validates document schemas before pushing"
echo ""
echo "To disable hooks temporarily, use: git config core.hooksPath .git/hooks"
echo "To re-enable hooks, run this script again."