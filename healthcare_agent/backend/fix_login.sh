#!/bin/bash
# Quick fix script for 401 login errors

echo "=========================================="
echo "Fixing Login 401 Error"
echo "=========================================="
echo ""

cd "$(dirname "$0")"

# Check if virtual environment exists
if [ -d "../venv" ]; then
    echo "Activating virtual environment..."
    source ../venv/bin/activate
elif [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check if admin user exists and fix if needed
echo "Checking and fixing admin user..."
python seed_admin.py

echo ""
echo "=========================================="
echo "Done! Try logging in again with:"
echo "  Email: admin@example.com"
echo "  Password: admin123"
echo "=========================================="

