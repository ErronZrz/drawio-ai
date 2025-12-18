"""
会话管理路由
处理用户会话的创建、查询和删除
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.session_manager import SessionManager

router = APIRouter()
session_manager = SessionManager()


class SessionResponse(BaseModel):
    """会话创建响应"""
    session_id: str
    preview_url: str
    message: str


class SessionStatusResponse(BaseModel):
    """会话状态响应"""
    session_id: str
    status: str
    created_at: str
    preview_url: Optional[str] = None


@router.post("/session", response_model=SessionResponse)
async def create_session():
    """
    创建新的绘图会话
    返回 session_id 和预览 URL
    """
    try:
        session_info = await session_manager.create_session()
        return SessionResponse(
            session_id=session_info["session_id"],
            preview_url=session_info["preview_url"],
            message="会话创建成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建会话失败: {str(e)}")


@router.get("/session/{session_id}", response_model=SessionStatusResponse)
async def get_session_status(session_id: str):
    """
    获取会话状态
    """
    session_info = await session_manager.get_session(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    return SessionStatusResponse(
        session_id=session_id,
        status=session_info.get("status", "unknown"),
        created_at=session_info.get("created_at", ""),
        preview_url=session_info.get("preview_url")
    )


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """
    删除会话
    """
    success = await session_manager.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    return {"message": "会话已删除", "session_id": session_id}
