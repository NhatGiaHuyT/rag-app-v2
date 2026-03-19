from typing import Any, Dict, List

from pydantic import BaseModel


class AnalyticsPoint(BaseModel):
    label: str
    value: int


class UserAnalyticsResponse(BaseModel):
    summary: Dict[str, int]
    activity: List[AnalyticsPoint]
    recent_feedback: List[Dict[str, Any]]


class AdminOverviewResponse(BaseModel):
    summary: Dict[str, int]
    activity: List[AnalyticsPoint]
    top_users: List[Dict[str, Any]]
    frequent_topics: List[Dict[str, Any]]
    peak_hours: List[Dict[str, Any]]
    feedback_summary: Dict[str, int]
    document_effectiveness: List[Dict[str, Any]]
