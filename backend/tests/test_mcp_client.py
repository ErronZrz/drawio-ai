#!/usr/bin/env python3
"""
MCP 客户端测试模块
用于验证与 drawio MCP Server 的通信是否正常工作

测试前提：
1. 已安装 Node.js 和 npm (用于 npx 命令)
2. 已安装 mcp Python 库: pip install mcp
3. MCP Server: @next-ai-drawio/mcp-server@latest (自动通过 npx 安装)

运行方式：
    cd backend
    python -m tests.test_mcp_client

或者运行特定测试：
    python -m tests.test_mcp_client --test connection
    python -m tests.test_mcp_client --test display
    python -m tests.test_mcp_client --test all
"""
import os
import sys
import asyncio
import argparse
import logging
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 测试用的示例 XML
SAMPLE_FLOWCHART_XML = '''<mxGraphModel dx="1434" dy="780" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169" math="0" shadow="0">
  <root>
    <mxCell id="0" />
    <mxCell id="1" parent="0" />
    <mxCell id="start-1" value="开始" style="ellipse;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="1">
      <mxGeometry x="200" y="80" width="80" height="40" as="geometry" />
    </mxCell>
    <mxCell id="process-1" value="处理数据" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
      <mxGeometry x="180" y="160" width="120" height="60" as="geometry" />
    </mxCell>
    <mxCell id="end-1" value="结束" style="ellipse;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;" vertex="1" parent="1">
      <mxGeometry x="200" y="260" width="80" height="40" as="geometry" />
    </mxCell>
    <mxCell id="edge-1" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;" edge="1" parent="1" source="start-1" target="process-1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="edge-2" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;" edge="1" parent="1" source="process-1" target="end-1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
  </root>
</mxGraphModel>'''

SAMPLE_ADD_CELL_XML = '''<mxCell id="decision-1" value="是否继续?" style="rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;" vertex="1" parent="1">
  <mxGeometry x="175" y="350" width="130" height="80" as="geometry" />
</mxCell>'''


class MCPClientTester:
    """MCP 客户端测试类"""
    
    def __init__(self):
        self.client = None
        self.test_session_id = f"test-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.results = {}
    
    async def setup(self):
        """初始化测试环境"""
        from app.services.mcp_client import DrawioMCPClient
        self.client = DrawioMCPClient()
        print("\n" + "=" * 60)
        print("MCP 客户端测试")
        print("=" * 60)
        print(f"测试会话 ID: {self.test_session_id}")
        print()
    
    async def teardown(self):
        """清理测试环境"""
        if self.client:
            await self.client.close()
            print("\n✓ MCP 连接已关闭")
    
    async def test_connection(self) -> bool:
        """
        测试 1: 连接测试
        验证能否成功连接到 MCP Server
        """
        print("\n" + "-" * 40)
        print("测试 1: MCP Server 连接测试")
        print("-" * 40)
        
        try:
            # 尝试列出可用工具
            tools = await self.client.list_available_tools()
            
            print(f"✓ 连接成功!")
            print(f"✓ 可用工具数量: {len(tools)}")
            print(f"✓ 工具列表: {tools}")
            
            # 验证必要的工具是否存在
            required_tools = ['start_session', 'display_diagram', 'edit_diagram', 'get_diagram', 'export_diagram']
            missing_tools = [t for t in required_tools if t not in tools]
            
            if missing_tools:
                print(f"⚠️ 警告: 缺少工具: {missing_tools}")
            else:
                print(f"✓ 所有必要工具都可用")
            
            self.results['connection'] = True
            return True
            
        except Exception as e:
            print(f"✗ 连接失败: {e}")
            print()
            print("可能的原因:")
            print("  1. drawio MCP Server 未安装")
            print("  2. npx 命令不可用")
            print("  3. MCP 服务器配置错误")
            print()
            print("解决方案:")
            print("  - 确保已安装 Node.js 和 npm")
            print("  - 设置环境变量 MCP_SERVER_COMMAND 和 MCP_SERVER_ARGS")
            self.results['connection'] = False
            return False
    
    async def test_start_session(self) -> bool:
        """
        测试 2: 启动会话测试
        验证能否成功创建绘图会话
        """
        print("\n" + "-" * 40)
        print("测试 2: 启动会话测试")
        print("-" * 40)
        
        try:
            result = await self.client.start_session(self.test_session_id)
            
            print(f"✓ 会话创建成功!")
            print(f"✓ 会话 ID: {result.get('session_id')}")
            print(f"✓ 预览 URL: {result.get('preview_url')}")
            
            # 验证返回结构
            if 'preview_url' in result:
                print(f"✓ 返回结构正确")
            
            self.results['start_session'] = True
            return True
            
        except Exception as e:
            print(f"✗ 启动会话失败: {e}")
            self.results['start_session'] = False
            return False
    
    async def test_display_diagram(self) -> bool:
        """
        测试 3: 显示图表测试
        验证能否成功显示/替换整个图表
        """
        print("\n" + "-" * 40)
        print("测试 3: 显示图表测试")
        print("-" * 40)
        
        try:
            success = await self.client.display_diagram(
                self.test_session_id, 
                SAMPLE_FLOWCHART_XML
            )
            
            if success:
                print(f"✓ 图表显示成功!")
                print(f"✓ 已渲染包含 {SAMPLE_FLOWCHART_XML.count('mxCell')} 个单元格的流程图")
                self.results['display_diagram'] = True
                return True
            else:
                print(f"✗ 图表显示返回失败")
                self.results['display_diagram'] = False
                return False
                
        except Exception as e:
            print(f"✗ 显示图表失败: {e}")
            self.results['display_diagram'] = False
            return False
    
    async def test_get_diagram(self) -> bool:
        """
        测试 4: 获取图表测试
        验证能否成功获取当前图表 XML
        """
        print("\n" + "-" * 40)
        print("测试 4: 获取图表测试")
        print("-" * 40)
        
        try:
            xml = await self.client.get_diagram(self.test_session_id)
            
            if xml:
                print(f"✓ 获取图表成功!")
                print(f"✓ XML 长度: {len(xml)} 字符")
                
                # 简单验证 XML 结构
                if 'mxCell' in xml or 'mxGraphModel' in xml:
                    print(f"✓ XML 格式有效")
                else:
                    print(f"⚠️ 警告: XML 可能格式不正确")
                
                # 显示 XML 预览
                preview = xml[:300] + "..." if len(xml) > 300 else xml
                print(f"\nXML 预览:")
                print("-" * 30)
                print(preview)
                print("-" * 30)
                
                self.results['get_diagram'] = True
                return True
            else:
                print(f"✗ 获取到的 XML 为空")
                self.results['get_diagram'] = False
                return False
                
        except Exception as e:
            print(f"✗ 获取图表失败: {e}")
            self.results['get_diagram'] = False
            return False
    
    async def test_edit_diagram(self) -> bool:
        """
        测试 5: 编辑图表测试
        验证能否成功添加/更新/删除元素
        """
        print("\n" + "-" * 40)
        print("测试 5: 编辑图表测试")
        print("-" * 40)
        
        try:
            # 测试添加操作
            operations = [
                {
                    "type": "add",
                    "cell_id": "decision-1",
                    "new_xml": SAMPLE_ADD_CELL_XML
                }
            ]
            
            success = await self.client.edit_diagram(self.test_session_id, operations)
            
            if success:
                print(f"✓ 编辑图表成功!")
                print(f"✓ 已添加决策节点 (decision-1)")
                
                # 验证添加是否生效
                xml = await self.client.get_diagram(self.test_session_id)
                if xml and 'decision-1' in xml:
                    print(f"✓ 验证: 新节点已添加到图表中")
                
                self.results['edit_diagram'] = True
                return True
            else:
                print(f"✗ 编辑图表返回失败")
                self.results['edit_diagram'] = False
                return False
                
        except Exception as e:
            print(f"✗ 编辑图表失败: {e}")
            self.results['edit_diagram'] = False
            return False
    
    async def test_export_diagram(self) -> bool:
        """
        测试 6: 导出图表测试
        验证能否成功导出 .drawio 文件
        """
        print("\n" + "-" * 40)
        print("测试 6: 导出图表测试")
        print("-" * 40)
        
        try:
            content = await self.client.export_diagram(self.test_session_id)
            
            if content:
                print(f"✓ 导出成功!")
                print(f"✓ 文件大小: {len(content)} 字节")
                
                # 验证文件格式
                content_str = content.decode('utf-8')
                if '<mxfile' in content_str:
                    print(f"✓ 文件格式正确 (.drawio)")
                elif '<mxGraphModel' in content_str:
                    print(f"✓ 文件包含有效的图表数据")
                
                # 保存测试文件（可选）
                test_file = f"/tmp/test_export_{self.test_session_id}.drawio"
                with open(test_file, 'wb') as f:
                    f.write(content)
                print(f"✓ 测试文件已保存: {test_file}")
                
                self.results['export_diagram'] = True
                return True
            else:
                print(f"✗ 导出内容为空")
                self.results['export_diagram'] = False
                return False
                
        except Exception as e:
            print(f"✗ 导出图表失败: {e}")
            self.results['export_diagram'] = False
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        await self.setup()
        
        try:
            # 按顺序运行测试（有依赖关系）
            tests = [
                ('connection', self.test_connection),
                ('start_session', self.test_start_session),
                ('display_diagram', self.test_display_diagram),
                ('get_diagram', self.test_get_diagram),
                ('edit_diagram', self.test_edit_diagram),
                ('export_diagram', self.test_export_diagram),
            ]
            
            for name, test_func in tests:
                success = await test_func()
                if not success and name == 'connection':
                    print("\n⚠️ 连接失败，跳过后续测试")
                    break
            
            # 输出测试汇总
            self.print_summary()
            
        finally:
            await self.teardown()
    
    async def run_single_test(self, test_name: str):
        """运行单个测试"""
        await self.setup()
        
        try:
            test_map = {
                'connection': self.test_connection,
                'start_session': self.test_start_session,
                'display': self.test_display_diagram,
                'get': self.test_get_diagram,
                'edit': self.test_edit_diagram,
                'export': self.test_export_diagram,
            }
            
            if test_name not in test_map:
                print(f"未知测试: {test_name}")
                print(f"可用测试: {list(test_map.keys())}")
                return
            
            # 如果不是连接测试，先确保连接
            if test_name != 'connection':
                await self.test_connection()
                if test_name in ['display', 'get', 'edit', 'export']:
                    await self.test_start_session()
                if test_name in ['get', 'edit', 'export']:
                    await self.test_display_diagram()
            
            await test_map[test_name]()
            
        finally:
            await self.teardown()
    
    def print_summary(self):
        """打印测试汇总"""
        print("\n" + "=" * 60)
        print("测试汇总")
        print("=" * 60)
        
        total = len(self.results)
        passed = sum(1 for v in self.results.values() if v)
        failed = total - passed
        
        for name, result in self.results.items():
            status = "✓ 通过" if result else "✗ 失败"
            print(f"  {name}: {status}")
        
        print("-" * 40)
        print(f"总计: {total} 个测试, {passed} 个通过, {failed} 个失败")
        
        if failed == 0:
            print("\n✅ 所有测试通过! MCP 客户端工作正常。")
        else:
            print(f"\n⚠️ 有 {failed} 个测试失败，请检查配置和日志。")


async def interactive_demo():
    """
    交互式演示模式
    逐步演示 MCP 客户端的各项功能
    """
    from app.services.mcp_client import DrawioMCPClient
    
    print("\n" + "=" * 60)
    print("MCP 客户端交互式演示")
    print("=" * 60)
    print("\n这个演示将逐步展示 drawio MCP Server 的各项功能。")
    print("请在每一步后查看浏览器中的图表变化。\n")
    
    client = DrawioMCPClient()
    session_id = f"demo-{datetime.now().strftime('%H%M%S')}"
    
    try:
        # Step 1: 连接
        input("按 Enter 开始连接 MCP Server...")
        print("\n正在连接...")
        tools = await client.list_available_tools()
        print(f"✓ 连接成功! 可用工具: {tools}\n")
        
        # Step 2: 创建会话
        input("按 Enter 创建绘图会话（将打开浏览器）...")
        print("\n正在创建会话...")
        result = await client.start_session(session_id)
        print(f"✓ 会话已创建!")
        print(f"  预览 URL: {result['preview_url']}")
        print("\n请在浏览器中查看空白画布。\n")
        
        # Step 3: 显示图表
        input("按 Enter 显示示例流程图...")
        print("\n正在渲染图表...")
        await client.display_diagram(session_id, SAMPLE_FLOWCHART_XML)
        print("✓ 图表已显示!")
        print("\n请在浏览器中查看流程图（开始 → 处理数据 → 结束）。\n")
        
        # Step 4: 添加元素
        input("按 Enter 添加决策节点...")
        print("\n正在添加节点...")
        await client.edit_diagram(session_id, [{
            "type": "add",
            "cell_id": "decision-demo",
            "new_xml": SAMPLE_ADD_CELL_XML
        }])
        print("✓ 决策节点已添加!")
        print("\n请在浏览器中查看新添加的菱形节点。\n")
        
        # Step 5: 获取 XML
        input("按 Enter 获取当前图表 XML...")
        print("\n正在获取...")
        xml = await client.get_diagram(session_id)
        print(f"✓ 获取成功! XML 长度: {len(xml) if xml else 0} 字符\n")
        
        # Step 6: 导出
        input("按 Enter 导出 .drawio 文件...")
        print("\n正在导出...")
        content = await client.export_diagram(session_id)
        export_file = f"/tmp/demo_{session_id}.drawio"
        with open(export_file, 'wb') as f:
            f.write(content)
        print(f"✓ 文件已导出: {export_file}")
        print(f"  文件大小: {len(content)} 字节\n")
        
        print("=" * 60)
        print("演示完成!")
        print("=" * 60)
        
    finally:
        await client.close()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='MCP 客户端测试工具')
    parser.add_argument(
        '--test', '-t',
        choices=['all', 'connection', 'start_session', 'display', 'get', 'edit', 'export'],
        default='all',
        help='要运行的测试 (默认: all)'
    )
    parser.add_argument(
        '--demo', '-d',
        action='store_true',
        help='运行交互式演示'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细日志'
    )
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 运行测试
    tester = MCPClientTester()
    
    if args.demo:
        asyncio.run(interactive_demo())
    elif args.test == 'all':
        asyncio.run(tester.run_all_tests())
    else:
        asyncio.run(tester.run_single_test(args.test))


if __name__ == "__main__":
    main()
