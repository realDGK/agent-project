#!/bin/bash
# Quick setup for testing with real documents

echo "========================================="
echo " SETTING UP TESTING ENVIRONMENT"
echo "========================================="

# Install Python dependencies
echo ""
echo "Installing required Python packages..."
pip install -q --upgrade pip
pip install -q networkx fastapi uvicorn asyncpg google-generativeai python-multipart python-dotenv

# Check system readiness
echo ""
echo "Checking system readiness..."
python3 check_system.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ System ready! Starting server..."
    echo ""
    python3 test_with_real_data.py
else
    echo ""
    echo "⚠️  Please fix the issues above before testing."
    echo ""
    echo "Most common fix:"
    echo "  export GOOGLE_API_KEY='your-gemini-api-key'"
    echo ""
fi
