# Search MCP

基于FastMCP的AI模型搜索能力MCP服务，支持通过配置调用外部搜索API。

## 功能特性

- 通过OpenAI兼容格式调用Grok搜索能力
- 环境变量配置API URL和Key
- 格式化搜索结果输出
- 可扩展架构，便于添加其他搜索Provider

## 安装

```bash
pip install -e .
```

## 配置

编辑项目根目录的 `config.toml` 文件：

```toml
[debug]
enabled = false  # 发布时设为 false，开发时设为 true

[grok]
api_url = "https://cc.guda.studio/grok/v1"
api_key = "your-api-key-here"

[logging]
level = "INFO"  # 可选：DEBUG, INFO, WARNING, ERROR
dir = "logs"    # 日志目录
```

## 使用

### 作为MCP服务运行

```bash
search-mcp
```

### Claude Desktop配置

在Claude Desktop配置文件中添加：

```json
{
  "mcpServers": {
    "search": {
      "command": "search-mcp"
    }
  }
}
```

注意：所有配置均通过 `config.toml` 文件管理，无需设置环境变量。

## 项目结构

```
search_mcp/
├── config.toml                 # 配置文件
├── pyproject.toml              # 项目配置和依赖
├── README.md                   # 使用文档
└── src/
    └── search_mcp/
        ├── __init__.py         # 包初始化
        ├── config.py           # 配置加载模块
        ├── logger.py           # 日志模块
        ├── server.py           # FastMCP服务入口，定义工具
        ├── providers/          # 搜索提供商模块
        │   ├── __init__.py     # Provider包导出
        │   ├── base.py         # 抽象基类和SearchResult数据模型
        │   └── grok.py         # Grok搜索实现
        └── utils.py            # 格式化工具函数
```

## 文件功能说明

- **config.toml**: 应用配置文件（调试开关、API配置、日志配置）
- **pyproject.toml**: 项目元数据、依赖管理、构建配置
- **config.py**: 配置文件加载器（单例模式）
- **logger.py**: 日志系统初始化
- **server.py**: FastMCP服务主入口，注册web_search工具
- **providers/base.py**: 定义SearchProvider抽象基类和SearchResult数据结构
- **providers/grok.py**: 实现Grok API调用逻辑和响应解析
- **utils.py**: 提供搜索结果格式化函数

## 扩展新的搜索Provider

1. 在`providers/`目录创建新文件
2. 继承`BaseSearchProvider`
3. 实现`search()`和`get_provider_name()`方法
4. 在`server.py`中注册新的Provider

示例：

```python
from .base import BaseSearchProvider, SearchResult

class NewProvider(BaseSearchProvider):
    def get_provider_name(self) -> str:
        return "NewProvider"
    
    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        # 实现搜索逻辑
        pass
```

## 开发

安装开发依赖：

```bash
pip install -e ".[dev]"
```

## License

MIT
