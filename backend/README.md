# Meeting Dashboard Backend - Zoom Recording Sync

A comprehensive FastAPI backend service for synchronizing Zoom recordings with Supabase/S3 storage, featuring OAuth authentication, real-time file monitoring, and automated upload processing.

## Features

- 🎥 **Zoom OAuth Integration**: Complete OAuth 2.0 flow with recording:read permissions
- 📁 **Real-time File Monitoring**: Python watchdog-based monitoring of local Zoom folder
- 🚀 **FastAPI REST API**: Modern async API with automatic documentation
- 💾 **Dual Storage Support**: Supabase Storage or AWS S3 compatibility
- 🗄️ **PostgreSQL Database**: Comprehensive metadata storage with Supabase
- 🔄 **Background Processing**: Async upload processing with retry logic
- 🛡️ **Error Handling**: Robust error handling with circuit breakers
- 📝 **Type Safety**: Full Pydantic model validation
- 🔧 **Configuration Management**: Environment-based settings

## Installation

1. **Install Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Set Up Environment Variables**
   ```bash
   cp env.example .env
   # Edit .env with your actual values
   ```

3. **Configure Zoom OAuth**
   - Create a Zoom OAuth app at https://marketplace.zoom.us/develop/create
   - Set the redirect URI to match your frontend callback
   - Copy client ID and secret to your .env file

4. **Set Up Supabase**
   - Create a Supabase project
   - Enable Storage and create a "recordings" bucket
   - Copy URL and keys to your .env file

## Environment Variables

All configuration is managed through environment variables. See `env.example` for the complete list.

### Required Variables

```bash
# Zoom OAuth
ZOOM_CLIENT_ID=your-zoom-client-id
ZOOM_CLIENT_SECRET=your-zoom-client-secret
ZOOM_REDIRECT_URI=http://localhost:3000/auth/zoom/callback

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-key
DATABASE_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres

# Security
SECRET_KEY=your-super-secret-key-here
```

## Database Schema

The application automatically creates the following tables:

### recordings
- `recording_id` (VARCHAR, PRIMARY KEY)
- `user_id` (VARCHAR, NOT NULL)
- `file_url` (TEXT)
- `meeting_title` (VARCHAR)
- `file_name` (VARCHAR)
- `file_size` (BIGINT)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)
- `processing_status` (VARCHAR)
- `transcription_text` (TEXT)
- `summary` (TEXT)
- `action_items` (JSONB)

### zoom_tokens
- `user_id` (VARCHAR, PRIMARY KEY)
- `access_token` (TEXT)
- `refresh_token` (TEXT)
- `expires_at` (TIMESTAMP)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

## API Endpoints

### Authentication
- `POST /auth/zoom/authorize` - Initialize Zoom OAuth flow
- `POST /auth/zoom/token` - Exchange OAuth code for token
- `GET /auth/zoom/status` - Check authentication status

### Recording Management
- `POST /upload/recording` - Upload recording file
- `GET /recordings` - List recordings with pagination
- `GET /recordings/{recording_id}` - Get specific recording

### File Monitoring
- `GET /monitor/status` - Get file monitor status
- `POST /monitor/start` - Start file monitoring
- `POST /monitor/stop` - Stop file monitoring
- `PUT /monitor/path` - Update monitored path

### Health Check
- `GET /health` - Service health check

## Running the Application

### Development Mode
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## File Monitoring

The service monitors your local Zoom recordings folder (default: `~/Zoom`) for new recordings:

1. **Automatic Detection**: Detects new `.mp4`, `.m4a`, `.mp3`, `.wav`, `.webm` files
2. **Completion Waiting**: Waits for files to finish writing before processing
3. **Metadata Extraction**: Extracts meeting title and date from filenames
4. **Background Upload**: Uploads to configured storage provider
5. **Database Storage**: Stores metadata in Supabase

## Zoom OAuth Scopes

The application requests the following Zoom OAuth **granular scopes** (updated March 2024):
- `cloud_recording:read:list_user_recordings:admin` - List user recordings
- `cloud_recording:read:list_recording_files:admin` - List recording files  
- `cloud_recording:read:recording:admin` - Read recording data
- `cloud_recording:read:list_account_recordings:admin` - List account recordings
- `user:read:user:admin` - Read user information
- `meeting:read:meeting:admin` - Read meeting information

**Note:** Zoom transitioned from "Classic" scopes (like `recording:read:admin`) to "Granular" scopes in March 2024. Apps created after this date must use the granular scopes listed above.

## Error Handling

The application includes comprehensive error handling:

- **Circuit Breakers**: Prevent cascading failures
- **Retry Logic**: Automatic retry with exponential backoff
- **Token Refresh**: Automatic OAuth token refresh
- **File Validation**: Size and format validation
- **Database Resilience**: Connection pooling and recovery

## Storage Options

### Supabase Storage (Default)
- Integrated with Supabase database
- Built-in CDN and access controls
- Signed URL generation

### AWS S3
- Enterprise-grade object storage
- Configurable regions and buckets
- IAM-based access control

## Development

### Code Structure
```
backend/
├── main.py              # FastAPI application
├── config.py            # Configuration management
├── auth.py              # Zoom OAuth authentication
├── models/
│   └── recording.py     # Pydantic models
├── services/
│   ├── database.py      # Database operations
│   ├── storage.py       # File storage service
│   └── file_monitor.py  # File monitoring service
└── utils/
    └── error_handler.py # Error handling utilities
```

### Testing
```bash
cd backend
pytest
```

### Code Formatting
```bash
cd backend
black .
flake8 .
mypy .
```

## Monitoring and Logging

The application provides comprehensive logging:
- **Structured Logging**: JSON-formatted logs
- **Error Tracking**: Detailed error context
- **Performance Metrics**: Request timing and statistics
- **Health Checks**: Service status monitoring

## Security Considerations

- **OAuth State Validation**: Prevents CSRF attacks
- **Token Encryption**: Secure token storage
- **File Validation**: Prevents malicious uploads
- **CORS Configuration**: Controlled cross-origin access
- **Input Sanitization**: SQL injection prevention

## Troubleshooting

### Common Issues

1. **Zoom OAuth Fails**
   - Verify client ID and secret
   - Check redirect URI matches exactly
   - Ensure OAuth app is published

2. **File Monitor Not Working**
   - Verify ZOOM_RECORDINGS_PATH exists
   - Check file permissions
   - Ensure supported file extensions

3. **Database Connection Issues**
   - Verify DATABASE_URL format
   - Check Supabase project status
   - Ensure connection limits

4. **Upload Failures**
   - Check file size limits
   - Verify storage credentials
   - Review error logs

### Logs Location
- Development: Console output
- Production: Configured LOG_FILE path

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure code passes linting
5. Submit a pull request

## License

This project is licensed under the MIT License. 