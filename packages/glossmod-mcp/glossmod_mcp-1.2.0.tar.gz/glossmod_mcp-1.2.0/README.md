# GlossModMCP - 3DM Mod API MCP 服务器

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)[![MCP](https://img.shields.io/badge/MCP-1.18+-green.svg)](https://modelcontextprotocol.io)[![Status](https://img.shields.io/badge/Status-✅%20Production%20Ready-brightgreen.svg)](#)[![License](https://img.shields.io/badge/License-MIT-blue.svg)](#)

**3DM Mod 站的  MCP 服务器**

[快速开始](#-快速开始) • [文档](#-文档导航) • [功能](#-核心功能) • [示例](#-使用示例)

</div>

---

## ✨ 项目简介

**GlossModMCP** 是一个完整的 **MCP (Model Context Protocol) 服务器实现**，为 Claude 和其他 LLM 应用提供 3DM Mod 网站的数据访问能力。


## ⚡ 快速开始 (3分钟)

### 前置条件
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) 

### 安装
```bash
pip install glossmod-mcp
```


### 更新
```bash
pip install --upgrade glossmod-mcp
```


### 配置

```json
"glossmod-mcp": {
    "type": "stdio",
    "command": "uvx",
    "args": ["glossmod-mcp"],
    "env": {
        "GLOSSMOD_API_KEY": "<YOUR_API_KEY_HERE>"
    }
}

```

