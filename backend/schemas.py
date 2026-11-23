from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

class UserCreate(BaseModel):
    clerk_id: str
    email: str

class UserResponse(BaseModel):
    id: str
    clerk_id: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True

class JobCreate(BaseModel):
    user_id: str
    job_type: str

class JobResponse(BaseModel):
    id: str
    user_id: str
    job_type: str
    status: str
    progress_percent: int
    current_stage: str
    created_at: datetime

    class Config:
        from_attributes = True