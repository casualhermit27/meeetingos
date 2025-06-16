#!/bin/bash

# Setup script for Meeting Dashboard Backend
echo "🚀 Setting up Meeting Dashboard Backend..."

# Check if Python 3.8+ is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Found Python $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
cd backend
pip install -r requirements.txt

# Create logs directory
mkdir -p logs

# Create .env file from example if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from example..."
    cp env.example .env
    echo "⚠️  Please edit .env file with your actual configuration values"
else
    echo "✅ .env file already exists"
fi

# Create default Zoom recordings directory
ZOOM_DIR="$HOME/Zoom"
if [ ! -d "$ZOOM_DIR" ]; then
    echo "📁 Creating default Zoom recordings directory..."
    mkdir -p "$ZOOM_DIR"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit backend/.env with your configuration"
echo "2. Set up your Zoom OAuth app at https://marketplace.zoom.us/develop/create"
echo "3. Create a Supabase project and configure the database"
echo "4. Run the backend: cd backend && python run.py"
echo ""
echo "Quick start:"
echo "  cd backend"
echo "  python run.py"
echo ""
echo "Documentation:"
echo "  API Docs: http://localhost:8000/docs"
echo "  ReDoc: http://localhost:8000/redoc" 