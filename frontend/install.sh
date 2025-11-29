#!/bin/bash

# Healthcare Volunteer Coordinator - Frontend Installation Script

echo "🏥 Healthcare Volunteer Coordinator - Frontend Setup"
echo "=================================================="
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    echo "   Visit: https://nodejs.org/"
    exit 1
fi

echo "✅ Node.js version: $(node --version)"
echo "✅ npm version: $(npm --version)"
echo ""

# Check if in correct directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found. Please run this script from the frontend directory."
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm install

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed successfully"
echo ""

# Create .env.local if it doesn't exist
if [ ! -f ".env.local" ]; then
    echo "🔧 Creating .env.local file..."
    cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF
    echo "✅ Created .env.local with default API URL"
else
    echo "ℹ️  .env.local already exists"
fi

echo ""
echo "=================================================="
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Make sure the backend is running on http://localhost:8000"
echo "   2. Run: npm run dev"
echo "   3. Open: http://localhost:3000"
echo "   4. Login with: admin@healthcare.org / admin123"
echo ""
echo "📚 For more information, see README.md and SETUP.md"
echo "=================================================="

