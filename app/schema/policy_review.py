from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.enums import ReviewStatus


class PolicyReviewBase(BaseModel):
    status: ReviewStatus = ReviewStatus.pending
    comments: Optional[str] = None


class PolicyReviewCreate(PolicyReviewBase):
    policy_id: int
    reviewer_id: int


class PolicyReviewUpdate(BaseModel):
    status: Optional[ReviewStatus] = None
    comments: Optional[str] = None
    reviewed_at: Optional[datetime] = None


class PolicyReview(PolicyReviewBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    policy_id: int
    reviewer_id: Optional[int]
    reviewed_at: Optional[datetime]
    created_at: datetime
