"""
DrawIO MCP Server 客户端封装
通过 MCP 协议与 drawio-mcp-server 通信

MCP (Model Context Protocol) 是 Anthropic 提出的标准协议，
用于 AI 模型与外部工具/资源进行通信。

drawio MCP Server 通过 stdio 方式提供服务，我们使用 mcp 库进行通信。
"""
import os
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class DrawioMCPClient:
    """
    封装 drawio MCP Server 调用
    
    MCP Server 提供的能力：
    - start_session: 启动绘图会话，打开浏览器预览
    - display_diagram: 显示/替换整个图表（从 XML 创建新图）
    - edit_diagram: 编辑图表（add/update/delete 操作）
    - get_diagram: 获取当前图表 XML
    - export_diagram: 导出为 .drawio 文件
    """
    
    def __init__(self):
        # MCP Server 命令配置
        self.server_command = os.getenv("MCP_SERVER_COMMAND", "npx")
        self.server_args = os.getenv("MCP_SERVER_ARGS", "@next-ai-drawio/mcp-server@latest").split()
        
        # 会话管理
        self.sessions: Dict[str, Any] = {}
        
        # MCP 客户端状态
        self._client_session: Optional[ClientSession] = None
        self._exit_stack: Optional[AsyncExitStack] = None
        self._initialized = False
        self._lock = asyncio.Lock()
    
    async def _ensure_connected(self) -> ClientSession:
        """
        确保与 MCP Server 建立连接
        使用懒加载模式，第一次调用时建立连接
        """
        async with self._lock:
            if self._client_session is not None and self._initialized:
                return self._client_session
            
            logger.info(f"正在连接 MCP Server: {self.server_command} {' '.join(self.server_args)}")
            
            # 创建服务器参数
            server_params = StdioServerParameters(
                command=self.server_command,
                args=self.server_args,
                env=None  # 继承当前环境变量
            )
            
            # 创建退出栈管理资源
            self._exit_stack = AsyncExitStack()
            
            # 建立 stdio 连接
            stdio_transport = await self._exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            
            # 创建客户端会话
            read_stream, write_stream = stdio_transport
            self._client_session = await self._exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            
            # 初始化会话
            await self._client_session.initialize()
            self._initialized = True
            
            logger.info("MCP Server 连接成功")
            
            # 列出可用工具（用于调试）
            tools = await self._client_session.list_tools()
            logger.info(f"可用工具: {[t.name for t in tools.tools]}")
            
            return self._client_session
    
    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        调用 MCP 工具
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            
        Returns:
            工具返回结果
        """
        session = await self._ensure_connected()
        
        logger.debug(f"调用工具: {tool_name}, 参数: {json.dumps(arguments, ensure_ascii=False)[:200]}")
        
        try:
            result = await session.call_tool(tool_name, arguments)
            
            # 解析结果
            if result.content:
                # MCP 返回的 content 是一个列表
                contents = []
                for item in result.content:
                    if hasattr(item, 'text'):
                        contents.append(item.text)
                    elif hasattr(item, 'data'):
                        contents.append(item.data)
                    else:
                        contents.append(str(item))
                
                # 如果只有一个内容，直接返回
                if len(contents) == 1:
                    # 尝试解析为 JSON
                    try:
                        return json.loads(contents[0])
                    except (json.JSONDecodeError, TypeError):
                        return contents[0]
                return contents
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"调用工具 {tool_name} 失败: {e}")
            raise
    
    async def start_session(self, session_id: str) -> Dict[str, Any]:
        """
        为用户创建新的绘图会话
        
        调用 MCP Server 的 start_session 工具，会启动嵌入式服务器并打开浏览器
        
        Args:
            session_id: 会话 ID（用于本地管理）
            
        Returns:
            包含 preview_url 等信息的字典
        """
        result = await self._call_tool("start_session", {})
        
        # 解析返回的预览 URL
        preview_url = None
        if isinstance(result, str):
            # 从返回文本中提取 URL
            if "http" in result:
                import re
                urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', result)
                if urls:
                    preview_url = urls[0]
        elif isinstance(result, dict):
            preview_url = result.get("url") or result.get("preview_url")
        
        # 默认预览 URL
        if not preview_url:
            preview_url = "http://localhost:6274"
        
        # 记录会话信息
        self.sessions[session_id] = {
            "preview_url": preview_url,
            "xml": None,
            "created": True
        }
        
        logger.info(f"会话 {session_id} 已创建，预览地址: {preview_url}")
        
        return {
            "preview_url": preview_url,
            "session_id": session_id,
            "message": "会话已创建"
        }
    
    async def display_diagram(self, session_id: str, xml: str) -> bool:
        """
        显示/替换整个图表
        
        注意：这会完全替换当前图表，如果只需要添加元素，请使用 edit_diagram
        
        Args:
            session_id: 会话 ID
            xml: 有效的 draw.io/mxGraph XML 格式
            
        Returns:
            是否成功
        """
        try:
            result = await self._call_tool("display_diagram", {
                "xml": xml
            })
            
            # 更新本地缓存
            if session_id in self.sessions:
                self.sessions[session_id]["xml"] = xml
            
            logger.info(f"会话 {session_id} 图表已更新")
            return True
            
        except Exception as e:
            logger.error(f"显示图表失败: {e}")
            return False
    
    async def edit_diagram(self, session_id: str, operations: List[Dict[str, Any]]) -> bool:
        """
        编辑图表（添加/更新/删除元素）
        
        MCP Server 会先从浏览器获取最新状态，然后应用操作，
        因此用户手动修改的内容会被保留。
        
        Args:
            session_id: 会话 ID
            operations: 操作列表，每个操作包含:
                - type: "add" | "update" | "delete"
                - cell_id: 单元格 ID
                - new_xml: 新的 mxCell XML（add/update 时需要）
                
        Returns:
            是否成功
        """
        try:
            # MCP edit_diagram 工具接受 operations 数组
            result = await self._call_tool("edit_diagram", {
                "operations": operations
            })
            
            logger.info(f"会话 {session_id} 图表编辑完成，操作数: {len(operations)}")
            return True
            
        except Exception as e:
            logger.error(f"编辑图表失败: {e}")
            return False
    
    async def get_diagram(self, session_id: str) -> Optional[str]:
        """
        获取当前图表 XML
        
        从浏览器获取最新状态，包括用户手动编辑的内容
        
        Args:
            session_id: 会话 ID
            
        Returns:
            图表 XML 字符串，如果没有图表则返回 None
        """
        try:
            result = await self._call_tool("get_diagram", {})
            
            # 解析返回的 XML
            xml = None
            if isinstance(result, str):
                xml = result
            elif isinstance(result, dict):
                xml = result.get("xml") or result.get("content")
            
            # 更新本地缓存
            if xml and session_id in self.sessions:
                self.sessions[session_id]["xml"] = xml
            
            return xml
            
        except Exception as e:
            logger.error(f"获取图表失败: {e}")
            return None
    
    async def export_diagram(self, session_id: str, file_path: Optional[str] = None) -> bytes:
        """
        导出为 .drawio 文件内容
        
        Args:
            session_id: 会话 ID
            file_path: 可选的文件保存路径（MCP Server 可能会使用）
            
        Returns:
            文件内容（bytes）
        """
        try:
            # 先尝试使用 export_diagram 工具
            export_path = file_path or f"/tmp/diagram_{session_id}.drawio"
            result = await self._call_tool("export_diagram", {
                "path": export_path
            })
            
            # 如果 MCP Server 保存了文件，尝试读取
            if os.path.exists(export_path):
                with open(export_path, 'rb') as f:
                    content = f.read()
                # 清理临时文件
                if not file_path:
                    os.remove(export_path)
                return content
            
        except Exception as e:
            logger.warning(f"export_diagram 工具调用失败: {e}，尝试从 XML 生成")
        
        # 后备方案：获取 XML 并包装为 .drawio 格式
        xml = await self.get_diagram(session_id)
        
        if not xml:
            # 返回空的 drawio 文件模板
            xml = self._get_empty_diagram_xml()
        
        # 确保 XML 是有效的 .drawio 格式
        drawio_xml = self._wrap_as_drawio_file(xml)
        
        return drawio_xml.encode('utf-8')
    
    def _get_empty_diagram_xml(self) -> str:
        """获取空白图表的 XML 模板"""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="drawio-ai" modified="2024-01-01T00:00:00.000Z" agent="DrawIO AI" version="1.0.0">
  <diagram id="default" name="Page-1">
    <mxGraphModel dx="1434" dy="780" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>'''
    
    def _wrap_as_drawio_file(self, xml: str) -> str:
        """
        将 mxGraphModel XML 包装为完整的 .drawio 文件格式
        """
        # 如果已经是完整的 mxfile 格式，直接返回
        if '<mxfile' in xml:
            return xml
        
        # 如果是 mxGraphModel 格式，包装为 mxfile
        if '<mxGraphModel' in xml:
            return f'''<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="drawio-ai" modified="2024-01-01T00:00:00.000Z" agent="DrawIO AI" version="1.0.0">
  <diagram id="default" name="Page-1">
{xml}
  </diagram>
</mxfile>'''
        
        # 其他情况，尝试作为 diagram 内容
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="drawio-ai" modified="2024-01-01T00:00:00.000Z" agent="DrawIO AI" version="1.0.0">
  <diagram id="default" name="Page-1">
    <mxGraphModel dx="1434" dy="780" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
{xml}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>'''
    
    async def close(self):
        """关闭 MCP 连接"""
        async with self._lock:
            if self._exit_stack:
                await self._exit_stack.aclose()
                self._exit_stack = None
            self._client_session = None
            self._initialized = False
            logger.info("MCP 连接已关闭")
    
    async def list_available_tools(self) -> List[str]:
        """
        列出 MCP Server 提供的所有工具
        用于调试和验证连接
        """
        session = await self._ensure_connected()
        tools = await session.list_tools()
        return [tool.name for tool in tools.tools]
    
    def __del__(self):
        """析构函数，确保资源释放"""
        if self._exit_stack:
            # 注意：这里不能使用 await，所以只能记录警告
            logger.warning("DrawioMCPClient 未正确关闭，请调用 close() 方法")


# 创建全局单例
_mcp_client: Optional[DrawioMCPClient] = None


def get_mcp_client() -> DrawioMCPClient:
    """获取 MCP 客户端单例"""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = DrawioMCPClient()
    return _mcp_client


async def cleanup_mcp_client():
    """清理 MCP 客户端资源"""
    global _mcp_client
    if _mcp_client:
        await _mcp_client.close()
        _mcp_client = None