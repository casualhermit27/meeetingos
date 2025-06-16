"""
Database service for managing recording metadata and user data using Supabase PostgreSQL
"""

import asyncio
import asyncpg
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from supabase import create_client, Client

from ..config import Settings
from ..models.recording import RecordingMetadata, Recording
from ..utils.error_handler import DatabaseError

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for database operations using Supabase PostgreSQL"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.supabase_client: Optional[Client] = None
        self.pool: Optional[asyncpg.Pool] = None
        
        # Table names
        self.recordings_table = "recordings"
        self.users_table = "users"
        self.zoom_tokens_table = "zoom_tokens"
        self.processing_jobs_table = "processing_jobs"
    
    async def initialize(self):
        """Initialize database connections and ensure tables exist"""
        try:
            # Initialize Supabase client
            self.supabase_client = create_client(
                self.settings.supabase_url,
                self.settings.supabase_service_key
            )
            
            # Initialize PostgreSQL connection pool
            self.pool = await asyncpg.create_pool(
                self.settings.database_url,
                min_size=1,
                max_size=self.settings.db_pool_size,
                command_timeout=60
            )
            
            # Ensure tables exist
            await self._ensure_tables_exist()
            
            logger.info("Database service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise DatabaseError(f"Database initialization failed: {str(e)}")
    
    async def _ensure_tables_exist(self):
        """Ensure all required tables exist in the database"""
        try:
            async with self.pool.acquire() as conn:
                # Create recordings table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS recordings (
                        recording_id VARCHAR PRIMARY KEY,
                        user_id VARCHAR NOT NULL,
                        file_url TEXT NOT NULL,
                        meeting_title VARCHAR(500) NOT NULL,
                        file_name VARCHAR(255) NOT NULL,
                        file_size BIGINT NOT NULL,
                        upload_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        meeting_date TIMESTAMP WITH TIME ZONE NOT NULL,
                        source VARCHAR(50) DEFAULT 'upload',
                        processing_status VARCHAR(50) DEFAULT 'pending',
                        transcription_text TEXT,
                        summary TEXT,
                        action_items JSONB,
                        metadata JSONB,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """)
                
                # Create zoom_tokens table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS zoom_tokens (
                        user_id VARCHAR PRIMARY KEY,
                        access_token TEXT NOT NULL,
                        refresh_token TEXT,
                        token_type VARCHAR(50) DEFAULT 'Bearer',
                        expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                        scope TEXT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """)
                
                # Create indexes for better performance
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_recordings_user_id ON recordings(user_id)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_recordings_meeting_date ON recordings(meeting_date)")
                
            logger.info("Database tables and indexes ensured")
            
        except Exception as e:
            logger.error(f"Failed to ensure tables exist: {str(e)}")
            raise DatabaseError(f"Table creation failed: {str(e)}")
    
    async def store_recording_metadata(self, metadata: RecordingMetadata) -> bool:
        """Store recording metadata in the database"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO recordings (
                        recording_id, user_id, file_url, meeting_title, file_name,
                        file_size, upload_timestamp, meeting_date, source
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (recording_id) DO UPDATE SET
                        file_url = EXCLUDED.file_url,
                        meeting_title = EXCLUDED.meeting_title,
                        updated_at = NOW()
                """, 
                    metadata.recording_id,
                    metadata.user_id,
                    metadata.file_url,
                    metadata.meeting_title,
                    metadata.file_name,
                    metadata.file_size,
                    metadata.upload_timestamp,
                    metadata.meeting_date,
                    getattr(metadata, 'source', 'upload')
                )
            
            logger.info(f"Stored recording metadata: {metadata.recording_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store recording metadata: {str(e)}")
            raise DatabaseError(f"Failed to store recording: {str(e)}")
    
    async def get_recording(self, recording_id: str, user_id: str) -> Optional[Dict]:
        """Get a specific recording by ID and user"""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT * FROM recordings 
                    WHERE recording_id = $1 AND user_id = $2
                """, recording_id, user_id)
                
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get recording: {str(e)}")
            raise DatabaseError(f"Failed to retrieve recording: {str(e)}")
    
    async def get_user_recordings(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get recordings for a user with pagination"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT * FROM recordings 
                    WHERE user_id = $1
                    ORDER BY meeting_date DESC
                    LIMIT $2 OFFSET $3
                """, user_id, limit, offset)
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get user recordings: {str(e)}")
            raise DatabaseError(f"Failed to retrieve recordings: {str(e)}")
    
    async def update_recording_status(self, recording_id: str, status: str) -> bool:
        """Update the processing status of a recording"""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute("""
                    UPDATE recordings 
                    SET processing_status = $1, updated_at = NOW()
                    WHERE recording_id = $2
                """, status, recording_id)
                
                rows_updated = int(result.split()[-1])
                return rows_updated > 0
                
        except Exception as e:
            logger.error(f"Failed to update recording status: {str(e)}")
            raise DatabaseError(f"Failed to update status: {str(e)}")
    
    async def store_zoom_token(self, user_id: str, token_data: Dict) -> bool:
        """Store Zoom OAuth token data"""
        try:
            expires_at = token_data.get("expires_at")
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO zoom_tokens (
                        user_id, access_token, refresh_token, token_type,
                        expires_at, scope, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, NOW())
                    ON CONFLICT (user_id) DO UPDATE SET
                        access_token = EXCLUDED.access_token,
                        refresh_token = EXCLUDED.refresh_token,
                        token_type = EXCLUDED.token_type,
                        expires_at = EXCLUDED.expires_at,
                        scope = EXCLUDED.scope,
                        updated_at = NOW()
                """,
                    user_id,
                    token_data.get("access_token"),
                    token_data.get("refresh_token"),
                    token_data.get("token_type", "Bearer"),
                    expires_at,
                    token_data.get("scope")
                )
            
            logger.info(f"Stored Zoom token for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store Zoom token: {str(e)}")
            raise DatabaseError(f"Failed to store token: {str(e)}")
    
    async def get_zoom_token(self, user_id: str) -> Optional[Dict]:
        """Get Zoom token data for a user"""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT * FROM zoom_tokens WHERE user_id = $1
                """, user_id)
                
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get Zoom token: {str(e)}")
            raise DatabaseError(f"Failed to retrieve token: {str(e)}")
    
    async def close(self):
        """Close database connections"""
        try:
            if self.pool:
                await self.pool.close()
            
            logger.info("Database connections closed")
            
        except Exception as e:
            logger.error(f"Error closing database connections: {str(e)}") 