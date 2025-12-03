from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse, Response
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
import io
import csv

from models.session import (
    SessionCreate,
    SessionResponse,
    get_db,
    MongoDBClient,
)
from config import settings

router = APIRouter(prefix="/api/sessions", tags=["Sessions"])


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(
    session: SessionCreate,
    db: MongoDBClient = Depends(get_db),
):
    """
    Create a new emotion tracking session with metadata

    This endpoint creates a session record with emotion score, location, and timestamp.
    Video should be uploaded separately using the video upload endpoint.
    """
    try:
        sessions_collection = db.get_sessions_collection()

        # Prepare session document
        now = datetime.utcnow().isoformat()
        session_doc = {
            "device_id": session.device_id,
            "emotion_score": session.emotion_score,
            "latitude": session.latitude,
            "longitude": session.longitude,
            "timestamp": session.timestamp,
            "video_id": None,  # Will be updated when video is uploaded
            "created_at": now,
            "updated_at": now,
        }

        # Insert into database
        result = sessions_collection.insert_one(session_doc)
        session_doc["_id"] = str(result.inserted_id)

        return SessionResponse(**session_doc)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.post("/{session_id}/video", status_code=200)
async def upload_video(
    session_id: str,
    video: UploadFile = File(...),
    db: MongoDBClient = Depends(get_db),
):
    """
    Upload video file for an existing session

    The video is stored in MongoDB GridFS and linked to the session.
    Supports MP4, QuickTime, and AVI formats up to configured size limit.
    """
    # Validate session exists
    try:
        sessions_collection = db.get_sessions_collection()
        session = sessions_collection.find_one({"_id": ObjectId(session_id)})
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    # Validate file type
    if video.content_type not in settings.ALLOWED_VIDEO_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(settings.ALLOWED_VIDEO_TYPES)}",
        )

    try:
        # Read video content
        video_content = await video.read()

        # Validate file size
        if len(video_content) > settings.MAX_VIDEO_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.MAX_VIDEO_SIZE / (1024*1024):.0f}MB",
            )

        # Store in GridFS
        fs = db.get_gridfs()
        video_id = fs.put(
            video_content,
            filename=video.filename,
            content_type=video.content_type,
            session_id=session_id,
            uploaded_at=datetime.utcnow().isoformat(),
        )

        # Update session with video_id
        sessions_collection.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$set": {
                    "video_id": str(video_id),
                    "updated_at": datetime.utcnow().isoformat(),
                }
            },
        )

        return {
            "message": "Video uploaded successfully",
            "session_id": session_id,
            "video_id": str(video_id),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload video: {str(e)}")


@router.get("", response_model=List[SessionResponse])
async def get_sessions_by_device(
    device_id: str = Query(..., description="Device ID to filter sessions"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of sessions to return"),
    skip: int = Query(0, ge=0, description="Number of sessions to skip"),
    db: MongoDBClient = Depends(get_db),
):
    """
    Retrieve all sessions for a specific device

    Returns sessions ordered by timestamp (newest first) with pagination support.
    """
    try:
        sessions_collection = db.get_sessions_collection()

        # Query sessions for device
        cursor = sessions_collection.find({"device_id": device_id}).sort("timestamp", -1).skip(skip).limit(limit)

        sessions = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            if doc.get("video_id"):
                doc["video_id"] = str(doc["video_id"])
            sessions.append(SessionResponse(**doc))

        return sessions

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve sessions: {str(e)}")


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: MongoDBClient = Depends(get_db),
):
    """
    Retrieve a specific session by ID
    """
    try:
        sessions_collection = db.get_sessions_collection()
        session = sessions_collection.find_one({"_id": ObjectId(session_id)})

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        session["_id"] = str(session["_id"])
        if session.get("video_id"):
            session["video_id"] = str(session["video_id"])

        return SessionResponse(**session)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid session ID")


@router.get("/{session_id}/video")
async def download_video(
    session_id: str,
    db: MongoDBClient = Depends(get_db),
):
    """
    Download video file for a specific session

    Returns the video file as a streaming response.
    """
    try:
        # Get session
        sessions_collection = db.get_sessions_collection()
        session = sessions_collection.find_one({"_id": ObjectId(session_id)})

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        if not session.get("video_id"):
            raise HTTPException(status_code=404, detail="No video found for this session")

        # Retrieve video from GridFS
        fs = db.get_gridfs()
        try:
            video_file = fs.get(ObjectId(session["video_id"]))
        except Exception:
            raise HTTPException(status_code=404, detail="Video file not found in storage")

        # Stream the video
        return StreamingResponse(
            io.BytesIO(video_file.read()),
            media_type=video_file.content_type or "video/mp4",
            headers={
                "Content-Disposition": f'attachment; filename="{video_file.filename}"'
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download video: {str(e)}")


@router.get("/export/csv")
async def export_sessions_csv(
    device_id: Optional[str] = Query(None, description="Filter by device ID (optional)"),
    db: MongoDBClient = Depends(get_db),
):
    """
    Export sessions data as CSV file

    Optionally filter by device_id. Returns all session metadata (excluding videos).
    """
    try:
        sessions_collection = db.get_sessions_collection()

        # Build query
        query = {}
        if device_id:
            query["device_id"] = device_id

        # Retrieve sessions
        cursor = sessions_collection.find(query).sort("timestamp", -1)

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "session_id",
            "device_id",
            "emotion_score",
            "latitude",
            "longitude",
            "timestamp",
            "has_video",
            "created_at",
        ])

        # Write data
        for session in cursor:
            writer.writerow([
                str(session["_id"]),
                session["device_id"],
                session["emotion_score"],
                session.get("latitude", ""),
                session.get("longitude", ""),
                session["timestamp"],
                "yes" if session.get("video_id") else "no",
                session["created_at"],
            ])

        # Prepare response
        output.seek(0)
        filename = f"emo_sessions_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export CSV: {str(e)}")


@router.delete("/{session_id}", status_code=200)
async def delete_session(
    session_id: str,
    db: MongoDBClient = Depends(get_db),
):
    """
    Delete a session and its associated video

    This will permanently remove the session metadata and video file from storage.
    """
    try:
        sessions_collection = db.get_sessions_collection()
        session = sessions_collection.find_one({"_id": ObjectId(session_id)})

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Delete video from GridFS if exists
        if session.get("video_id"):
            fs = db.get_gridfs()
            try:
                fs.delete(ObjectId(session["video_id"]))
            except Exception as e:
                print(f"Warning: Failed to delete video: {e}")

        # Delete session document
        sessions_collection.delete_one({"_id": ObjectId(session_id)})

        return {
            "message": "Session deleted successfully",
            "session_id": session_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")
