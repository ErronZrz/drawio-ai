#!/bin/bash

# DrawIO AI 启动脚本
# 同时启动前端和后端服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}"
echo "======================================"
echo "       DrawIO AI 启动脚本"
echo "======================================"
echo -e "${NC}"

# 检查 .env 文件
check_env() {
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        echo -e "${YELLOW}警告: .env 文件不存在${NC}"
        if [ -f "$PROJECT_ROOT/.env.example" ]; then
            echo "正在从 .env.example 创建 .env..."
            cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
            echo -e "${RED}请编辑 .env 文件，填入你的 GLM_API_KEY${NC}"
            exit 1
        fi
    fi
    
    # 检查后端 .env
    if [ ! -f "$PROJECT_ROOT/backend/.env" ]; then
        if [ -f "$PROJECT_ROOT/backend/.env.example" ]; then
            cp "$PROJECT_ROOT/backend/.env.example" "$PROJECT_ROOT/backend/.env"
        fi
        # 从根目录复制配置
        if [ -f "$PROJECT_ROOT/.env" ]; then
            cp "$PROJECT_ROOT/.env" "$PROJECT_ROOT/backend/.env"
        fi
    fi
}

# 检查依赖
check_dependencies() {
    echo -e "${BLUE}检查依赖...${NC}"
    
    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}错误: 未找到 python3${NC}"
        exit 1
    fi
    echo -e "  ${GREEN}✓${NC} Python3: $(python3 --version)"
    
    # 检查 Node.js
    if ! command -v node &> /dev/null; then
        echo -e "${RED}错误: 未找到 node${NC}"
        exit 1
    fi
    echo -e "  ${GREEN}✓${NC} Node.js: $(node --version)"
    
    # 检查 npm
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}错误: 未找到 npm${NC}"
        exit 1
    fi
    echo -e "  ${GREEN}✓${NC} npm: $(npm --version)"
    
    echo ""
}

# 启动后端
start_backend() {
    echo -e "${BLUE}启动后端服务...${NC}"
    cd "$PROJECT_ROOT/backend"
    
    # 检查虚拟环境
    if [ -d "venv" ]; then
        source venv/bin/activate
    elif [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    
    # 启动 FastAPI
    echo -e "  后端地址: ${GREEN}http://localhost:8005${NC}"
    python3 -m uvicorn app.main:app --reload --port 8005 &
    BACKEND_PID=$!
    echo -e "  后端 PID: $BACKEND_PID"
    
    cd "$PROJECT_ROOT"
}

# 启动前端
start_frontend() {
    echo -e "${BLUE}启动前端服务...${NC}"
    cd "$PROJECT_ROOT/frontend"
    
    # 检查 node_modules
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}正在安装前端依赖...${NC}"
        npm install
    fi
    
    # 启动 Vite
    echo -e "  前端地址: ${GREEN}http://localhost:3005${NC}"
    npm run dev &
    FRONTEND_PID=$!
    echo -e "  前端 PID: $FRONTEND_PID"
    
    cd "$PROJECT_ROOT"
}

# 清理函数
cleanup() {
    echo ""
    echo -e "${YELLOW}正在停止服务...${NC}"
    
    # 终止后端
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo "  后端已停止"
    fi
    
    # 终止前端
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo "  前端已停止"
    fi
    
    # 终止所有相关进程
    pkill -f "uvicorn app.main:app" 2>/dev/null || true
    pkill -f "vite" 2>/dev/null || true
    
    echo -e "${GREEN}服务已停止${NC}"
    exit 0
}

# 主流程
main() {
    # 注册清理函数
    trap cleanup SIGINT SIGTERM
    
    # 检查环境
    check_env
    check_dependencies
    
    echo ""
    
    # 启动服务
    start_backend
    sleep 2  # 等待后端启动
    start_frontend
    
    echo ""
    echo -e "${GREEN}======================================"
    echo "        服务已启动"
    echo "======================================${NC}"
    echo ""
    echo -e "  前端: ${GREEN}http://localhost:3005${NC}"
    echo -e "  后端: ${GREEN}http://localhost:8005${NC}"
    echo -e "  API 文档: ${GREEN}http://localhost:8005/docs${NC}"
    echo ""
    echo -e "${YELLOW}按 Ctrl+C 停止所有服务${NC}"
    echo ""
    
    # 等待进程
    wait
}

# 运行
main
