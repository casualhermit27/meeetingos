#!/usr/bin/env python3
"""
Startup script for Meeting Dashboard Backend
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from config import get_settings_for_environment


def main():
    """Main entry point for the application"""
    # Get environment
    env = os.getenv("ENVIRONMENT", "development").lower()
    settings = get_settings_for_environment(env)
    
    # Configure uvicorn
    uvicorn_config = {
        "app": "main:app",
        "host": settings.host,
        "port": settings.port,
        "reload": settings.reload,
        "log_level": settings.log_level.lower(),
        "access_log": True,
    }
    
    print(f"🚀 Starting Meeting Dashboard API in {env} mode...")
    print(f"📡 Server will be available at: http://{settings.host}:{settings.port}")
    print(f"📚 API Documentation: http://{settings.host}:{settings.port}/docs")
    print(f"📋 ReDoc: http://{settings.host}:{settings.port}/redoc")
    
    if settings.zoom_recordings_path:
        print(f"📁 Monitoring Zoom recordings at: {settings.zoom_recordings_path}")
    else:
        print("⚠️  No Zoom recordings path configured - file monitoring disabled")
    
    print(f"💾 Storage provider: {settings.storage_provider}")
    print(f"🗄️  Database: {settings.supabase_url}")
    print("\n" + "="*60 + "\n")
    
    # Start the server
    uvicorn.run(**uvicorn_config)


if __name__ == "__main__":
    main() 