"""
会话管理服务
负责管理用户的绘图会话
"""
import uuid
from datetime import datetime
from typing import Dict, Optional, Any
import os
import logging

logger = logging.getLogger(__name__)

# TODO: 后续可替换为 Redis 存储
_sessions: Dict[str, Dict[str, Any]] = {}


class SessionManager:
    """会话管理器"""
    
    def __init__(self):
        self.base_preview_url = os.getenv("PREVIEW_BASE_URL", "http://localhost:6274")
    
    async def create_session(self) -> Dict[str, Any]:
        """
        创建新会话
        同时调用 MCP Server 启动绘图会话
        返回包含 session_id 和 preview_url 的字典
        """
        from app.services.mcp_client import get_mcp_client
        
        session_id = str(uuid.uuid4())[:8]  # 使用短 ID
        created_at = datetime.now().isoformat()
        
        # 调用 MCP Server 启动会话
        try:
            mcp_client = get_mcp_client()
            mcp_result = await mcp_client.start_session(session_id)
            preview_url = mcp_result.get("preview_url", f"{self.base_preview_url}")
            logger.info(f"MCP 会话已启动: {session_id}, 预览 URL: {preview_url}")
        except Exception as e:
            logger.warning(f"MCP 会话启动失败: {e}，使用默认预览 URL")
            preview_url = f"{self.base_preview_url}?session={session_id}"
        
        session_info = {
            "session_id": session_id,
            "status": "active",
            "created_at": created_at,
            "preview_url": preview_url,
            "diagram_xml": None,  # 当前图表 XML
            "chat_history": [],   # 对话历史
        }
        
        _sessions[session_id] = session_info
        
        return session_info
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话信息
        """
        return _sessions.get(session_id)
    
    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新会话信息
        """
        if session_id not in _sessions:
            return False
        
        _sessions[session_id].update(updates)
        return True
    
    async def delete_session(self, session_id: str) -> bool:
        """
        删除会话
        """
        if session_id not in _sessions:
            return False
        
        del _sessions[session_id]
        return True
    
    async def list_sessions(self) -> list:
        """
        列出所有会话
        """
        return list(_sessions.values())
    
    async def update_diagram_xml(self, session_id: str, xml: str) -> bool:
        """
        更新会话的图表 XML
        """
        return await self.update_session(session_id, {"diagram_xml": xml})
    
    async def add_chat_message(self, session_id: str, role: str, content: str) -> bool:
        """
        添加聊天消息到历史记录
        """
        if session_id not in _sessions:
            return False
        
        _sessions[session_id]["chat_history"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        return True
