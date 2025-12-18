"""
数据模型定义
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ChatMessage(BaseModel):
    """聊天消息"""
    role: str  # user / assistant
    content: str
    timestamp: Optional[str] = None


class SessionInfo(BaseModel):
    """会话信息"""
    session_id: str
    status: str
    created_at: str
    preview_url: Optional[str] = None
    diagram_xml: Optional[str] = None
    chat_history: List[ChatMessage] = []


class DiagramOperation(BaseModel):
    """图表操作"""
    action: str  # add / update / delete
    cell_id: str
    new_xml: Optional[str] = None


class GLMResponse(BaseModel):
    """GLM 响应"""
    action: str  # display / edit / none
    xml: Optional[str] = None
    operations: Optional[List[DiagramOperation]] = None
    reply: str
