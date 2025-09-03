from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uuid

class BaseEntity(BaseModel):
    """Base model with common fields for all entities"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When record was created")
    updated_at: Optional[datetime] = Field(default=None, description="When record was last updated")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        
    def mark_updated(self):
        """Helper method to update the updated_at timestamp"""
        self.updated_at = datetime.utcnow()