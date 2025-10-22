# GlossModMCP - 3DM Mod API MCP 服务器

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)[![MCP](https://img.shields.io/badge/MCP-1.18+-green.svg)](https://modelcontextprotocol.io)[![Status](https://img.shields.io/badge/Status-✅%20Production%20Ready-brightgreen.svg)](#)[![License](https://img.shields.io/badge/License-MIT-blue.svg)](#)

**3DM Mod 站的  MCP 服务器**

[快速开始](#-快速开始) • [文档](#-文档导航) • [功能](#-核心功能) • [示例](#-使用示例)

</div>

---

## ✨ 项目简介

**GlossModMCP** 是一个完整的 **MCP (Model Context Protocol) 服务器实现**，为 Claude 和其他 LLM 应用提供 3DM Mod 网站的数据访问能力。

### 🎯 项目特点

- ✅ **完整实现** - 7 个工具函数 + 4 个资源端点 + 4 个提示模板
- 📚 **详尽文档** - 1500+ 行文档，覆盖快速开始到深入学习
- 🚀 **开箱即用** - 无需修改代码，直接运行
- 🔄 **异步支持** - 高效的并发处理能力
- 💡 **易于扩展** - 清晰的代码结构，便于二次开发
- 🔍 **类型安全** - 完整的类型注解和数据验证

---

## ⚡ 快速开始 (3分钟)

### 前置条件
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) 

### 配置

```json
"GlossModMCP": {
    "command": "uv",
    "args": [
        "run",
        "--with",
        "mcp[cli]",
        "mcp",
        "run",
        "server.py"
    ],
    "env": {
        "GLOSSMOD_API_KEY": "<your-api-key>"
    }
}

```

