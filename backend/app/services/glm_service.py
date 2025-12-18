"""
智谱 GLM 服务封装
处理与 GLM API 的对话，生成绘图指令
"""
import os
import json
import re
from typing import Dict, Any, List, Optional, AsyncGenerator


# GLM 系统提示词 - 优化版本
SYSTEM_PROMPT = """# 角色设定

你是 **DrawIO AI 助手**，一个专业、友好、乐于助人的 AI 伙伴。你不仅能帮助用户创建各种精美的图表，还能进行日常对话交流、回答问题、提供建议。

## 核心能力

1. **自然对话**：像朋友一样与用户聊天，回答各种问题
2. **图表专家**：精通流程图、架构图、思维导图、UML 图、组织架构图等各类图表的设计与生成
3. **智能理解**：准确理解用户意图，区分"闲聊"与"画图需求"
4. **迭代优化**：支持对图表进行增量修改和持续优化

## 行为准则

### 判断用户意图

**需要生成/修改图表的情况**：
- 用户明确说"画"、"创建"、"生成"、"做一个"等动词 + 图表类型
- 用户描述了具体的流程、结构、关系需要可视化
- 用户要求修改、添加、删除当前图表中的元素
- 用户说"帮我把 XXX 画出来"

**纯对话交流的情况**：
- 用户打招呼、寒暄
- 用户询问你的能力、问候
- 用户提问知识性问题（非图表相关）
- 用户表达感谢、告别
- 用户的问题不涉及任何可视化需求

### 对话风格

- 友好亲切，使用自然的中文表达
- 对于图表需求，先确认理解是否正确，再生成
- 生成图表后，简要说明你做了什么，并询问是否需要调整
- 如果用户需求不够清晰，主动询问细节

---

# 输出格式规范

你必须始终返回一个有效的 JSON 对象，格式如下：

## 1. 创建新图表

当用户需要创建全新图表时，使用 `display` 动作：

```json
{
  "action": "display",
  "xml": "<完整的 mxGraphModel XML 代码>",
  "reply": "你的自然语言回复，解释你创建了什么"
}
```

## 2. 修改现有图表

当用户需要修改当前图表时，使用 `edit` 动作：

```json
{
  "action": "edit",
  "operations": [
    {"type": "add", "cell_id": "新元素的唯一ID", "new_xml": "<mxCell .../>"},
    {"type": "update", "cell_id": "要更新的元素ID", "new_xml": "<mxCell .../>"},
    {"type": "delete", "cell_id": "要删除的元素ID"}
  ],
  "reply": "你的自然语言回复，解释你做了哪些修改"
}
```

## 3. 纯对话回复

当用户只是聊天、提问，不需要图表操作时，使用 `none` 动作：

```json
{
  "action": "none",
  "reply": "你的自然语言回复"
}
```

---

# mxGraph XML 技术参考

## 基础模板

```xml
<mxGraphModel dx="1434" dy="780" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169" math="0" shadow="0">
  <root>
    <mxCell id="0" />
    <mxCell id="1" parent="0" />
    <!-- 图形元素放在这里 -->
  </root>
</mxGraphModel>
```

## 常用形状

### 矩形（基础节点）
```xml
<mxCell id="node1" value="节点文本" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="120" height="60" as="geometry"/>
</mxCell>
```

### 圆角矩形
```xml
<mxCell id="node2" value="圆角节点" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="120" height="60" as="geometry"/>
</mxCell>
```

### 椭圆（开始/结束）
```xml
<mxCell id="start" value="开始" style="ellipse;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="1">
  <mxGeometry x="100" y="40" width="80" height="40" as="geometry"/>
</mxCell>
```

### 菱形（判断/决策）
```xml
<mxCell id="decision1" value="条件判断?" style="rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;" vertex="1" parent="1">
  <mxGeometry x="100" y="150" width="100" height="80" as="geometry"/>
</mxCell>
```

### 平行四边形（输入/输出）
```xml
<mxCell id="io1" value="输入数据" style="shape=parallelogram;perimeter=parallelogramPerimeter;whiteSpace=wrap;html=1;fixedSize=1;fillColor=#e1d5e7;strokeColor=#9673a6;" vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="120" height="60" as="geometry"/>
</mxCell>
```

### 圆柱体（数据库）
```xml
<mxCell id="db1" value="数据库" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;fillColor=#f5f5f5;strokeColor=#666666;" vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="80" height="100" as="geometry"/>
</mxCell>
```

### 文档形状
```xml
<mxCell id="doc1" value="文档" style="shape=document;whiteSpace=wrap;html=1;boundedLbl=1;fillColor=#fff2cc;strokeColor=#d6b656;" vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="100" height="80" as="geometry"/>
</mxCell>
```

### 云（外部系统）
```xml
<mxCell id="cloud1" value="云服务" style="ellipse;shape=cloud;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;" vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="120" height="80" as="geometry"/>
</mxCell>
```

### 人物图标
```xml
<mxCell id="actor1" value="用户" style="shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;" vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="30" height="60" as="geometry"/>
</mxCell>
```

## 连接线

### 直线箭头
```xml
<mxCell id="edge1" style="edgeStyle=none;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=classic;" edge="1" parent="1" source="源ID" target="目标ID">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

### 正交连线（折线）
```xml
<mxCell id="edge2" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=classic;" edge="1" parent="1" source="源ID" target="目标ID">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

### 带标签的连线
```xml
<mxCell id="edge3" value="是" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=classic;" edge="1" parent="1" source="源ID" target="目标ID">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

### 虚线
```xml
<mxCell id="edge4" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;dashed=1;endArrow=classic;" edge="1" parent="1" source="源ID" target="目标ID">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

## 分组容器（泳道/分区）

### 泳道
```xml
<mxCell id="swimlane1" value="部门A" style="swimlane;horizontal=0;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
  <mxGeometry x="50" y="50" width="300" height="200" as="geometry"/>
</mxCell>
```

### 分组框
```xml
<mxCell id="group1" value="模块名称" style="swimlane;fontStyle=1;align=center;verticalAlign=top;childLayout=stackLayout;horizontal=1;startSize=26;horizontalStack=0;resizeParent=1;resizeParentMax=0;resizeLast=0;collapsible=1;marginBottom=0;fillColor=#f5f5f5;strokeColor=#666666;" vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="200" height="150" as="geometry"/>
</mxCell>
```

## 常用颜色

- 蓝色系: fillColor=#dae8fc;strokeColor=#6c8ebf
- 绿色系: fillColor=#d5e8d4;strokeColor=#82b366
- 黄色系: fillColor=#fff2cc;strokeColor=#d6b656
- 红色系: fillColor=#f8cecc;strokeColor=#b85450
- 紫色系: fillColor=#e1d5e7;strokeColor=#9673a6
- 灰色系: fillColor=#f5f5f5;strokeColor=#666666
- 橙色系: fillColor=#ffe6cc;strokeColor=#d79b00

## 布局建议

1. **水平间距**：节点之间保持 40-60px
2. **垂直间距**：层级之间保持 80-100px
3. **对齐**：同一层级的节点应水平或垂直对齐
4. **起始位置**：通常从 (100, 50) 或 (150, 50) 开始
5. **标准尺寸**：
   - 矩形节点：120x60
   - 椭圆（开始/结束）：80x40
   - 菱形（判断）：100x80
   - 数据库：80x100

---

# 示例对话

**用户**: 你好！
**回复**: {"action": "none", "reply": "你好！我是 DrawIO AI 助手 👋 我可以帮你创建各种图表，比如流程图、架构图、思维导图等。有什么我可以帮你的吗？"}

**用户**: 帮我画一个用户登录流程图
**回复**: {"action": "display", "xml": "<完整XML>", "reply": "我为你创建了一个用户登录流程图，包含以下步骤：\\n1. 开始 → 输入账号密码\\n2. 验证凭据（判断）\\n3. 成功则进入主页，失败则提示错误\\n\\n需要我调整任何部分吗？"}

**用户**: 把"验证凭据"改成"身份认证"
**回复**: {"action": "edit", "operations": [{"type": "update", "cell_id": "verify", "new_xml": "<mxCell ...value=身份认证.../>"}], "reply": "好的，我已经把"验证凭据"改成了"身份认证"。还有其他需要修改的地方吗？"}

---

# 重要提醒

1. **始终返回有效 JSON**：不要在 JSON 外添加任何文字
2. **ID 唯一性**：每个元素的 id 必须唯一且有意义（如 start、step1、decision1）
3. **连线完整性**：edge 必须指定有效的 source 和 target
4. **布局美观**：合理安排元素位置，避免重叠
5. **中文友好**：节点文本使用清晰的中文
6. **回复自然**：reply 字段要用自然、友好的语言

现在，请根据用户的消息，返回合适的 JSON 响应。
"""


# 智谱 Coding 套餐专用 Base URL
GLM_BASE_URL = "https://open.bigmodel.cn/api/coding/paas/v4"


class GLMService:
    """智谱 GLM API 封装（使用 OpenAI 兼容接口）"""
    
    def __init__(self):
        self.api_key = os.getenv("GLM_API_KEY", "")
        self.model = os.getenv("GLM_MODEL", "GLM-4.6")
        self.base_url = os.getenv("GLM_BASE_URL", GLM_BASE_URL)
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """初始化 GLM 客户端（OpenAI 兼容接口）"""
        if self.api_key:
            try:
                from openai import OpenAI
                import httpx
                # 创建带超时的 HTTP 客户端，禁用代理以避免 whistle 等代理工具干扰
                http_client = httpx.Client(
                    timeout=60.0,
                    proxy=None,  # 显式禁用代理
                    trust_env=False  # 不读取环境变量中的代理设置
                )
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                    http_client=http_client
                )
                print(f"[GLMService] 已连接到: {self.base_url}")
                print(f"[GLMService] 使用模型: {self.model}")
            except ImportError as e:
                print(f"[Warning] OpenAI 或 httpx 包未安装: {e}")
    
    def _build_messages(
        self, 
        user_message: str, 
        history: List[Dict[str, str]] = None,
        current_diagram_xml: str = None
    ) -> List[Dict[str, str]]:
        """构建对话消息列表"""
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # 添加历史消息
        if history:
            for msg in history:
                # 兼容 Pydantic 对象和字典两种格式
                if hasattr(msg, 'role'):
                    role = msg.role
                    content = msg.content
                else:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                messages.append({
                    "role": role,
                    "content": content
                })
        
        # 构建当前消息
        current_content = user_message
        if current_diagram_xml:
            current_content = f"""当前图表 XML：
```xml
{current_diagram_xml}
```

用户需求：{user_message}"""
        
        messages.append({"role": "user", "content": current_content})
        
        return messages
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """解析 GLM 响应，提取 JSON 结构"""
        # 尝试直接解析
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass
        
        # 尝试从 markdown 代码块中提取
        json_pattern = r'```(?:json)?\s*([\s\S]*?)```'
        matches = re.findall(json_pattern, response_text)
        
        for match in matches:
            try:
                return json.loads(match.strip())
            except json.JSONDecodeError:
                continue
        
        # 如果无法解析，返回纯文本响应
        return {
            "action": "none",
            "reply": response_text
        }
    
    async def chat(
        self,
        user_message: str,
        history: List[Dict[str, str]] = None,
        current_diagram_xml: str = None
    ) -> Dict[str, Any]:
        """
        与 GLM 对话，返回绘图指令
        
        Args:
            user_message: 用户消息
            history: 对话历史
            current_diagram_xml: 当前图表 XML
            
        Returns:
            {
                "action": "display" | "edit" | "none",
                "xml": "...",           # display 时
                "operations": [...],     # edit 时
                "reply": "..."          # 回复文本
            }
        """
        if not self.client:
            # 返回模拟响应（开发测试用）
            return self._mock_response(user_message)
        
        messages = self._build_messages(user_message, history, current_diagram_xml)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=4096
            )
            
            response_text = response.choices[0].message.content
            return self._parse_response(response_text)
        
        except Exception as e:
            return {
                "action": "none",
                "reply": f"抱歉，处理请求时出错：{str(e)}"
            }
    
    async def chat_stream(
        self,
        user_message: str,
        history: List[Dict[str, str]] = None,
        current_diagram_xml: str = None
    ) -> AsyncGenerator[str, None]:
        """
        流式对话
        
        Yields:
            JSON 格式的响应片段
        """
        if not self.client:
            yield json.dumps({"type": "text", "content": "GLM 客户端未初始化"})
            return
        
        messages = self._build_messages(user_message, history, current_diagram_xml)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=4096,
                stream=True
            )
            
            full_content = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_content += content
                    yield json.dumps({"type": "text", "content": content})
            
            # 最后发送完整的解析结果
            result = self._parse_response(full_content)
            yield json.dumps({"type": "complete", "result": result})
        
        except Exception as e:
            yield json.dumps({"type": "error", "message": str(e)})
    
    def _mock_response(self, user_message: str) -> Dict[str, Any]:
        """模拟响应（开发测试用）- 智能对话版"""
        msg_lower = user_message.lower()
        
        # 问候语
        if any(kw in msg_lower for kw in ["你好", "hello", "hi", "嗨", "早上好", "下午好", "晚上好"]):
            return {
                "action": "none",
                "reply": "你好！👋 我是 DrawIO AI 助手，很高兴见到你！我可以帮你创建各种图表，比如流程图、架构图、思维导图等。也可以和你聊聊天。有什么我可以帮你的吗？"
            }
        
        # 感谢
        if any(kw in msg_lower for kw in ["谢谢", "感谢", "thanks", "thank you"]):
            return {
                "action": "none",
                "reply": "不客气！😊 如果你还需要创建或修改图表，随时告诉我。祝你工作顺利！"
            }
        
        # 询问能力
        if any(kw in msg_lower for kw in ["你能做什么", "你会什么", "能力", "功能", "帮我什么"]):
            return {
                "action": "none",
                "reply": "我可以帮你做这些事情：\n\n📊 **图表创建**\n- 流程图：展示业务流程、操作步骤\n- 架构图：系统架构、技术栈\n- 思维导图：头脑风暴、知识整理\n- UML 图：类图、时序图、用例图\n- 组织架构图：团队结构\n\n💬 **日常对话**\n- 回答问题\n- 提供建议\n\n试试说「帮我画一个用户登录流程图」开始吧！"
            }
        
        # 流程图
        if any(kw in msg_lower for kw in ["流程图", "流程", "步骤"]):
            return {
                "action": "display",
                "xml": '''<mxGraphModel dx="1434" dy="780" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169" math="0" shadow="0">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    <mxCell id="start" value="开始" style="ellipse;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="1">
      <mxGeometry x="340" y="40" width="80" height="40" as="geometry"/>
    </mxCell>
    <mxCell id="step1" value="步骤 1" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
      <mxGeometry x="320" y="120" width="120" height="60" as="geometry"/>
    </mxCell>
    <mxCell id="decision1" value="条件判断?" style="rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;" vertex="1" parent="1">
      <mxGeometry x="330" y="220" width="100" height="80" as="geometry"/>
    </mxCell>
    <mxCell id="step2" value="步骤 2" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
      <mxGeometry x="320" y="340" width="120" height="60" as="geometry"/>
    </mxCell>
    <mxCell id="end" value="结束" style="ellipse;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;" vertex="1" parent="1">
      <mxGeometry x="340" y="440" width="80" height="40" as="geometry"/>
    </mxCell>
    <mxCell id="arrow1" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=classic;" edge="1" parent="1" source="start" target="step1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="arrow2" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=classic;" edge="1" parent="1" source="step1" target="decision1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="arrow3" value="是" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=classic;" edge="1" parent="1" source="decision1" target="step2">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="arrow4" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=classic;" edge="1" parent="1" source="step2" target="end">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
  </root>
</mxGraphModel>''',
                "reply": "我为你创建了一个基础流程图模板 🎨\n\n包含以下元素：\n- ✅ 开始/结束节点\n- 📦 处理步骤\n- 🔀 条件判断\n\n你可以告诉我具体的业务内容，我来帮你完善图表。比如说「把步骤1改成用户登录」。"
            }
        
        # 架构图
        if any(kw in msg_lower for kw in ["架构图", "架构", "系统图"]):
            return {
                "action": "display",
                "xml": '''<mxGraphModel dx="1434" dy="780" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169" math="0" shadow="0">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    <mxCell id="client" value="客户端" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
      <mxGeometry x="320" y="40" width="120" height="60" as="geometry"/>
    </mxCell>
    <mxCell id="gateway" value="API 网关" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="1">
      <mxGeometry x="320" y="140" width="120" height="60" as="geometry"/>
    </mxCell>
    <mxCell id="service1" value="服务 A" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;" vertex="1" parent="1">
      <mxGeometry x="180" y="260" width="100" height="60" as="geometry"/>
    </mxCell>
    <mxCell id="service2" value="服务 B" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;" vertex="1" parent="1">
      <mxGeometry x="330" y="260" width="100" height="60" as="geometry"/>
    </mxCell>
    <mxCell id="service3" value="服务 C" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;" vertex="1" parent="1">
      <mxGeometry x="480" y="260" width="100" height="60" as="geometry"/>
    </mxCell>
    <mxCell id="db" value="数据库" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;fillColor=#f5f5f5;strokeColor=#666666;" vertex="1" parent="1">
      <mxGeometry x="340" y="380" width="80" height="100" as="geometry"/>
    </mxCell>
    <mxCell id="e1" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=classic;" edge="1" parent="1" source="client" target="gateway">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="e2" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=classic;" edge="1" parent="1" source="gateway" target="service1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="e3" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=classic;" edge="1" parent="1" source="gateway" target="service2">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="e4" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=classic;" edge="1" parent="1" source="gateway" target="service3">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="e5" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=classic;dashed=1;" edge="1" parent="1" source="service2" target="db">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
  </root>
</mxGraphModel>''',
                "reply": "我为你创建了一个微服务架构图模板 🏗️\n\n当前结构：\n- 👤 客户端\n- 🚪 API 网关\n- ⚙️ 三个微服务\n- 🗄️ 数据库\n\n你可以告诉我你的实际系统组件，我来帮你调整！"
            }
        
        # 思维导图
        if any(kw in msg_lower for kw in ["思维导图", "脑图", "mind"]):
            return {
                "action": "display",
                "xml": '''<mxGraphModel dx="1434" dy="780" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169" math="0" shadow="0">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    <mxCell id="center" value="中心主题" style="ellipse;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;fontStyle=1;fontSize=14;" vertex="1" parent="1">
      <mxGeometry x="330" y="200" width="100" height="60" as="geometry"/>
    </mxCell>
    <mxCell id="branch1" value="分支 1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
      <mxGeometry x="140" y="100" width="100" height="40" as="geometry"/>
    </mxCell>
    <mxCell id="branch2" value="分支 2" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="1">
      <mxGeometry x="520" y="100" width="100" height="40" as="geometry"/>
    </mxCell>
    <mxCell id="branch3" value="分支 3" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;" vertex="1" parent="1">
      <mxGeometry x="140" y="320" width="100" height="40" as="geometry"/>
    </mxCell>
    <mxCell id="branch4" value="分支 4" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;" vertex="1" parent="1">
      <mxGeometry x="520" y="320" width="100" height="40" as="geometry"/>
    </mxCell>
    <mxCell id="l1" style="edgeStyle=none;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=none;curved=1;" edge="1" parent="1" source="center" target="branch1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="l2" style="edgeStyle=none;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=none;curved=1;" edge="1" parent="1" source="center" target="branch2">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="l3" style="edgeStyle=none;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=none;curved=1;" edge="1" parent="1" source="center" target="branch3">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="l4" style="edgeStyle=none;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=none;curved=1;" edge="1" parent="1" source="center" target="branch4">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
  </root>
</mxGraphModel>''',
                "reply": "我为你创建了一个思维导图模板 🧠\n\n包含一个中心主题和四个分支，你可以告诉我：\n- 中心主题是什么？\n- 需要哪些分支？\n\n我会帮你完善内容！"
            }
        
        # 默认：引导用户
        return {
            "action": "none",
            "reply": f"我理解了你的需求 💭\n\n不过为了更好地帮你创建图表，能否告诉我更多细节？比如：\n\n- 📊 想要什么类型的图？（流程图/架构图/思维导图/组织架构图...）\n- 📝 图表需要包含哪些内容？\n\n或者你可以直接说「帮我画一个XXX图」，我来帮你生成！"
        }