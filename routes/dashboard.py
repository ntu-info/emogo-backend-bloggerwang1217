from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from models.session import get_db, MongoDBClient
from bson import ObjectId
import io
import csv
import zipfile
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard(
    request: Request,
    db: MongoDBClient = Depends(get_db),
):
    """
    Returns an HTML page with summary statistics and a list of sessions.
    """
    sessions_collection = db.get_sessions_collection()
    sessions = list(sessions_collection.find())
    session_count = len(sessions)
    device_count = len(sessions_collection.distinct("device_id"))

    # Convert ObjectId to string for the template
    for session in sessions:
        session['_id'] = str(session['_id'])

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "session_count": session_count,
            "device_count": device_count,
            "sessions": sessions,
        },
    )

@router.get("/export")
async def export_csv(db: MongoDBClient = Depends(get_db)):
    """
    Exports all session data as a CSV file.
    """
    sessions_collection = db.get_sessions_collection()
    sessions = sessions_collection.find()

    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(["session_id", "device_id", "timestamp", "gps_x", "gps_y", "emotion_score"])

    # Write data
    for session in sessions:
        writer.writerow([
            str(session.get("_id")),
            session.get("device_id"),
            session.get("timestamp"),
            session.get("latitude"),
            session.get("longitude"),
            session.get("emotion_score"),
        ])

    output.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=sessions_{timestamp}.csv"})

@router.get("/download")
async def download_videos(db: MongoDBClient = Depends(get_db)):
    """
    Downloads all videos as a zip file.
    """
    fs = db.get_gridfs()
    sessions_collection = db.get_sessions_collection()
    sessions_with_video = sessions_collection.find({"video_id": {"$ne": None}})

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for session in sessions_with_video:
            video_id = session.get("video_id")
            if video_id:
                try:
                    grid_out = fs.get(ObjectId(video_id))
                    filename = grid_out.filename or f"{video_id}.mp4"
                    zip_file.writestr(f"{filename}", grid_out.read())
                except Exception as e:
                    print(f"Warning: Failed to retrieve video {video_id}: {e}")

    zip_buffer.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return StreamingResponse(zip_buffer, media_type="application/zip", headers={"Content-Disposition": f"attachment; filename=videos_{timestamp}.zip"})
