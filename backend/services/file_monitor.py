"""
File monitoring service for Zoom recordings using watchdog
"""

import asyncio
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent

from ..config import Settings
from .storage import StorageService
from .database import DatabaseService
from ..models.recording import RecordingMetadata
from ..utils.error_handler import FileMonitorError

logger = logging.getLogger(__name__)


class ZoomRecordingHandler(FileSystemEventHandler):
    """File system event handler for Zoom recordings"""
    
    def __init__(self, file_monitor):
        self.file_monitor = file_monitor
        self.processing_files: Set[str] = set()
        
    def on_created(self, event):
        """Handle file creation events"""
        if not event.is_directory:
            asyncio.create_task(self._handle_file_event(event.src_path, "created"))
    
    def on_modified(self, event):
        """Handle file modification events"""
        if not event.is_directory:
            asyncio.create_task(self._handle_file_event(event.src_path, "modified"))
    
    async def _handle_file_event(self, file_path: str, event_type: str):
        """Handle file system events asynchronously"""
        try:
            # Avoid processing the same file multiple times
            if file_path in self.processing_files:
                return
            
            # Check if file is a supported recording format
            if not self.file_monitor._is_supported_file(file_path):
                return
            
            # Wait for file to be fully written (Zoom may still be writing)
            await self._wait_for_file_completion(file_path)
            
            # Add to processing set
            self.processing_files.add(file_path)
            
            try:
                await self.file_monitor._process_new_recording(file_path)
                logger.info(f"Successfully processed new recording: {file_path}")
            finally:
                self.processing_files.discard(file_path)
                
        except Exception as e:
            logger.error(f"Failed to handle file event for {file_path}: {str(e)}")
            self.processing_files.discard(file_path)
    
    async def _wait_for_file_completion(self, file_path: str, max_wait: int = 300):
        """
        Wait for file to be completely written
        
        Args:
            file_path: Path to the file
            max_wait: Maximum wait time in seconds
        """
        try:
            initial_size = os.path.getsize(file_path)
            wait_time = 0
            stable_count = 0
            
            while wait_time < max_wait:
                await asyncio.sleep(5)  # Check every 5 seconds
                wait_time += 5
                
                try:
                    current_size = os.path.getsize(file_path)
                    
                    if current_size == initial_size:
                        stable_count += 1
                        if stable_count >= 3:  # Stable for 15 seconds
                            break
                    else:
                        initial_size = current_size
                        stable_count = 0
                        
                except OSError:
                    # File may not be accessible yet
                    continue
            
            logger.info(f"File appears complete after {wait_time} seconds: {file_path}")
            
        except Exception as e:
            logger.error(f"Error waiting for file completion: {str(e)}")


class ZoomFileMonitor:
    """Service for monitoring Zoom recordings folder"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.storage_service = None
        self.db_service = None
        
        self.observer: Optional[Observer] = None
        self.handler: Optional[ZoomRecordingHandler] = None
        self.is_monitoring = False
        self.monitored_path: Optional[str] = None
        self.last_check: Optional[datetime] = None
        
        # Track processed files to avoid duplicates
        self.processed_files: Set[str] = set()
        
        # Statistics
        self.stats = {
            "files_processed": 0,
            "files_failed": 0,
            "start_time": None,
            "last_file_time": None
        }
    
    async def initialize(self, storage_service: StorageService, db_service: DatabaseService):
        """Initialize the file monitor with required services"""
        self.storage_service = storage_service
        self.db_service = db_service
        logger.info("File monitor initialized")
    
    async def start_monitoring(self, path: Optional[str] = None) -> bool:
        """
        Start monitoring the Zoom recordings folder
        
        Args:
            path: Optional custom path to monitor
            
        Returns:
            True if monitoring started successfully
        """
        try:
            if self.is_monitoring:
                logger.warning("File monitoring is already active")
                return True
            
            # Use provided path or settings path
            monitor_path = path or self.settings.zoom_recordings_path
            
            if not monitor_path:
                raise FileMonitorError("No Zoom recordings path configured")
            
            # Expand and validate path
            expanded_path = Path(monitor_path).expanduser().resolve()
            
            if not expanded_path.exists():
                logger.info(f"Creating monitoring directory: {expanded_path}")
                expanded_path.mkdir(parents=True, exist_ok=True)
            
            if not expanded_path.is_dir():
                raise FileMonitorError(f"Path is not a directory: {expanded_path}")
            
            # Set up file system observer
            self.observer = Observer()
            self.handler = ZoomRecordingHandler(self)
            
            self.observer.schedule(
                self.handler,
                str(expanded_path),
                recursive=True  # Monitor subdirectories too
            )
            
            self.observer.start()
            
            # Update state
            self.is_monitoring = True
            self.monitored_path = str(expanded_path)
            self.stats["start_time"] = datetime.utcnow()
            self.last_check = datetime.utcnow()
            
            # Scan for existing files
            await self._scan_existing_files(expanded_path)
            
            logger.info(f"Started monitoring Zoom recordings at: {expanded_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start file monitoring: {str(e)}")
            await self.stop_monitoring()
            raise FileMonitorError(f"Failed to start monitoring: {str(e)}")
    
    async def stop_monitoring(self):
        """Stop file monitoring"""
        try:
            if self.observer:
                self.observer.stop()
                self.observer.join(timeout=5)
                self.observer = None
            
            self.handler = None
            self.is_monitoring = False
            self.monitored_path = None
            
            logger.info("Stopped file monitoring")
            
        except Exception as e:
            logger.error(f"Error stopping file monitoring: {str(e)}")
    
    async def update_path(self, new_path: str):
        """
        Update the monitored path
        
        Args:
            new_path: New path to monitor
        """
        try:
            was_monitoring = self.is_monitoring
            
            if was_monitoring:
                await self.stop_monitoring()
            
            # Update settings
            self.settings.zoom_recordings_path = new_path
            
            if was_monitoring:
                await self.start_monitoring(new_path)
            
            logger.info(f"Updated monitoring path to: {new_path}")
            
        except Exception as e:
            logger.error(f"Failed to update monitoring path: {str(e)}")
            raise FileMonitorError(f"Failed to update path: {str(e)}")
    
    async def get_status(self) -> Dict:
        """Get monitoring status information"""
        return {
            "status": "active" if self.is_monitoring else "stopped",
            "is_active": self.is_monitoring,
            "monitored_path": self.monitored_path or "Not set",
            "last_check": self.last_check,
            "stats": self.stats.copy()
        }
    
    async def _scan_existing_files(self, path: Path):
        """
        Scan directory for existing files that haven't been processed
        
        Args:
            path: Directory path to scan
        """
        try:
            logger.info(f"Scanning for existing recordings in: {path}")
            
            existing_files = []
            
            # Walk through directory structure
            for file_path in path.rglob("*"):
                if file_path.is_file() and self._is_supported_file(str(file_path)):
                    # Check if file is recent (within last 7 days)
                    mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if datetime.utcnow() - mod_time < timedelta(days=7):
                        existing_files.append(str(file_path))
            
            logger.info(f"Found {len(existing_files)} recent recording files")
            
            # Process files in background
            for file_path in existing_files:
                if file_path not in self.processed_files:
                    asyncio.create_task(self._process_new_recording(file_path))
            
        except Exception as e:
            logger.error(f"Error scanning existing files: {str(e)}")
    
    async def _process_new_recording(self, file_path: str):
        """
        Process a new recording file
        
        Args:
            file_path: Path to the recording file
        """
        try:
            if file_path in self.processed_files:
                return
            
            logger.info(f"Processing new recording: {file_path}")
            
            # Mark as processing
            self.processed_files.add(file_path)
            
            # Extract metadata from file
            metadata = await self._extract_file_metadata(file_path)
            
            # Upload to storage
            file_url = await self._upload_recording(file_path, metadata)
            
            # Store metadata in database
            recording_metadata = RecordingMetadata(
                recording_id=metadata["recording_id"],
                user_id=metadata["user_id"],
                file_url=file_url,
                meeting_title=metadata["meeting_title"],
                file_name=metadata["file_name"],
                file_size=metadata["file_size"],
                upload_timestamp=datetime.utcnow(),
                meeting_date=metadata["meeting_date"],
                source="local_folder"
            )
            
            await self.db_service.store_recording_metadata(recording_metadata)
            
            # Update statistics
            self.stats["files_processed"] += 1
            self.stats["last_file_time"] = datetime.utcnow()
            
            logger.info(f"Successfully processed recording: {metadata['recording_id']}")
            
        except Exception as e:
            logger.error(f"Failed to process recording {file_path}: {str(e)}")
            self.stats["files_failed"] += 1
            
            # Remove from processed set to allow retry
            self.processed_files.discard(file_path)
            
            # Retry after delay
            await asyncio.sleep(60)
            if self.settings.max_retry_attempts > 0:
                asyncio.create_task(self._retry_processing(file_path, 1))
    
    async def _retry_processing(self, file_path: str, attempt: int):
        """
        Retry processing a failed file
        
        Args:
            file_path: Path to the file
            attempt: Current attempt number
        """
        try:
            if attempt > self.settings.max_retry_attempts:
                logger.error(f"Max retry attempts reached for: {file_path}")
                return
            
            logger.info(f"Retrying processing (attempt {attempt}): {file_path}")
            
            # Wait before retry
            await asyncio.sleep(self.settings.retry_delay_seconds * attempt)
            
            # Remove from processed set and retry
            self.processed_files.discard(file_path)
            await self._process_new_recording(file_path)
            
        except Exception as e:
            logger.error(f"Retry {attempt} failed for {file_path}: {str(e)}")
            
            # Schedule next retry
            if attempt < self.settings.max_retry_attempts:
                asyncio.create_task(self._retry_processing(file_path, attempt + 1))
    
    async def _extract_file_metadata(self, file_path: str) -> Dict:
        """
        Extract metadata from recording file
        
        Args:
            file_path: Path to the recording file
            
        Returns:
            Dictionary containing file metadata
        """
        try:
            path_obj = Path(file_path)
            stat = path_obj.stat()
            
            # Generate recording ID
            timestamp = datetime.fromtimestamp(stat.st_mtime)
            recording_id = f"local_{timestamp.strftime('%Y%m%d_%H%M%S')}_{path_obj.stem}"
            
            # Extract meeting title from filename or directory
            meeting_title = self._extract_meeting_title(file_path)
            
            return {
                "recording_id": recording_id,
                "user_id": "local_user",  # Default user for local files
                "file_name": path_obj.name,
                "file_size": stat.st_size,
                "meeting_title": meeting_title,
                "meeting_date": timestamp,
                "file_path": file_path
            }
            
        except Exception as e:
            logger.error(f"Failed to extract metadata from {file_path}: {str(e)}")
            raise
    
    def _extract_meeting_title(self, file_path: str) -> str:
        """
        Extract meeting title from file path
        
        Args:
            file_path: Path to the recording file
            
        Returns:
            Meeting title
        """
        try:
            path_obj = Path(file_path)
            
            # Common Zoom naming patterns
            filename = path_obj.stem
            
            # Remove common Zoom suffixes
            zoom_suffixes = ["_video", "_audio_only", "_chat", "_transcript"]
            for suffix in zoom_suffixes:
                if filename.endswith(suffix):
                    filename = filename[:-len(suffix)]
                    break
            
            # Replace underscores and hyphens with spaces
            title = filename.replace("_", " ").replace("-", " ")
            
            # Clean up multiple spaces
            title = " ".join(title.split())
            
            # If still looks like a generic name, use directory name
            if len(title) < 5 or title.isdigit():
                title = path_obj.parent.name.replace("_", " ").replace("-", " ")
            
            return title.title() if title else f"Meeting {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
        except Exception as e:
            logger.error(f"Error extracting meeting title: {str(e)}")
            return f"Meeting {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    async def _upload_recording(self, file_path: str, metadata: Dict) -> str:
        """
        Upload recording file to storage
        
        Args:
            file_path: Local file path
            metadata: File metadata
            
        Returns:
            URL of uploaded file
        """
        try:
            # Create storage path
            storage_path = f"recordings/{metadata['user_id']}/{metadata['recording_id']}/{metadata['file_name']}"
            
            # Upload file
            with open(file_path, 'rb') as file:
                file_url = await self.storage_service.upload_file_stream(
                    file, 
                    storage_path,
                    metadata['file_size']
                )
            
            logger.info(f"Uploaded recording to: {file_url}")
            return file_url
            
        except Exception as e:
            logger.error(f"Failed to upload recording {file_path}: {str(e)}")
            raise
    
    def _is_supported_file(self, file_path: str) -> bool:
        """
        Check if file is a supported recording format
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file is supported
        """
        try:
            path_obj = Path(file_path)
            extension = path_obj.suffix.lower()
            
            return extension in self.settings.supported_file_extensions
            
        except Exception:
            return False
    
    async def force_scan(self) -> Dict:
        """
        Force a manual scan of the monitored directory
        
        Returns:
            Scan results
        """
        try:
            if not self.monitored_path:
                raise FileMonitorError("No path being monitored")
            
            path = Path(self.monitored_path)
            initial_count = self.stats["files_processed"]
            
            await self._scan_existing_files(path)
            
            # Wait a moment for processing to start
            await asyncio.sleep(2)
            
            files_found = self.stats["files_processed"] - initial_count
            
            return {
                "success": True,
                "files_found": files_found,
                "scan_time": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Force scan failed: {str(e)}")
            raise FileMonitorError(f"Scan failed: {str(e)}")
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            await self.stop_monitoring()
            self.processed_files.clear()
            logger.info("File monitor cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}") 