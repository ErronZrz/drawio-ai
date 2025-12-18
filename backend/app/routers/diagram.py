"""
图表操作路由
处理图表的获取、修改和导出
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, List

from app.services.session_manager import SessionManager
from app.services.mcp_client import get_mcp_client

router = APIRouter()
session_manager = SessionManager()


class DiagramXMLResponse(BaseModel):
    """图表 XML 响应"""
    session_id: str
    xml: str


class EditOperation(BaseModel):
    """编辑操作"""
    type: str  # add / update / delete
    cell_id: str
    new_xml: Optional[str] = None  # add/update 时需要


class EditDiagramRequest(BaseModel):
    """编辑图表请求"""
    operations: List[EditOperation]


@router.get("/diagram/{session_id}", response_model=DiagramXMLResponse)
async def get_diagram(session_id: str):
    """
    获取当前图表 XML
    """
    session_info = await session_manager.get_session(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    try:
        mcp_client = get_mcp_client()
        xml = await mcp_client.get_diagram(session_id)
        return DiagramXMLResponse(session_id=session_id, xml=xml or "")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图表失败: {str(e)}")


@router.post("/diagram/{session_id}/edit")
async def edit_diagram(session_id: str, request: EditDiagramRequest):
    """
    编辑图表（手动操作）
    """
    session_info = await session_manager.get_session(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    try:
        mcp_client = get_mcp_client()
        operations = [op.model_dump() for op in request.operations]
        success = await mcp_client.edit_diagram(session_id, operations)
        return {"success": success, "message": "图表已更新"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"编辑图表失败: {str(e)}")


@router.get("/diagram/{session_id}/download")
async def download_diagram(session_id: str):
    """
    下载 .drawio 文件
    """
    session_info = await session_manager.get_session(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    try:
        mcp_client = get_mcp_client()
        file_content = await mcp_client.export_diagram(session_id)
        
        return Response(
            content=file_content,
            media_type="application/xml",
            headers={
                "Content-Disposition": f"attachment; filename=diagram_{session_id}.drawio"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出图表失败: {str(e)}")
