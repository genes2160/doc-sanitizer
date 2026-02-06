from pydantic import BaseModel, Field
from typing import Dict, Optional, Literal

Status = Literal["queued", "processing", "done", "failed"]

class SubmissionOut(BaseModel):
    id: str
    filename: str
    content_type: str
    status: Status
    created_at: str
    updated_at: str
    output_url: Optional[str] = None
    error: Optional[str] = None
    rating: Optional[int] = None
    rating_note: Optional[str] = None

class RateIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    note: Optional[str] = Field(default=None, max_length=500)

class ReplaceMetaOut(BaseModel):
    replaced_count: int
