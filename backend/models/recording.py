"""
Data models for recording management
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class ProcessingStatus(str, Enum):
    """Recording processing status enumeration"""
    PENDING = "pending"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class RecordingSource(str, Enum):
    """Recording source enumeration"""
    UPLOAD = "upload"
    LOCAL_FOLDER = "local_folder"
    ZOOM_CLOUD = "zoom_cloud"
    API = "api"


class RecordingMetadata(BaseModel):
    """Metadata for a recording file"""
    recording_id: str = Field(..., description="Unique recording identifier")
    user_id: str = Field(..., description="User who owns the recording")
    file_url: str = Field(..., description="URL to the recording file")
    meeting_title: str = Field(..., description="Title of the meeting")
    file_name: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes", ge=0)
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the file was uploaded")
    meeting_date: datetime = Field(..., description="When the meeting took place")
    source: RecordingSource = Field(default=RecordingSource.UPLOAD, description="Source of the recording")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
    
    @validator('meeting_title')
    def validate_meeting_title(cls, v):
        """Validate meeting title"""
        if not v or not v.strip():
            raise ValueError("Meeting title cannot be empty")
        return v.strip()[:500]  # Limit to 500 characters
    
    @validator('file_name')
    def validate_file_name(cls, v):
        """Validate file name"""
        if not v or not v.strip():
            raise ValueError("File name cannot be empty")
        return v.strip()


class Recording(BaseModel):
    """Complete recording object with all metadata and processing results"""
    recording_id: str = Field(..., description="Unique recording identifier")
    user_id: str = Field(..., description="User who owns the recording")
    file_url: str = Field(..., description="URL to the recording file")
    meeting_title: str = Field(..., description="Title of the meeting")
    file_name: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes", ge=0)
    upload_timestamp: datetime = Field(..., description="When the file was uploaded")
    meeting_date: datetime = Field(..., description="When the meeting took place")
    source: RecordingSource = Field(..., description="Source of the recording")
    processing_status: ProcessingStatus = Field(default=ProcessingStatus.PENDING, description="Processing status")
    
    # Processing results
    transcription_text: Optional[str] = Field(None, description="Transcribed text from the recording")
    summary: Optional[str] = Field(None, description="AI-generated summary")
    action_items: Optional[List[Dict[str, Any]]] = Field(None, description="Extracted action items")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the record was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When the record was last updated")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
    
    @validator('action_items')
    def validate_action_items(cls, v):
        """Validate action items format"""
        if v is not None and not isinstance(v, list):
            raise ValueError("Action items must be a list")
        return v


class ActionItem(BaseModel):
    """Individual action item from a meeting"""
    id: str = Field(..., description="Unique action item ID")
    text: str = Field(..., description="Action item description")
    assignee: Optional[str] = Field(None, description="Person assigned to the action")
    due_date: Optional[datetime] = Field(None, description="Due date for the action")
    priority: Optional[str] = Field(None, description="Priority level (high, medium, low)")
    status: str = Field(default="pending", description="Status of the action item")
    timestamp: Optional[float] = Field(None, description="Timestamp in recording where mentioned")
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
    
    @validator('text')
    def validate_text(cls, v):
        """Validate action item text"""
        if not v or not v.strip():
            raise ValueError("Action item text cannot be empty")
        return v.strip()
    
    @validator('priority')
    def validate_priority(cls, v):
        """Validate priority level"""
        if v and v.lower() not in ['high', 'medium', 'low']:
            raise ValueError("Priority must be 'high', 'medium', or 'low'")
        return v.lower() if v else None


class MeetingSummary(BaseModel):
    """AI-generated meeting summary"""
    recording_id: str = Field(..., description="Associated recording ID")
    summary: str = Field(..., description="Main summary text")
    key_points: List[str] = Field(default_factory=list, description="Key discussion points")
    decisions: List[str] = Field(default_factory=list, description="Decisions made")
    action_items: List[ActionItem] = Field(default_factory=list, description="Action items")
    participants: List[str] = Field(default_factory=list, description="Meeting participants")
    duration_minutes: Optional[int] = Field(None, description="Meeting duration in minutes")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="When summary was generated")
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
    
    @validator('summary')
    def validate_summary(cls, v):
        """Validate summary text"""
        if not v or not v.strip():
            raise ValueError("Summary cannot be empty")
        return v.strip()


class ZoomRecordingInfo(BaseModel):
    """Information about a Zoom cloud recording"""
    meeting_id: str = Field(..., description="Zoom meeting ID")
    meeting_uuid: str = Field(..., description="Zoom meeting UUID")
    recording_id: str = Field(..., description="Zoom recording ID")
    topic: str = Field(..., description="Meeting topic")
    start_time: datetime = Field(..., description="Meeting start time")
    duration: int = Field(..., description="Duration in minutes")
    total_size: int = Field(..., description="Total recording size in bytes")
    recording_count: int = Field(..., description="Number of recording files")
    recording_files: List[Dict] = Field(default_factory=list, description="Individual recording files")
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class ProcessingJob(BaseModel):
    """Background processing job for recordings"""
    job_id: str = Field(..., description="Unique job identifier")
    recording_id: str = Field(..., description="Associated recording ID")
    job_type: str = Field(..., description="Type of processing job")
    status: str = Field(default="pending", description="Job status")
    progress: int = Field(default=0, description="Progress percentage (0-100)", ge=0, le=100)
    result: Optional[Dict[str, Any]] = Field(None, description="Job result data")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    started_at: Optional[datetime] = Field(None, description="When job started")
    completed_at: Optional[datetime] = Field(None, description="When job completed")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When job was created")
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
    
    @validator('job_type')
    def validate_job_type(cls, v):
        """Validate job type"""
        valid_types = ['transcription', 'summary', 'action_items', 'upload']
        if v not in valid_types:
            raise ValueError(f"Job type must be one of: {valid_types}")
        return v


class RecordingFilter(BaseModel):
    """Filter parameters for recording queries"""
    user_id: Optional[str] = Field(None, description="Filter by user ID")
    source: Optional[RecordingSource] = Field(None, description="Filter by recording source")
    status: Optional[ProcessingStatus] = Field(None, description="Filter by processing status")
    date_from: Optional[datetime] = Field(None, description="Filter recordings from this date")
    date_to: Optional[datetime] = Field(None, description="Filter recordings up to this date")
    search_term: Optional[str] = Field(None, description="Search in title and transcription")
    limit: int = Field(default=50, description="Maximum number of results", ge=1, le=100)
    offset: int = Field(default=0, description="Number of results to skip", ge=0)
    
    class Config:
        use_enum_values = True


class RecordingResponse(BaseModel):
    """Response model for recording API endpoints"""
    recordings: List[Recording] = Field(..., description="List of recordings")
    total: int = Field(..., description="Total number of recordings")
    limit: int = Field(..., description="Limit used in query")
    offset: int = Field(..., description="Offset used in query")
    has_more: bool = Field(..., description="Whether there are more results")
    
    @validator('has_more', always=True)
    def calculate_has_more(cls, v, values):
        """Calculate if there are more results"""
        total = values.get('total', 0)
        limit = values.get('limit', 0)
        offset = values.get('offset', 0)
        return total > offset + limit


class UploadProgress(BaseModel):
    """File upload progress information"""
    upload_id: str = Field(..., description="Unique upload identifier")
    file_name: str = Field(..., description="Name of the file being uploaded")
    file_size: int = Field(..., description="Total file size in bytes")
    bytes_uploaded: int = Field(default=0, description="Bytes uploaded so far")
    progress_percent: float = Field(default=0.0, description="Upload progress as percentage")
    status: str = Field(default="uploading", description="Upload status")
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Upload start time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
    
    @validator('progress_percent', always=True)
    def calculate_progress(cls, v, values):
        """Calculate progress percentage"""
        file_size = values.get('file_size', 0)
        bytes_uploaded = values.get('bytes_uploaded', 0)
        if file_size > 0:
            return min(100.0, (bytes_uploaded / file_size) * 100)
        return 0.0


# Utility functions for model validation
def validate_recording_id(recording_id: str) -> bool:
    """Validate recording ID format"""
    if not recording_id or len(recording_id) < 5:
        return False
    return True


def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """Validate file extension"""
    if not filename:
        return False
    
    extension = filename.lower().split('.')[-1] if '.' in filename else ''
    return f".{extension}" in [ext.lower() for ext in allowed_extensions]


def create_recording_id(user_id: str, timestamp: datetime = None) -> str:
    """Generate a unique recording ID"""
    if timestamp is None:
        timestamp = datetime.utcnow()
    
    return f"rec_{timestamp.strftime('%Y%m%d_%H%M%S')}_{user_id[:8]}"


def extract_meeting_info(filename: str) -> Dict[str, str]:
    """Extract meeting information from filename"""
    # Common Zoom filename patterns
    info = {
        'title': filename,
        'date': '',
        'time': ''
    }
    
    # Try to extract date/time patterns
    import re
    
    # Pattern: Meeting_YYYY-MM-DD_HH-MM-SS
    date_pattern = r'(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})'
    match = re.search(date_pattern, filename)
    
    if match:
        info['date'] = match.group(1)
        info['time'] = match.group(2).replace('-', ':')
        # Remove date/time from title
        info['title'] = re.sub(date_pattern, '', filename).strip('_-.')
    
    # Clean up title
    info['title'] = info['title'].replace('_', ' ').replace('-', ' ').strip()
    if not info['title']:
        info['title'] = 'Meeting Recording'
    
    return info 