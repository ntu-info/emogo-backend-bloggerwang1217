[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/e7FBMwSa)
[![Open in Visual Studio Code](https://classroom.github.com/assets/open-in-vscode-2e0aaae1b6195c2367325f4f02e2d04e9abb55f0b24a779b69b11b9e10269abc.svg)](https://classroom.github.com/online_ide?assignment_repo_id=21875569&assignment_repo_type=AssignmentRepo)

# I'm Emo Now Backend API

FastAPI backend for the "I'm Emo Now" emotion tracking mobile application. This API handles emotion session management, GPS tracking, and video storage using MongoDB and GridFS.

The frontend mobile app is available here: https://github.com/bloggerwang1217/I-m-emo-now

This app allows users to directly upload emotion metadata and videos to this backend API.

## API Endpoints

Please checkout the links here:

- For API information: https://bloggermandolin.com/im-emo-now/docs
- For the export/download dashboard: https://bloggermandolin.com/im-emo-now/dashboard

### Health & Info
- `GET /` - API information and available endpoints
- `GET /health` - Check API and database connectivity

### Sessions Management
- `POST /api/sessions` - Create a new emotion session
- `GET /api/sessions` - Get all sessions for a device (query: `device_id`, `limit`, `skip`)
- `GET /api/sessions/{session_id}` - Get a specific session
- `DELETE /api/sessions/{session_id}` - Delete a session and its video

### Video Upload & Download
- `POST /api/sessions/{session_id}/video` - Upload video file for a session
- `GET /api/sessions/{session_id}/video` - Download video file for a session

### Data Export
- `GET /api/sessions/export/csv` - Export sessions as CSV (optional filter: `device_id`)
- `GET /dashboard` - Dashboard page with statistics
- `GET /dashboard/export` - Export all sessions data as CSV
- `GET /dashboard/download` - Download all videos as ZIP file

## Features

- 📱 Device-based session tracking (no registration required)
- 😊 Emotion score recording (1-5 scale)
- 📍 GPS location tracking
- 🎥 Video upload and storage via MongoDB GridFS
- 📊 CSV data export
- 🔄 RESTful API design
- 🗑️ Automatic data retention (90 days TTL)

## Tech Stack

- **Framework**: FastAPI 0.104.1
- **Database**: MongoDB with GridFS
- **Server**: Uvicorn
- **Validation**: Pydantic 2.5.0

## Project Structure

```
backend/
├── main.py                 # Application entry point
├── config.py              # Configuration management
├── models/
│   ├── __init__.py
│   └── session.py         # MongoDB models and client
├── routes/
│   ├── __init__.py
│   ├── health.py          # Health check endpoint
│   └── sessions.py        # Session API routes
├── requirements.txt
└── .env                   # Environment variables (not in git)
```

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd emogo-backend
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

Copy `.env.example` to `.env` and update with your MongoDB connection string:

```bash
cp .env.example .env
```

Edit `.env`:
```env
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/emo_now
MONGODB_DATABASE=emo_now
```

### 4. Run the server

```bash
# Development mode (with auto-reload)
python main.py

# Or using uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

See the **API Endpoints** section above for a complete list of available routes.

### Example: Create Session

```bash
curl -X POST "http://localhost:8000/api/sessions" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "550e8400-e29b-41d4-a716-446655440000",
    "emotion_score": 4,
    "latitude": 25.0330,
    "longitude": 121.5654,
    "timestamp": "2024-12-02T12:00:00Z"
  }'
```

### Example: Upload Video

```bash
curl -X POST "http://localhost:8000/api/sessions/{session_id}/video" \
  -F "video=@/path/to/video.mp4"
```

## MongoDB Setup

### Option 1: MongoDB Atlas (Cloud - Recommended)

1. Create account at https://www.mongodb.com/cloud/atlas
2. Create a free cluster
3. Create database user
4. Configure network access (allow from anywhere for development)
5. Get connection string and update `.env`

### Option 2: Local MongoDB

1. Install MongoDB: https://www.mongodb.com/try/download/community
2. Start MongoDB service
3. Use connection string: `mongodb://localhost:27017`

## Deployment

### Deploy on Render

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set environment variables in Render dashboard:
   - `MONGODB_URL`
   - `MONGODB_DATABASE`
4. Render will automatically detect and deploy

Start Command:
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Deploy on Other Platforms

The application can be deployed on any platform that supports Python:
- Heroku
- Railway
- Fly.io
- DigitalOcean App Platform
- AWS/GCP/Azure

## Configuration

Key configuration options in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGODB_URL` | MongoDB connection string | `mongodb://localhost:27017` |
| `MONGODB_DATABASE` | Database name | `emo_now` |
| `MAX_VIDEO_SIZE` | Max video file size in bytes | `104857600` (100MB) |
| `CORS_ORIGINS` | Allowed CORS origins | `*` |
| `DATA_RETENTION_DAYS` | Auto-delete after N days | `90` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |

## Security Considerations

⚠️ **Current limitations** (suitable for research/development):
- No user authentication
- Open CORS policy (accepts all origins)
- No rate limiting by default

For production deployment, consider:
- Implementing API key authentication
- Restricting CORS origins
- Adding rate limiting middleware
- Using HTTPS/TLS
- Regular security audits

## Data Retention

Sessions are automatically deleted after 90 days (configurable via `DATA_RETENTION_DAYS`). This is implemented using MongoDB TTL indexes on the `created_at` field.

## Troubleshooting

### Cannot connect to MongoDB
- Verify `MONGODB_URL` is correct
- Check network access settings in MongoDB Atlas
- Ensure database user has proper permissions

### Video upload fails
- Check file size doesn't exceed `MAX_VIDEO_SIZE`
- Verify file type is MP4, QuickTime, or AVI
- Ensure MongoDB has sufficient storage space

### Port already in use
- Change `PORT` in `.env` to use a different port
- Or kill the process using the port: `lsof -ti:8000 | xargs kill`

## Development

### Running tests
```bash
# TODO: Add test suite
pytest
```

### Code formatting
```bash
black .
```

### Type checking
```bash
mypy .
```

## License

MIT License - see LICENSE file for details

## Support

For issues and questions, please open an issue on GitHub.