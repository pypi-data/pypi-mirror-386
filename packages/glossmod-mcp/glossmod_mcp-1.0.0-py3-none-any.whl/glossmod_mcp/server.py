"""
基于 3DM Mod API 的 MCP 服务器实现。

提供对 3DM Mod 网站数据的访问，包括游戏、Mod、Minecraft 等相关功能。

cd 到工作目录并运行：
    uv run server stdio
"""

import os
from typing import Optional
import httpx
from pydantic import BaseModel

from mcp.server.fastmcp import FastMCP

# 创建 MCP 服务器
mcp = FastMCP("GlossModMCP")

# 配置
API_BASE_URL = "https://mod.3dmgame.com/api/v3"
API_KEY = os.getenv("GLOSSMOD_API_KEY", "")


# ==================== 数据模型 ====================

class Game(BaseModel):
    """游戏信息"""
    id: int
    name: str
    englishName: Optional[str] = None
    description: Optional[str] = None
    allcount: Optional[int] = None


class Mod(BaseModel):
    """Mod 信息"""
    id: int
    title: str
    author: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    gameId: Optional[int] = None


class MinecraftMod(BaseModel):
    """Minecraft Mod 信息"""
    id: int
    name: str
    author: Optional[str] = None
    description: Optional[str] = None
    modules: Optional[str] = None


# ==================== 工具函数 ====================

@mcp.tool()
async def get_games(page: int = 1, page_size: int = 20, search: Optional[str] = None, 
                   game_type: Optional[str] = None, sort_by: str = "allcount", 
                   sort_order: str = "desc") -> dict:
    """
    获取游戏列表。
    
    ⚠️ 重要：这是所有游戏相关查询的入口点。必须先搜索游戏名称来获取 game_id，
    然后才能在其他函数（如 get_mods）中使用该 ID。
    
    典型工作流:
    1. 使用 search 参数调用此函数来查找游戏
    2. 从返回结果中获取游戏的 id 字段
    3. 将该 id 作为 game_id 参数传递给 get_mods、get_game_detail 等函数
    
    支持分页、搜索、类型筛选和排序。
    
    参数:
    - search: 游戏名称搜索关键词（必需用于查找特定游戏）
    - game_type: 游戏类型筛选
    - page: 页码
    - page_size: 每页结果数
    
    返回结构:
    {
        "data": [
            {
                "id": number,                    # 游戏ID（用于其他查询）
                "game_name": string,             # 游戏名称
                "game_ename": string,            # 游戏英文名称
                "game_cover_imgUrl": string,     # 游戏封面图
                "game_path": string,             # 游戏路径
                "game_desc": string,             # 游戏描述
                "allcount": number,              # 总Mod数量
                "tcount": number                 # 最近30天Mod数量
            }
        ],
        "count": number,                         # 总数
        "page": number,                          # 当前页码
        "pageSize": number,                      # 每页数量
        "totalPages": number                     # 总页数
    }
    
    示例:
    - 搜索 "Skyrim" 游戏 -> 获取 id = 123
    - 搜索 Skyrim 的 Mod: get_mods(game_id=123)
    - 或同时查询多个游戏: get_mods(game_id=[123, 456, 789])
    """
    params: dict = {
        "page": page,
        "pageSize": page_size,
        "sortBy": sort_by,
        "sortOrder": sort_order,
    }
    if search:
        params["search"] = search
    if game_type:
        params["gameType"] = game_type
    
    headers = {}
    if API_KEY:
        headers["Authorization"] = API_KEY
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/games", params=params, headers=headers)
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_game_detail(game_id: int) -> dict:
    """
    获取指定游戏的详细信息。
    
    ⚠️ 前置条件：game_id 必须从 get_games 函数的搜索结果中获取。
    
    工作流:
    1. get_games(search="游戏名") -> 获取 id
    2. get_game_detail(game_id=该id) -> 获取详细信息
    
    包括 Mod 统计数据。
    """
    headers = {}
    if API_KEY:
        headers["Authorization"] = API_KEY
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/games/{game_id}", headers=headers)
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_mods(page: int = 1, page_size: int = 20, game_id: Optional[int | list[int]] = None,
                   search: Optional[str] = None, order: int = 0, time: Optional[int] = None) -> dict:
    """
    获取 Mod 列表。
    
    ⚠️ 前置条件：必须先使用 get_games 函数搜索游戏，获取其 id，然后才能查询 Mod。
    
    典型工作流:
    1. 调用 get_games(search="游戏名") 获取游戏 ID
    2. 使用返回的 id 值作为此函数的 game_id 参数
    
    支持多种筛选条件、排序和分页。
    
    参数:
    - page: 页码，默认 1
    - page_size: 每页数量，默认 20
    - game_id: 游戏ID，来自 get_games 函数的返回值
      * 支持单个 ID: game_id=123
      * 支持多个 ID (数组): game_id=[123, 456, 789]（同时查询多个游戏的 Mod）
    - search: 搜索关键词
    - order: 排序方式（控制结果按什么字段排序）
      * 0 = 默认排序
      * 1 = 按浏览量排序
      * 2 = 按下载量排序
      * 3 = 按点赞量排序
      * 4 = 按收藏量排序
      * 5 = 按更新时间排序
    - time: 时间筛选 (1=今天, 2=最近一周, 3=最近一个月, 4=最近三个月)
    
    """
    params: dict = {
        "page": page,
        "pageSize": page_size,
        "order": order,
    }
    if game_id:
        # 支持单个 ID 或多个 ID (数组)
        params["gameId"] = game_id
    if search:
        params["search"] = search
    if time:
        params["time"] = time
    
    headers = {}
    if API_KEY:
        headers["Authorization"] = API_KEY
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/mods", params=params, headers=headers)
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_mod_detail(mod_id: int) -> dict:
    """
    获取指定 Mod 的详细信息。
    
    包括用户信息和游戏信息。
    """
    headers = {}
    if API_KEY:
        headers["Authorization"] = API_KEY
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/mods/{mod_id}", headers=headers)
        response.raise_for_status()
        return response.json()




# ==================== 资源函数 ====================

@mcp.resource("glossmod://games/list")
async def games_list_resource() -> str:
    """
    获取游戏列表资源。
    
    返回热门游戏列表。
    """
    result = await get_games(page=1, page_size=10, sort_by="allcount")
    data = result.get("data", [])
    content = "# 热门游戏列表\n\n"
    for game in data:
        content += f"## {game.get('name', 'N/A')}\n"
        content += f"- ID: {game.get('id', 'N/A')}\n"
        content += f"- Mod 数量: {game.get('allcount', 'N/A')}\n"
        if game.get('description'):
            content += f"- 描述: {game.get('description')}\n"
        content += "\n"
    return content


@mcp.resource("glossmod://games/{game_id}")
async def game_detail_resource(game_id: int) -> str:
    """
    获取指定游戏的详细信息资源。    
    """
    result = await get_game_detail(game_id)
    data = result.get("data", {})
    
    content = f"# {data.get('name', 'N/A')}\n\n"
    content += f"**ID:** {data.get('id', 'N/A')}\n"
    content += f"**英文名:** {data.get('englishName', 'N/A')}\n"
    content += f"**Mod 总数:** {data.get('allcount', 'N/A')}\n"
    content += f"**最近30天 Mod 数:** {data.get('tcount', 'N/A')}\n"
    if data.get('description'):
        content += f"\n**描述:**\n{data.get('description')}\n"
    
    return content


@mcp.resource("glossmod://mods/latest")
async def latest_mods_resource() -> str:
    """
    获取最新 Mod 列表资源。
    """
    result = await get_mods(page=1, page_size=10, time=2)  # 最近一周
    data = result.get("data", [])
    
    content = "# 最新 Mod\n\n"
    for mod in data:
        content += f"## {mod.get('title', 'N/A')}\n"
        content += f"- ID: {mod.get('id', 'N/A')}\n"
        content += f"- 作者: {mod.get('author', 'N/A')}\n"
        content += f"- 版本: {mod.get('version', 'N/A')}\n"
        if mod.get('description'):
            content += f"- 简介: {mod.get('description')[:100]}...\n"
        content += "\n"
    
    return content



# ==================== 提示函数 ====================

@mcp.prompt(name="search_game")
def search_game(game_name: str, detailed: bool = False) -> str:
    """
    生成游戏搜索提示。
    
    此提示帮助用户搜索特定的游戏并获取相关信息。
    
    参数:
    - game_name: 要搜索的游戏名称
    - detailed: 是否需要详细信息
    
    返回: 优化的游戏搜索提示词
    """
    prompt = f"请帮我搜索游戏 '{game_name}'"
    
    if detailed:
        prompt += ("\n\n请执行以下步骤："
                   "\n1. 使用 get_games 工具搜索游戏"
                   "\n2. 如果找到，使用 get_game_detail 获取详细信息"
                   "\n3. 返回游戏的完整信息，包括："
                   "\n   - 游戏 ID（用于后续查询）"
                   "\n   - 游戏名称和英文名"
                   "\n   - 描述"
                   "\n   - Mod 数量统计")
    else:
        prompt += ("。请返回游戏的基本信息："
                   "游戏 ID、名称和 Mod 数量。")
    
    return prompt


@mcp.prompt(name="search_mod")
def search_mod(mod_query: str, game_id: Optional[int] = None, filter_by: str = "latest") -> str:
    """
    生成 Mod 搜索提示。
    
    此提示帮助用户搜索特定的 Mod 或浏览 Mod 列表。
    
    参数:
    - mod_query: Mod 搜索关键词
    - game_id: 特定游戏的 ID（可选）
    - filter_by: 筛选方式 ("latest", "trending", "popular")
    
    返回: 优化的 Mod 搜索提示词
    """
    if game_id:
        prompt = (f"请帮我搜索游戏 ID 为 {game_id} 的 Mod。"
                  f"\n搜索关键词：'{mod_query}'")
    else:
        prompt = f"请帮我搜索 Mod：'{mod_query}'"
    
    if filter_by == "latest":
        prompt += "\n请按最新发布时间排序。"
    elif filter_by == "trending":
        prompt += "\n请显示热门/趋势的 Mod。"
    elif filter_by == "popular":
        prompt += "\n请按下载量或浏览量排序。"
    
    prompt += ("\n对于搜索结果，请："
               "\n1. 使用 get_mods 工具进行搜索"
               "\n2. 如果需要，使用 get_mod_detail 获取单个 Mod 的详细信息"
               "\n3. 返回 Mod 列表，包括标题、作者、版本和简介")
    
    return prompt


@mcp.prompt(name="list_trending_mods")
def list_trending_mods(time_range: str = "week", game_id: Optional[int] = None) -> str:
    """
    生成趋势 Mod 列表提示。
    
    此提示帮助用户查看热门或新发布的 Mod。
    
    参数:
    - time_range: 时间范围 ("today", "week", "month", "all")
    - game_id: 特定游戏的 ID（可选）
    
    返回: 优化的趋势列表提示词
    """
    time_map = {
        "today": 1,
        "week": 2,
        "month": 3,
        "all": 4
    }
    time_value = time_map.get(time_range, 2)
    
    if game_id:
        prompt = f"请为游戏 ID {game_id} 获取趋势 Mod 列表"
    else:
        prompt = "请获取全网趋势 Mod 列表"
    
    prompt += f"（时间范围：{time_range}）。\n\n执行步骤："
    prompt += (f"\n1. 使用 get_mods 工具，设置 time={time_value} 参数"
               f"\n2. 如果指定了游戏 ID，使用 game_id={game_id}"
               f"\n3. 按合适的排序方式显示结果"
               f"\n4. 对于每个 Mod，返回："
               f"\n   - Mod 标题和 ID"
               f"\n   - 作者名称"
               f"\n   - 版本号"
               f"\n   - 简介"
               f"\n   - 浏览和下载统计（如可用）")
    
    return prompt


def main():
    """MCP 服务器入口点"""
    mcp.run()


if __name__ == "__main__":
    main()
