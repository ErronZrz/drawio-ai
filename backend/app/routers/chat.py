"""
AI 对话路由
处理用户与 GLM 的对话，生成绘图指令
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import logging

from app.services.glm_service import GLMService
from app.services.session_manager import SessionManager
from app.services.mcp_client import get_mcp_client

logger = logging.getLogger(__name__)

router = APIRouter()
glm_service = GLMService()
session_manager = SessionManager()


class ChatMessage(BaseModel):
    """聊天消息"""
    role: str  # user / assistant
    content: str


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    history: Optional[List[ChatMessage]] = []


class ChatResponse(BaseModel):
    """聊天响应"""
    reply: str
    diagram_updated: bool
    action: Optional[str] = None  # display / edit / none


@router.post("/chat/{session_id}", response_model=ChatResponse)
async def chat_with_glm(session_id: str, request: ChatRequest):
    """
    与 GLM 进行对话，生成/修改图表
    """
    # 验证会话是否存在
    session_info = await session_manager.get_session(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    try:
        # 获取 MCP 客户端
        mcp_client = get_mcp_client()
        
        # 获取当前图表 XML（如果有）
        current_xml = await mcp_client.get_diagram(session_id)
        
        # 调用 GLM 服务
        result = await glm_service.chat(
            user_message=request.message,
            history=request.history,
            current_diagram_xml=current_xml
        )
        
        # 根据 GLM 返回的指令执行图表操作
        diagram_updated = False
        action = result.get("action", "none")
        
        logger.info(f"GLM 返回 action: {action}")
        
        if action == "display" and result.get("xml"):
            # 显示新图表
            xml = result["xml"]
            logger.info(f"准备显示图表，XML 长度: {len(xml)}")
            success = await mcp_client.display_diagram(session_id, xml)
            if success:
                diagram_updated = True
                logger.info(f"图表显示成功")
            else:
                logger.error(f"图表显示失败，MCP display_diagram 返回 False")
        elif action == "edit" and result.get("operations"):
            # 编辑现有图表
            operations = result["operations"]
            logger.info(f"准备编辑图表，操作数: {len(operations)}")
            success = await mcp_client.edit_diagram(session_id, operations)
            if success:
                diagram_updated = True
                logger.info(f"图表编辑成功")
            else:
                logger.error(f"图表编辑失败，MCP edit_diagram 返回 False")
        
        return ChatResponse(
            reply=result.get("reply", ""),
            diagram_updated=diagram_updated,
            action=action
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对话处理失败: {str(e)}")


@router.post("/chat/{session_id}/stream")
async def chat_with_glm_stream(session_id: str, request: ChatRequest):
    """
    与 GLM 进行流式对话
    """
    # 验证会话是否存在
    session_info = await session_manager.get_session(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    async def generate():
        try:
            mcp_client = get_mcp_client()
            current_xml = await mcp_client.get_diagram(session_id)
            final_result = None
            
            async for chunk in glm_service.chat_stream(
                user_message=request.message,
                history=request.history,
                current_diagram_xml=current_xml
            ):
                yield f"data: {chunk}\n\n"
                
                # 解析 chunk，获取最终结果
                try:
                    import json
                    chunk_data = json.loads(chunk)
                    if chunk_data.get("type") == "complete":
                        final_result = chunk_data.get("result")
                except:
                    pass
            
            # 流式结束后，执行图表操作
            if final_result:
                action = final_result.get("action", "none")
                diagram_updated = False
                
                if action == "display" and final_result.get("xml"):
                    xml = final_result["xml"]
                    logger.info(f"[stream] 准备显示图表，XML 长度: {len(xml)}")
                    success = await mcp_client.display_diagram(session_id, xml)
                    if success:
                        diagram_updated = True
                        logger.info("[stream] 图表显示成功")
                    else:
                        logger.error("[stream] 图表显示失败")
                        
                elif action == "edit" and final_result.get("operations"):
                    operations = final_result["operations"]
                    logger.info(f"[stream] 准备编辑图表，操作数: {len(operations)}")
                    success = await mcp_client.edit_diagram(session_id, operations)
                    if success:
                        diagram_updated = True
                        logger.info("[stream] 图表编辑成功")
                    else:
                        logger.error("[stream] 图表编辑失败")
                
                # 发送图表更新状态
                yield f"data: {{\"type\": \"diagram_status\", \"updated\": {str(diagram_updated).lower()}}}\n\n"
                
        except Exception as e:
            logger.error(f"[stream] 错误: {str(e)}")
            yield f"data: {{\"type\": \"error\", \"message\": \"{str(e)}\"}}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
