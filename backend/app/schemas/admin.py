from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


class AdminUserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str = "user"
    is_active: bool = True
    is_expert: bool = False
    feature_flags: Dict[str, bool] = Field(default_factory=dict)


class AdminUserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    is_expert: Optional[bool] = None
    feature_flags: Optional[Dict[str, bool]] = None


class AdminUserSuspend(BaseModel):
    suspend_until: Optional[datetime] = None
    reason: Optional[str] = None


class AdminPasswordReset(BaseModel):
    new_password: str


class AdminUserResponse(BaseModel):
    id: int
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    role: str
    feature_flags: Dict[str, bool] = Field(default_factory=dict)
    is_active: bool
    is_superuser: bool
    is_expert: bool
    suspended_until: Optional[datetime] = None
    suspension_reason: Optional[str] = None
    knowledge_base_count: int
    chat_count: int


class AdminUserListResponse(BaseModel):
    users: List[AdminUserResponse]


class AdminDocumentUpdate(BaseModel):
    category: Optional[str] = None
    department: Optional[str] = None
    sensitivity: Optional[str] = None
    status: Optional[str] = None
    access_level: Optional[str] = None


class AdminKnowledgeBaseUpdate(BaseModel):
    category: Optional[str] = None
    department: Optional[str] = None
    sensitivity: Optional[str] = None
    visibility: Optional[str] = None
    preprocessing_config: Optional[Dict[str, Any]] = None


class ManualQAEntryCreate(BaseModel):
    question: str
    answer: str
    tags: List[str] = Field(default_factory=list)


class ManualQAEntryResponse(BaseModel):
    id: int
    question: str
    answer: str
    tags: List[str] = Field(default_factory=list)
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    id: int
    actor_user_id: Optional[int] = None
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class AccessLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    resource_type: str
    resource_id: Optional[str] = None
    action: str
    success: bool
    failure_reason: Optional[str] = None
    created_at: datetime


class SystemAlertResponse(BaseModel):
    id: int
    severity: str
    source: str
    message: str
    is_resolved: bool
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class SystemConfigUpdate(BaseModel):
    response_settings: Dict[str, Any] = Field(default_factory=dict)
    feedback_workflow: Dict[str, Any] = Field(default_factory=dict)
    integrations: Dict[str, Any] = Field(default_factory=dict)
    model_settings: Dict[str, Any] = Field(default_factory=dict)


class SystemConfigResponse(BaseModel):
    response_settings: Dict[str, Any] = Field(default_factory=dict)
    feedback_workflow: Dict[str, Any] = Field(default_factory=dict)
    integrations: Dict[str, Any] = Field(default_factory=dict)
    model_settings: Dict[str, Any] = Field(default_factory=dict)


class AdminExpertAssignmentRequest(BaseModel):
    expert_user_id: int
    assignment_note: Optional[str] = None


class AdminFlaggedAnswerResponse(BaseModel):
    feedback_id: int
    message_id: int
    chat_id: int
    chat_title: str
    question: str
    answer: str
    comment: Optional[str] = None
    created_at: str
    status: str
    requester_user_id: int
    requester_username: str
    expert_assignee_id: Optional[int] = None
    expert_assignee_name: Optional[str] = None
