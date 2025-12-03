from fastapi import APIRouter, Depends
from models.session import get_db, MongoDBClient
from datetime import datetime

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(db: MongoDBClient = Depends(get_db)):
    """
    Health check endpoint to verify API and database connectivity
    """
    # Check MongoDB connection
    mongodb_status = "connected"
    try:
        # Ping the database to check connection
        db.client.admin.command("ping")
    except Exception as e:
        mongodb_status = f"disconnected: {str(e)}"

    return {
        "status": "healthy" if "connected" in mongodb_status else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api": "operational",
            "mongodb": mongodb_status,
            "gridfs": "operational" if db.fs else "unavailable",
        },
    }
