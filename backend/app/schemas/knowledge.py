from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class KnowledgeBaseBase(BaseModel):
    name: str
    description: Optional[str] = None
    visibility: str = "private"

class KnowledgeBaseCreate(KnowledgeBaseBase):
    pass

class KnowledgeBaseUpdate(KnowledgeBaseBase):
    pass

class DocumentBase(BaseModel):
    file_name: str
    file_path: str
    file_hash: str
    file_size: int
    content_type: str
    access_level: str = "inherit"


class PermissionAssignment(BaseModel):
    user_id: int
    username: str
    permission_level: str
    full_name: Optional[str] = None

class DocumentCreate(DocumentBase):
    knowledge_base_id: int

class DocumentUploadBase(BaseModel):
    file_name: str
    file_hash: str
    file_size: int
    content_type: str
    temp_path: str
    status: str = "pending"
    error_message: Optional[str] = None

class DocumentUploadCreate(DocumentUploadBase):
    knowledge_base_id: int

class DocumentUploadResponse(DocumentUploadBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProcessingTaskBase(BaseModel):
    status: str
    error_message: Optional[str] = None

class ProcessingTaskCreate(ProcessingTaskBase):
    document_id: int
    knowledge_base_id: int

class ProcessingTask(ProcessingTaskBase):
    id: int
    document_id: int
    knowledge_base_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DocumentResponse(DocumentBase):
    id: int
    knowledge_base_id: int
    created_at: datetime
    updated_at: datetime
    processing_tasks: List[ProcessingTask] = []
    permissions: List[PermissionAssignment] = []

    class Config:
        from_attributes = True

class KnowledgeBaseResponse(KnowledgeBaseBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    documents: List[DocumentResponse] = []
    permissions: List[PermissionAssignment] = []

    class Config:
        from_attributes = True

class PreviewRequest(BaseModel):
    document_ids: List[int]
    chunk_size: int = 1000
    chunk_overlap: int = 200 


class KnowledgeBasePermissionUpdate(BaseModel):
    visibility: Optional[str] = None
    user_permissions: List[int] = []
    editor_user_ids: List[int] = []


class DocumentPermissionUpdate(BaseModel):
    access_level: Optional[str] = None
    user_permissions: List[int] = []
    editor_user_ids: List[int] = []
