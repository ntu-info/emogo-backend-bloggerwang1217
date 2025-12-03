from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure
import gridfs
from config import settings


class PyObjectId(ObjectId):
    """Custom type for handling MongoDB ObjectId in Pydantic models"""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class SessionCreate(BaseModel):
    """Schema for creating a new session"""

    device_id: str = Field(..., description="Unique device identifier")
    emotion_score: int = Field(..., ge=1, le=5, description="Emotion score from 1 (very negative) to 5 (very positive)")
    latitude: Optional[float] = Field(None, description="GPS latitude")
    longitude: Optional[float] = Field(None, description="GPS longitude")
    timestamp: str = Field(..., description="ISO format timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": "550e8400-e29b-41d4-a716-446655440000",
                "emotion_score": 3,
                "latitude": 25.0330,
                "longitude": 121.5654,
                "timestamp": "2024-01-01T12:00:00Z",
            }
        }


class SessionResponse(BaseModel):
    """Schema for session response"""

    id: str = Field(alias="_id", description="Session ID")
    device_id: str
    emotion_score: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timestamp: str
    video_id: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "device_id": "550e8400-e29b-41d4-a716-446655440000",
                "emotion_score": 3,
                "latitude": 25.0330,
                "longitude": 121.5654,
                "timestamp": "2024-01-01T12:00:00Z",
                "video_id": "507f1f77bcf86cd799439012",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
            }
        }


class MongoDBClient:
    """MongoDB client manager with GridFS support"""

    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db = None
        self.fs: Optional[gridfs.GridFS] = None

    def connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(
                settings.MONGODB_URL,
                **settings.mongodb_client_kwargs
            )
            # Test the connection
            self.client.admin.command("ping")
            self.db = self.client[settings.MONGODB_DATABASE]
            self.fs = gridfs.GridFS(self.db)

            # Create indexes
            self._create_indexes()

            print(f"✓ Connected to MongoDB: {settings.MONGODB_DATABASE}")
            return True
        except ConnectionFailure as e:
            print(f"✗ Failed to connect to MongoDB: {e}")
            return False

    def _create_indexes(self):
        """Create necessary indexes for sessions collection"""
        sessions_collection = self.db.sessions

        # Create indexes as specified in the implementation plan
        sessions_collection.create_index([("device_id", ASCENDING)])
        sessions_collection.create_index([("timestamp", DESCENDING)])
        sessions_collection.create_index([("device_id", ASCENDING), ("timestamp", DESCENDING)])

        # TTL index for automatic data expiration (90 days)
        sessions_collection.create_index(
            [("created_at", ASCENDING)],
            expireAfterSeconds=settings.DATA_RETENTION_DAYS * 24 * 60 * 60
        )

        print("✓ Database indexes created")

    def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            print("✓ Disconnected from MongoDB")

    def get_sessions_collection(self):
        """Get sessions collection"""
        return self.db.sessions

    def get_gridfs(self) -> gridfs.GridFS:
        """Get GridFS instance for file operations"""
        return self.fs


# Global database client instance
mongodb_client = MongoDBClient()


def get_db():
    """Dependency function to get database instance"""
    return mongodb_client
