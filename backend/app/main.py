"""
drawio-ai 后端服务入口
基于 FastAPI 构建，提供会话管理、GLM 对话和图表操作接口
"""
from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# 加载根目录的 .env 文件
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

from app.routers import session, chat, diagram
from app.services.mcp_client import cleanup_mcp_client

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("DrawIO AI Backend 启动中...")
    yield
    # 关闭时
    logger.info("DrawIO AI Backend 关闭中...")
    await cleanup_mcp_client()
    logger.info("MCP 客户端已清理")


app = FastAPI(
    title="DrawIO AI",
    description="AI 驱动的 draw.io 绘图应用",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(session.router, prefix="/api", tags=["会话管理"])
app.include_router(chat.router, prefix="/api", tags=["AI 对话"])
app.include_router(diagram.router, prefix="/api", tags=["图表操作"])


@app.get("/")
async def root():
    """健康检查接口"""
    return {"status": "ok", "message": "DrawIO AI Backend is running"}


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}