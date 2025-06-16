"""
Zoom OAuth authentication service
"""

import asyncio
import base64
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import httpx
import logging
from urllib.parse import urlencode

from .config import Settings
from .utils.error_handler import AuthenticationError, ZoomAPIError

logger = logging.getLogger(__name__)


class ZoomAuth:
    """Zoom OAuth authentication service"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client_id = settings.zoom_client_id
        self.client_secret = settings.zoom_client_secret
        self.redirect_uri = settings.zoom_redirect_uri
        self.oauth_url = settings.zoom_oauth_url
        self.base_url = settings.zoom_base_url
        
        # OAuth granular scopes for recording access (Updated March 2024)
        self.scopes = [
            "cloud_recording:read:list_user_recordings:admin",     # List user recordings
            "cloud_recording:read:list_recording_files:admin",     # List recording files
            "cloud_recording:read:recording:admin",                # Read recording data
            "cloud_recording:read:list_account_recordings:admin",  # List account recordings
            "user:read:user:admin",                                # Read user info
            "meeting:read:meeting:admin"                           # Read meeting info
        ]
        
        # Store for OAuth states (in production, use Redis or database)
        self._oauth_states: Dict[str, Dict] = {}
    
    async def get_authorization_url(self, redirect_uri: Optional[str] = None) -> Tuple[str, str]:
        """
        Generate Zoom OAuth authorization URL
        
        Args:
            redirect_uri: Optional custom redirect URI
            
        Returns:
            Tuple of (authorization_url, state)
        """
        try:
            # Generate secure random state
            state = secrets.token_urlsafe(32)
            
            # Store state with timestamp for validation
            self._oauth_states[state] = {
                "created_at": datetime.utcnow(),
                "redirect_uri": redirect_uri or self.redirect_uri
            }
            
            # Build authorization URL
            params = {
                "response_type": "code",
                "client_id": self.client_id,
                "redirect_uri": redirect_uri or self.redirect_uri,
                "state": state,
                "scope": " ".join(self.scopes)
            }
            
            auth_url = f"{self.oauth_url}/authorize?{urlencode(params)}"
            
            logger.info(f"Generated Zoom OAuth URL with state: {state}")
            return auth_url, state
            
        except Exception as e:
            logger.error(f"Failed to generate authorization URL: {str(e)}")
            raise AuthenticationError("Failed to generate authorization URL")
    
    async def exchange_code_for_token(self, code: str, state: str) -> Dict:
        """
        Exchange OAuth code for access token
        
        Args:
            code: OAuth authorization code
            state: OAuth state parameter
            
        Returns:
            Dictionary containing token data
        """
        try:
            # Validate state
            if not self._validate_state(state):
                raise AuthenticationError("Invalid or expired OAuth state")
            
            # Get redirect URI from stored state
            stored_state = self._oauth_states.get(state, {})
            redirect_uri = stored_state.get("redirect_uri", self.redirect_uri)
            
            # Prepare token exchange request
            auth_header = base64.b64encode(
                f"{self.client_id}:{self.client_secret}".encode()
            ).decode()
            
            headers = {
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri
            }
            
            # Make token exchange request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.oauth_url}/token",
                    headers=headers,
                    data=data,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Zoom token exchange failed: {response.status_code} - {response.text}")
                    raise ZoomAPIError(f"Token exchange failed: {response.status_code}")
                
                token_data = response.json()
            
            # Add expiration timestamp
            expires_in = token_data.get("expires_in", 3600)
            token_data["expires_at"] = datetime.utcnow() + timedelta(seconds=expires_in)
            token_data["created_at"] = datetime.utcnow()
            
            # Clean up used state
            self._oauth_states.pop(state, None)
            
            logger.info("Successfully exchanged OAuth code for access token")
            return token_data
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Failed to exchange OAuth code: {str(e)}")
            raise AuthenticationError("Failed to exchange authorization code")
    
    async def refresh_access_token(self, refresh_token: str) -> Dict:
        """
        Refresh expired access token
        
        Args:
            refresh_token: OAuth refresh token
            
        Returns:
            Dictionary containing new token data
        """
        try:
            auth_header = base64.b64encode(
                f"{self.client_id}:{self.client_secret}".encode()
            ).decode()
            
            headers = {
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.oauth_url}/token",
                    headers=headers,
                    data=data,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Zoom token refresh failed: {response.status_code} - {response.text}")
                    raise ZoomAPIError(f"Token refresh failed: {response.status_code}")
                
                token_data = response.json()
            
            # Add expiration timestamp
            expires_in = token_data.get("expires_in", 3600)
            token_data["expires_at"] = datetime.utcnow() + timedelta(seconds=expires_in)
            token_data["refreshed_at"] = datetime.utcnow()
            
            logger.info("Successfully refreshed access token")
            return token_data
            
        except Exception as e:
            logger.error(f"Failed to refresh access token: {str(e)}")
            raise AuthenticationError("Failed to refresh access token")
    
    async def validate_token(self, access_token: str) -> bool:
        """
        Validate access token by making a test API call
        
        Args:
            access_token: Zoom access token
            
        Returns:
            True if token is valid, False otherwise
        """
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/users/me",
                    headers=headers,
                    timeout=10.0
                )
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Token validation failed: {str(e)}")
            return False
    
    async def get_user_info(self, access_token: str) -> Dict:
        """
        Get user information from Zoom API
        
        Args:
            access_token: Zoom access token
            
        Returns:
            Dictionary containing user information
        """
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/users/me",
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    raise ZoomAPIError(f"Failed to get user info: {response.status_code}")
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Failed to get user info: {str(e)}")
            raise ZoomAPIError("Failed to retrieve user information")
    
    async def get_recordings(self, access_token: str, user_id: str = "me", 
                           from_date: Optional[str] = None, 
                           to_date: Optional[str] = None) -> Dict:
        """
        Get user's cloud recordings from Zoom
        
        Args:
            access_token: Zoom access token
            user_id: User ID (default: "me" for current user)
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            
        Returns:
            Dictionary containing recordings data
        """
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            params = {"page_size": 300}  # Maximum page size
            
            if from_date:
                params["from"] = from_date
            if to_date:
                params["to"] = to_date
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/users/{user_id}/recordings",
                    headers=headers,
                    params=params,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    raise ZoomAPIError(f"Failed to get recordings: {response.status_code}")
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Failed to get recordings: {str(e)}")
            raise ZoomAPIError("Failed to retrieve recordings")
    
    async def is_token_expired(self, token_data: Dict) -> bool:
        """
        Check if access token is expired
        
        Args:
            token_data: Token data dictionary
            
        Returns:
            True if token is expired, False otherwise
        """
        try:
            if "expires_at" not in token_data:
                return True
            
            expires_at = token_data.get("expires_at")
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            
            # Add 5 minute buffer for clock skew
            return datetime.utcnow() + timedelta(minutes=5) >= expires_at
            
        except Exception as e:
            logger.error(f"Failed to check token expiration: {str(e)}")
            return True
    
    def _validate_state(self, state: str) -> bool:
        """
        Validate OAuth state parameter
        
        Args:
            state: OAuth state to validate
            
        Returns:
            True if state is valid, False otherwise
        """
        try:
            if state not in self._oauth_states:
                return False
            
            stored_state = self._oauth_states[state]
            created_at = stored_state.get("created_at")
            
            # State expires after 10 minutes
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at)
            
            if datetime.utcnow() - created_at > timedelta(minutes=10):
                self._oauth_states.pop(state, None)
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"State validation failed: {str(e)}")
            return False
    
    async def cleanup_expired_states(self):
        """Clean up expired OAuth states"""
        try:
            current_time = datetime.utcnow()
            expired_states = []
            
            for state, data in self._oauth_states.items():
                created_at = data.get("created_at")
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at)
                
                if current_time - created_at > timedelta(minutes=10):
                    expired_states.append(state)
            
            for state in expired_states:
                self._oauth_states.pop(state, None)
            
            if expired_states:
                logger.info(f"Cleaned up {len(expired_states)} expired OAuth states")
                
        except Exception as e:
            logger.error(f"Failed to cleanup expired states: {str(e)}")


# Periodic cleanup task
async def start_state_cleanup_task(zoom_auth: ZoomAuth, interval: int = 300):
    """
    Start periodic cleanup of expired OAuth states
    
    Args:
        zoom_auth: ZoomAuth instance
        interval: Cleanup interval in seconds (default: 5 minutes)
    """
    while True:
        try:
            await asyncio.sleep(interval)
            await zoom_auth.cleanup_expired_states()
        except Exception as e:
            logger.error(f"State cleanup task failed: {str(e)}")
            await asyncio.sleep(60)  # Wait 1 minute before retrying 