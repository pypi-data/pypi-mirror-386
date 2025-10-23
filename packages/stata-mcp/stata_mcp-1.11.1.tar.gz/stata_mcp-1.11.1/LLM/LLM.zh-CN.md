# Stata-MCP - AI 助手项目介绍

## 🎯 项目概述

Stata-MCP 是一个基于 MCP (Model Context Protocol) 协议的 Stata 统计分析助手，让 AI 能够帮助用户完成回归分析和数据统计任务。项目通过提供标准化的工具和接口，使 AI 能够理解、生成和执行 Stata 代码。

**核心价值**: 让 LLM 能够像专业的统计分析师一样使用 Stata 进行数据分析。

## 🏗️ 项目架构

### 主要模块结构
```
stata-mcp/
├── src/stata_mcp/
│   ├── __init__.py              # 主模块入口，MCP 服务器配置
│   ├── core/                    # 核心功能模块
│   │   ├── data_info/           # 数据文件分析 (CSV, DTA)
│   │   ├── rag/                 # RAG (检索增强生成) 系统
│   │   └── stata/               # Stata 相关核心功能
│   │       ├── stata_controller/ # Stata 控制器
│   │       ├── stata_do/        # Stata 执行器
│   │       └── stata_finder/    # Stata 安装查找器
│   ├── utils/                   # 工具类模块
│   │   ├── Installer/          # 安装器
│   │   ├── Prompt/             # 提示词管理
│   │   └── usable.py           # 可用性检查
│   ├── cli/                    # 命令行接口
│   ├── mode/                   # 不同操作模式
│   │   ├── langchain_agent.py  # LangChain 基础的代理模式
│   │   └── pmp/                # 基于提示词的模式
│   ├── agent_as_tool/          # 代理作为工具集成
│   ├── evaluate/               # LLM 评估模块
│   └── sandbox/                # 沙箱环境
│       ├── core/               # 沙箱核心
│       └── jupyter_manager/    # Jupyter 内核管理
├── agent_examples/             # 代理模式示例
│   ├── openai/                 # OpenAI 代理示例
│   ├── langchain/              # LangChain 代理示例
│   └── task_prompt/            # 任务提示词示例
├── main.py                     # 应用入口
└── pyproject.toml             # 项目配置
```

### 核心功能组件

1. **StataFinder** (`src/stata_mcp/core/stata/stata_finder/`): 跨平台 Stata 安装检测
   - macOS: 通过系统路径查找
   - Windows: 通过注册表和程序文件查找
   - Linux: 支持自定义路径配置

2. **StataController** (`src/stata_mcp/core/stata/stata_controller/`): Stata 进程控制
   - 命令执行管理
   - 会话状态维护
   - 错误处理机制

3. **StataDo** (`src/stata_mcp/core/stata/stata_do/`): Do 文件执行器
   - 跨平台 do 文件执行
   - 日志文件管理
   - 结果输出处理

4. **Prompt 管理系统** (`src/stata_mcp/utils/Prompt/`): AI 提示词管理
   - 多语言支持 (中英文)
   - 角色定义和策略提示
   - 动态提示词生成

5. **代理模式** (`src/stata_mcp/mode/`): 自主分析代理
   - `langchain_agent.py`: LangChain 基础的代理框架
   - `pmp/`: 基于提示词的代理模式
   - 多轮对话支持

6. **代理作为工具** (`src/stata_mcp/agent_as_tool/`): 工具集成
   - `StataAgent`: 可嵌入的 Stata 代理
   - 与其他代理框架集成
   - 自定义模型配置

7. **评估模块** (`src/stata_mcp/evaluate/`): LLM 性能评估
   - 自动评分系统
   - 质量评估工具
   - 基准评估框架

8. **RAG 系统** (`src/stata_mcp/core/rag/`): 知识检索
   - 文档索引和搜索
   - 上下文感知响应生成
   - 统计知识库

## 🛠️ 如何使用

### 基础配置

在 AI 客户端配置文件中添加:
```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": ["stata-mcp"]
    }
  }
}
```

### 核心工具函数

AI 可以通过以下工具与 Stata 交互:

1. **`stata_do(dofile_path, is_read_log=True)`** - 执行 Stata do 文件
2. **`write_dofile(content)`** - 写入 Stata 代码到 do 文件
3. **`append_dofile(original_dofile_path, content)`** - 追加代码到现有 do 文件
4. **`get_data_info(data_path, vars_list=None, encoding="utf-8")`** - 获取数据文件信息
5. **`ssc_install(command, is_replace=True)`** - 安装 SSC 包
6. **`help(cmd)`** - 获取 Stata 命令帮助
7. **`mk_dir(path)`** - 创建目录
8. **`load_figure(figure_path)`** - 加载图表
9. **`read_file(file_path, encoding="utf-8")`** - 读取文件内容

### 代理模式使用

#### 交互式代理模式
```bash
# 运行代理模式，提供交互式界面
stata-mcp --agent

# 或使用 uvx
uvx stata-mcp --agent
```

#### 代理作为工具集成
```python
from agents import Agent, Runner
from stata_mcp.agent_as_tool import StataAgent

# 初始化 Stata 代理
stata_agent = StataAgent()
sa_tool = stata_agent.as_tool()

# 创建包含 Stata 工具的主代理
agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant",
    tools=[sa_tool],
)

# 运行代理
async def main(task: str):
    result = await Runner.run(agent, input=task)
    return result
```

### 评估系统

项目包含全面的 LLM 评估系统：
- **自动评分**: 评估分析质量和准确性
- **基准测试**: 标准化评估数据集
- **性能指标**: 响应时间、准确性、完整性
- **对比分析**: 模型性能比较

### RAG 集成

知识检索功能：
- **文档搜索**: 查找相关统计文献
- **上下文感知**: 提供领域特定上下文
- **知识库**: 精选的统计方法和示例

### 提示词系统

项目内置了专业的提示词模板:
- `stata_assistant_role()` - Stata 助手角色定义
- `stata_analysis_strategy()` - Stata 分析策略指南

## 🧩 代码贡献指南

### 开发环境设置

1. 克隆项目:
```bash
git clone https://github.com/sepinetam/stata-mcp.git
cd stata-mcp
```

2. 安装依赖:
```bash
uv sync
```

3. 运行测试:
```bash
uv run pytest tests/
```

### 代码规范

- **类型标注**: 所有函数必须包含完整的类型标注
- **文档注释**: 每个函数都需要有详细的英文文档注释
- **命名规范**: 使用描述性变量名，遵循 PEP 8 规范
- **错误处理**: 完善的异常处理和错误信息

### 添加新功能

1. **新工具函数**: 在 `src/stata_mcp/__init__.py` 中添加 `@stata_mcp.tool()` 装饰器
2. **新提示词**: 在 `src/stata_mcp/utils/Prompt/string.py` 中添加多语言提示词
3. **平台支持**: 在对应的平台模块中添加实现

### 测试要求

- 单元测试覆盖核心功能
- 跨平台兼容性测试
- 错误场景测试

## 🌟 特色功能

### 跨平台支持
- **macOS**: 自动检测 Stata 安装路径
- **Windows**: 支持注册表查找和程序文件扫描
- **Linux**: 支持自定义路径配置

### 智能数据解析
- 支持多种数据格式 (.dta, .csv, .xlsx, .xls)
- 自动数据统计分析
- 缺失值检测和面板数据结构识别

### 专业提示词系统
- 多语言角色定义
- 统计分析策略指导
- 错误处理和调试建议

## 🔧 技术栈

- **Python 3.11+**: 核心编程语言
- **MCP Protocol**: AI 交互协议
- **LangChain**: 代理框架和工具集成
- **OpenAI Agents**: 高级代理编排
- **pandas**: 数据处理和分析
- **pexpect**: 跨平台进程控制
- **pathvalidate**: 文件路径安全验证
- **dotenv**: 环境配置管理
- **FastMCP**: 高性能 MCP 服务器框架

## 🚀 快速开始示例

```python
# AI 可以使用以下方式与 Stata-MCP 交互

# 1. 创建分析 do 文件
dofile_content = """
use "data.dta"
summarize
regress y x1 x2 x3
outreg2 using "results.txt", replace
"""

dofile_path = write_dofile(dofile_content)

# 2. 执行分析
result = stata_do(dofile_path, is_read_log=True)
print(result["log_content"])

# 3. 获取数据信息
data_info = get_data_info("data.dta")
print(data_info)
```

## 📊 项目状态

- ✅ macOS 支持 (已完成)
- ✅ Windows 支持 (已完成)
- 🔄 Linux 支持 (开发中)
- 🔄 更多 LLM 集成 (规划中)
- 🔄 性能优化 (进行中)

## 🤝 贡献方式

1. **报告问题**: 在 GitHub Issues 中提交 bug 报告或功能请求
2. **提交代码**: Fork 项目并提交 Pull Request
3. **文档改进**: 帮助完善文档和示例
4. **测试验证**: 帮助测试不同平台的兼容性

## 📞 联系方式

- **作者**: Sepine Tam (谭淞)
- **邮箱**: sepinetam@gmail.com
- **GitHub**: https://github.com/sepinetam

## 📄 许可证

Apache License 2.0 - 详见 [LICENSE](../LICENSE) 文件

---

**Stata-MCP**: 让 AI 成为你的专业统计分析师助手！