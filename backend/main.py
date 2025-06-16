"""
FastAPI backend for Meeting Dashboard - Zoom Recording Sync
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, File, UploadFile, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
import asyncio
import logging
from datetime import datetime
from pathlib import Path

from .config import Settings
from .auth import ZoomAuth
from .services.file_monitor import ZoomFileMonitor
from .services.storage import StorageService
from .services.database import DatabaseService
from .models.recording import Recording, RecordingMetadata
from .utils.error_handler import AppErrorHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Meeting Dashboard API",
    description="Backend for Zoom recording sync and meeting management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
settings = Settings()
security = HTTPBearer()
zoom_auth = ZoomAuth(settings)
storage_service = StorageService(settings)
db_service = DatabaseService(settings)
file_monitor = ZoomFileMonitor(settings)
error_handler = AppErrorHandler()

# Models for API requests/responses
class ZoomAuthRequest(BaseModel):
    """Request model for Zoom OAuth initialization"""
    redirect_uri: str = Field(..., description="OAuth redirect URI")

class ZoomAuthResponse(BaseModel):
    """Response model for Zoom OAuth"""
    auth_url: str = Field(..., description="Zoom OAuth authorization URL")
    state: str = Field(..., description="OAuth state parameter")

class ZoomTokenRequest(BaseModel):
    """Request model for Zoom OAuth token exchange"""
    code: str = Field(..., description="OAuth authorization code")
    state: str = Field(..., description="OAuth state parameter")

class RecordingUploadResponse(BaseModel):
    """Response model for recording upload"""
    recording_id: str = Field(..., description="Unique recording ID")
    file_url: str = Field(..., description="URL of uploaded file")
    metadata: RecordingMetadata = Field(..., description="Recording metadata")
    message: str = Field(..., description="Success message")

class MonitorStatusResponse(BaseModel):
    """Response model for file monitor status"""
    status: str = Field(..., description="Monitor status")
    is_active: bool = Field(..., description="Whether monitor is active")
    monitored_path: str = Field(..., description="Path being monitored")
    last_check: Optional[datetime] = Field(None, description="Last check timestamp")

class ErrorResponse(BaseModel):
    """Standard error response model"""
    error: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

# Dependency injection
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate JWT token and return current user"""
    try:
        # For now, return a mock user - implement JWT validation as needed
        return {"user_id": "mock_user", "email": "user@example.com"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        logger.info("Starting Meeting Dashboard API...")
        
        # Initialize database
        await db_service.initialize()
        
        # Initialize storage service
        await storage_service.initialize()
        
        # Start file monitor if Zoom path is configured
        if settings.zoom_recordings_path:
            await file_monitor.start_monitoring()
            logger.info(f"Started monitoring Zoom recordings at: {settings.zoom_recordings_path}")
        
        logger.info("Meeting Dashboard API started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        logger.info("Shutting down Meeting Dashboard API...")
        
        # Stop file monitor
        await file_monitor.stop_monitoring()
        
        # Close database connections
        await db_service.close()
        
        logger.info("Meeting Dashboard API shut down successfully")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

# Health check endpoint
@app.get("/health", response_model=Dict[str, str])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

# Zoom OAuth endpoints
@app.post("/auth/zoom/authorize", response_model=ZoomAuthResponse)
async def zoom_authorize(request: ZoomAuthRequest):
    """Initialize Zoom OAuth flow"""
    try:
        auth_url, state = await zoom_auth.get_authorization_url(request.redirect_uri)
        return ZoomAuthResponse(auth_url=auth_url, state=state)
    except Exception as e:
        logger.error(f"Failed to initialize Zoom OAuth: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize Zoom authorization"
        )

@app.post("/auth/zoom/token")
async def zoom_token_exchange(request: ZoomTokenRequest, current_user: dict = Depends(get_current_user)):
    """Exchange OAuth code for access token"""
    try:
        token_data = await zoom_auth.exchange_code_for_token(request.code, request.state)
        
        # Store token in database
        await db_service.store_zoom_token(current_user["user_id"], token_data)
        
        return {
            "message": "Zoom authorization successful",
            "token_expires_at": token_data.get("expires_at")
        }
    except Exception as e:
        logger.error(f"Failed to exchange Zoom OAuth token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange authorization code"
        )

@app.get("/auth/zoom/status")
async def zoom_auth_status(current_user: dict = Depends(get_current_user)):
    """Check Zoom authentication status"""
    try:
        token_data = await db_service.get_zoom_token(current_user["user_id"])
        
        if not token_data:
            return {"connected": False, "status": "Not Connected"}
        
        # Check if token is expired
        is_expired = await zoom_auth.is_token_expired(token_data)
        
        if is_expired:
            return {"connected": False, "status": "Token Expired"}
        
        return {"connected": True, "status": "Connected"}
        
    except Exception as e:
        logger.error(f"Failed to check Zoom auth status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check authentication status"
        )

# Recording upload endpoint
@app.post("/upload/recording", response_model=RecordingUploadResponse)
async def upload_recording(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    meeting_title: Optional[str] = None,
    meeting_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Upload a meeting recording"""
    try:
        # Validate file type
        if not file.filename.lower().endswith(('.mp4', '.m4a', '.mp3', '.wav')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Supported formats: mp4, m4a, mp3, wav"
            )
        
        # Generate unique recording ID
        recording_id = f"rec_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{current_user['user_id']}"
        
        # Upload file to storage
        file_url = await storage_service.upload_file(
            file, 
            f"recordings/{current_user['user_id']}/{recording_id}/{file.filename}"
        )
        
        # Create recording metadata
        metadata = RecordingMetadata(
            recording_id=recording_id,
            user_id=current_user["user_id"],
            file_url=file_url,
            meeting_title=meeting_title or f"Meeting {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            file_name=file.filename,
            file_size=file.size or 0,
            upload_timestamp=datetime.utcnow(),
            meeting_date=datetime.fromisoformat(meeting_date) if meeting_date else datetime.utcnow()
        )
        
        # Store metadata in database
        await db_service.store_recording_metadata(metadata)
        
        # Add background task for processing (transcription, etc.)
        background_tasks.add_task(process_recording_async, recording_id, file_url)
        
        return RecordingUploadResponse(
            recording_id=recording_id,
            file_url=file_url,
            metadata=metadata,
            message="Recording uploaded successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload recording: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload recording"
        )

# File monitor endpoints
@app.get("/monitor/status", response_model=MonitorStatusResponse)
async def get_monitor_status(current_user: dict = Depends(get_current_user)):
    """Get file monitor status"""
    try:
        status = await file_monitor.get_status()
        return MonitorStatusResponse(**status)
    except Exception as e:
        logger.error(f"Failed to get monitor status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get monitor status"
        )

@app.post("/monitor/start")
async def start_monitor(current_user: dict = Depends(get_current_user)):
    """Start file monitoring"""
    try:
        if not settings.zoom_recordings_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Zoom recordings path not configured"
            )
        
        await file_monitor.start_monitoring()
        return {"message": "File monitoring started", "path": settings.zoom_recordings_path}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start monitor: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start file monitoring"
        )

@app.post("/monitor/stop")
async def stop_monitor(current_user: dict = Depends(get_current_user)):
    """Stop file monitoring"""
    try:
        await file_monitor.stop_monitoring()
        return {"message": "File monitoring stopped"}
    except Exception as e:
        logger.error(f"Failed to stop monitor: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop file monitoring"
        )

@app.put("/monitor/path")
async def update_monitor_path(
    path: str,
    current_user: dict = Depends(get_current_user)
):
    """Update monitored path"""
    try:
        if not Path(path).expanduser().exists():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Path does not exist"
            )
        
        await file_monitor.update_path(path)
        return {"message": "Monitor path updated", "path": path}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update monitor path: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update monitor path"
        )

# Recording management endpoints
@app.get("/recordings")
async def get_recordings(
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """Get user's recordings"""
    try:
        recordings = await db_service.get_user_recordings(
            current_user["user_id"], 
            limit=limit, 
            offset=offset
        )
        return {
            "recordings": recordings,
            "total": len(recordings),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Failed to get recordings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recordings"
        )

@app.get("/recordings/{recording_id}")
async def get_recording(
    recording_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get specific recording"""
    try:
        recording = await db_service.get_recording(recording_id, current_user["user_id"])
        
        if not recording:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recording not found"
            )
        
        return recording
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get recording: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recording"
        )

# Background task for processing recordings
async def process_recording_async(recording_id: str, file_url: str):
    """Background task to process uploaded recording"""
    try:
        logger.info(f"Processing recording {recording_id}")
        
        # Here you would add:
        # - Transcription service integration
        # - Summary generation
        # - Action item extraction
        # - Notification sending
        
        # Update processing status
        await db_service.update_recording_status(recording_id, "processed")
        
        logger.info(f"Recording {recording_id} processed successfully")
        
    except Exception as e:
        logger.error(f"Failed to process recording {recording_id}: {str(e)}")
        await db_service.update_recording_status(recording_id, "failed")

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 