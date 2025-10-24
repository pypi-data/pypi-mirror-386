# Halo MCP Server 设计文档

## 1. 项目概述

### 1.1 项目名称
**halo-mcp-server** - 基于 Python 的 Halo 内容管理 MCP 服务器

### 1.2 项目定位
为 AI 助手（如 Claude、GPT 等）提供与 Halo 博客系统交互的能力，通过 Model Context Protocol (MCP) 实现文档的发布、修改、删除等操作。

### 1.3 核心特性
- ✅ 本地运行，无需独立部署服务端
- ✅ 基于 MCP 协议，与 AI 助手无缝集成
- ✅ 支持文章的完整生命周期管理（CRUD）
- ✅ 支持分类、标签管理
- ✅ 支持草稿和发布流程
- ✅ 支持评论管理
- ✅ 支持附件上传
- ✅ 支持搜索和查询

### 1.4 使用场景
- **AI 辅助写作**: AI 帮助生成并发布博客文章
- **内容批量管理**: 批量创建、更新、删除文章
- **自动化运维**: 定时发布、内容同步
- **智能问答**: 基于博客内容的智能检索和回答

---

## 2. 技术架构

### 2.1 技术栈

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| 编程语言 | Python 3.10+ | 现代 Python 特性支持 |
| MCP SDK | mcp | Model Context Protocol SDK |
| HTTP 客户端 | httpx | 异步 HTTP 请求 |
| 配置管理 | python-dotenv | 环境变量管理 |
| 数据验证 | pydantic | 数据模型验证 |
| 日志记录 | loguru | 结构化日志 |

### 2.2 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                     AI Assistant (Claude)                    │
│                   (MCP Client - Claude Desktop)              │
└──────────────────────────┬──────────────────────────────────┘
                           │ MCP Protocol
                           │ (stdio)
┌──────────────────────────▼──────────────────────────────────┐
│                  Halo MCP Server (Python)                    │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              MCP Protocol Handler Layer                 │ │
│  │  - Tool Registration   - Resource Provider             │ │
│  │  - Prompt Templates    - Error Handling                │ │
│  └────────────────┬───────────────────────────────────────┘ │
│  ┌────────────────▼───────────────────────────────────────┐ │
│  │              Business Logic Layer                       │ │
│  │  - PostManager      - CategoryManager                  │ │
│  │  - TagManager       - AttachmentManager                │ │
│  │  - CommentManager   - SearchManager                    │ │
│  └────────────────┬───────────────────────────────────────┘ │
│  ┌────────────────▼───────────────────────────────────────┐ │
│  │              Halo API Client Layer                      │ │
│  │  - Authentication   - Request/Response Handler         │ │
│  │  - Rate Limiting    - Error Retry                      │ │
│  └────────────────┬───────────────────────────────────────┘ │
└───────────────────┼───────────────────────────────────────┘
                    │ HTTPS/HTTP
┌───────────────────▼───────────────────────────────────────┐
│                    Halo Server                             │
│  - Console API   - Public API   - UC API                   │
└────────────────────────────────────────────────────────────┘
```

### 2.3 目录结构

```
halo-mcp-server/
├── src/
│   └── halo-mcp-server/
│       ├── __init__.py
│       ├── __main__.py              # 入口文件
│       ├── server.py                # MCP Server 主程序
│       ├── config.py                # 配置管理
│       ├── client/
│       │   ├── __init__.py
│       │   ├── base.py              # 基础 HTTP 客户端
│       │   ├── auth.py              # 认证处理
│       │   └── halo_client.py       # Halo API 客户端
│       ├── managers/
│       │   ├── __init__.py
│       │   ├── post_manager.py      # 文章管理
│       │   ├── category_manager.py  # 分类管理
│       │   ├── tag_manager.py       # 标签管理
│       │   ├── attachment_manager.py # 附件管理
│       │   ├── comment_manager.py   # 评论管理
│       │   └── search_manager.py    # 搜索管理
│       ├── models/
│       │   ├── __init__.py
│       │   ├── post.py              # 文章数据模型
│       │   ├── category.py          # 分类数据模型
│       │   ├── tag.py               # 标签数据模型
│       │   └── common.py            # 通用数据模型
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── post_tools.py        # 文章相关 Tools
│       │   ├── category_tools.py    # 分类相关 Tools
│       │   ├── tag_tools.py         # 标签相关 Tools
│       │   ├── attachment_tools.py  # 附件相关 Tools
│       │   └── search_tools.py      # 搜索相关 Tools
│       ├── prompts/
│       │   ├── __init__.py
│       │   └── templates.py         # Prompt 模板
│       └── utils/
│           ├── __init__.py
│           ├── logger.py            # 日志工具
│           ├── markdown.py          # Markdown 处理
│           └── validators.py        # 数据验证
├── tests/
│   ├── __init__.py
│   ├── test_client.py
│   ├── test_managers.py
│   └── test_tools.py
├── examples/
│   ├── config.example.env           # 配置示例
│   └── usage_examples.md            # 使用示例
├── pyproject.toml                   # 项目配置
├── README.md                        # 项目说明
├── DESIGN.md                        # 设计文档（本文件）
└── LICENSE                          # 许可证
```

---

## 3. MCP Tools 设计

### 3.1 文章管理 Tools

#### 3.1.1 list_my_posts
**功能**: 列出当前用户的文章

**输入参数**:
- `page` (integer, optional): 页码，默认 0
- `size` (integer, optional): 每页大小，默认 20
- `publish_phase` (string, optional): 发布阶段，可选值：DRAFT, PENDING_APPROVAL, PUBLISHED, FAILED
- `keyword` (string, optional): 搜索关键词
- `category` (string, optional): 分类名称

**输出示例**:
```json
{
  "total": 100,
  "page": 0,
  "size": 20,
  "items": [
    {
      "name": "post-20240101-hello",
      "title": "Hello World",
      "excerpt": "我的第一篇博客",
      "publish_time": "2024-01-01T10:00:00Z",
      "status": "PUBLISHED",
      "categories": ["技术"],
      "tags": ["Python", "MCP"],
      "view_count": 100,
      "comment_count": 5
    }
  ]
}
```

#### 3.1.2 get_post
**功能**: 获取文章详情

**输入参数**:
- `name` (string, required): 文章名称/slug

**输出示例**:
```json
{
  "name": "post-20240101-hello",
  "title": "Hello World",
  "slug": "hello-world",
  "content": {
    "raw": "# Hello World\n\n这是我的第一篇博客...",
    "content": "<h1>Hello World</h1><p>这是我的第一篇博客...</p>"
  },
  "excerpt": "我的第一篇博客",
  "categories": ["技术"],
  "tags": ["Python", "MCP"],
  "cover": "https://example.com/cover.jpg",
  "publish_time": "2024-01-01T10:00:00Z",
  "allow_comment": true,
  "visible": "PUBLIC"
}
```

#### 3.1.3 create_post
**功能**: 创建文章

**输入参数**:
- `title` (string, required): 文章标题
- `content` (string, required): Markdown 格式的内容
- `excerpt` (string, optional): 文章摘要
- `slug` (string, optional): URL slug，留空则自动生成
- `categories` (array, optional): 分类名称列表
- `tags` (array, optional): 标签名称列表
- `cover` (string, optional): 封面图片 URL
- `allow_comment` (boolean, optional): 是否允许评论，默认 true
- `pinned` (boolean, optional): 是否置顶，默认 false
- `visible` (string, optional): 可见性，可选值：PUBLIC, PRIVATE，默认 PUBLIC
- `publish_immediately` (boolean, optional): 是否立即发布，默认 false

**输出示例**:
```json
{
  "success": true,
  "name": "post-20240101-hello",
  "message": "文章创建成功",
  "url": "http://blog.example.com/posts/hello-world"
}
```

#### 3.1.4 update_post
**功能**: 更新文章

**输入参数**:
- `name` (string, required): 文章名称
- `title` (string, optional): 新标题
- `content` (string, optional): 新内容
- `excerpt` (string, optional): 新摘要
- `categories` (array, optional): 新分类
- `tags` (array, optional): 新标签
- `cover` (string, optional): 新封面
- `allow_comment` (boolean, optional): 是否允许评论
- `pinned` (boolean, optional): 是否置顶
- `visible` (string, optional): 可见性

**输出示例**:
```json
{
  "success": true,
  "name": "post-20240101-hello",
  "message": "文章更新成功"
}
```

#### 3.1.5 publish_post
**功能**: 发布文章

**输入参数**:
- `name` (string, required): 文章名称

**输出示例**:
```json
{
  "success": true,
  "name": "post-20240101-hello",
  "message": "文章发布成功",
  "publish_time": "2024-01-01T10:00:00Z",
  "url": "http://blog.example.com/posts/hello-world"
}
```

#### 3.1.6 unpublish_post
**功能**: 取消发布文章

**输入参数**:
- `name` (string, required): 文章名称

**输出示例**:
```json
{
  "success": true,
  "name": "post-20240101-hello",
  "message": "文章已取消发布，转为草稿状态"
}
```

#### 3.1.7 delete_post
**功能**: 删除文章（移至回收站）

**输入参数**:
- `name` (string, required): 文章名称

**输出示例**:
```json
{
  "success": true,
  "name": "post-20240101-hello",
  "message": "文章已移至回收站"
}
```

#### 3.1.8 get_post_draft
**功能**: 获取文章草稿

**输入参数**:
- `name` (string, required): 文章名称
- `include_patched` (boolean, optional): 是否包含补丁内容，默认 false

**输出示例**:
```json
{
  "name": "snapshot-123",
  "post_name": "post-20240101-hello",
  "content": {
    "raw": "# Hello World\n\n草稿内容...",
    "rawType": "markdown"
  },
  "last_modified": "2024-01-01T09:00:00Z"
}
```

#### 3.1.9 update_post_draft
**功能**: 更新文章草稿

**输入参数**:
- `name` (string, required): 文章名称
- `content` (string, required): Markdown 内容

**输出示例**:
```json
{
  "success": true,
  "message": "草稿已保存",
  "last_modified": "2024-01-01T09:30:00Z"
}
```

---

### 3.2 分类管理 Tools

#### 3.2.1 list_categories
**功能**: 列出所有分类

**输入参数**:
- `page` (integer, optional): 页码，默认 0
- `size` (integer, optional): 每页大小，默认 50

**输出示例**:
```json
{
  "total": 10,
  "items": [
    {
      "name": "category-tech",
      "display_name": "技术",
      "slug": "tech",
      "description": "技术类文章",
      "post_count": 25,
      "cover": "https://example.com/tech-cover.jpg"
    }
  ]
}
```

#### 3.2.2 create_category
**功能**: 创建分类

**输入参数**:
- `display_name` (string, required): 分类显示名称
- `slug` (string, optional): URL slug，留空则自动生成
- `description` (string, optional): 分类描述
- `cover` (string, optional): 封面图片 URL
- `priority` (integer, optional): 优先级，用于排序

**输出示例**:
```json
{
  "success": true,
  "name": "category-tech",
  "message": "分类创建成功"
}
```

#### 3.2.3 update_category
**功能**: 更新分类

**输入参数**:
- `name` (string, required): 分类名称
- `display_name` (string, optional): 新显示名称
- `description` (string, optional): 新描述
- `cover` (string, optional): 新封面

#### 3.2.4 delete_category
**功能**: 删除分类

**输入参数**:
- `name` (string, required): 分类名称

---

### 3.3 标签管理 Tools

#### 3.3.1 list_tags
**功能**: 列出所有标签

**输入参数**:
- `page` (integer, optional): 页码，默认 0
- `size` (integer, optional): 每页大小，默认 100

**输出示例**:
```json
{
  "total": 50,
  "items": [
    {
      "name": "tag-python",
      "display_name": "Python",
      "slug": "python",
      "color": "#3776AB",
      "post_count": 15
    }
  ]
}
```

#### 3.3.2 create_tag
**功能**: 创建标签

**输入参数**:
- `display_name` (string, required): 标签显示名称
- `slug` (string, optional): URL slug
- `color` (string, optional): 标签颜色，十六进制格式

#### 3.3.3 update_tag
**功能**: 更新标签

**输入参数**:
- `name` (string, required): 标签名称
- `display_name` (string, optional): 新显示名称
- `color` (string, optional): 新颜色

#### 3.3.4 delete_tag
**功能**: 删除标签

**输入参数**:
- `name` (string, required): 标签名称

---

### 3.4 附件管理 Tools

#### 3.4.1 list_attachments
**功能**: 列出附件

**输入参数**:
- `page` (integer, optional): 页码
- `size` (integer, optional): 每页大小
- `keyword` (string, optional): 搜索关键词
- `accepts` (array, optional): 媒体类型过滤，如 ["image/*", "video/*"]
- `group` (string, optional): 分组名称

**输出示例**:
```json
{
  "total": 100,
  "items": [
    {
      "name": "attachment-123",
      "display_name": "图片.jpg",
      "media_type": "image/jpeg",
      "size": 102400,
      "url": "https://example.com/uploads/image.jpg",
      "upload_time": "2024-01-01T10:00:00Z"
    }
  ]
}
```

#### 3.4.2 upload_attachment
**功能**: 上传附件

**输入参数**:
- `file_path` (string, required): 本地文件路径
- `group` (string, optional): 分组名称
- `display_name` (string, optional): 显示名称

**输出示例**:
```json
{
  "success": true,
  "name": "attachment-123",
  "url": "https://example.com/uploads/image.jpg",
  "message": "文件上传成功"
}
```

#### 3.4.3 upload_from_url
**功能**: 从 URL 上传附件

**输入参数**:
- `url` (string, required): 文件 URL
- `group` (string, optional): 分组名称
- `display_name` (string, optional): 显示名称

**输出示例**:
```json
{
  "success": true,
  "name": "attachment-124",
  "url": "https://example.com/uploads/imported-image.jpg",
  "message": "文件导入成功"
}
```

---

### 3.5 搜索 Tools

#### 3.5.1 search_posts
**功能**: 搜索文章

**输入参数**:
- `keyword` (string, required): 搜索关键词
- `limit` (integer, optional): 返回结果数量限制，默认 10

**输出示例**:
```json
{
  "total": 5,
  "keyword": "Python",
  "items": [
    {
      "name": "post-python-guide",
      "title": "Python 入门指南",
      "excerpt": "本文介绍 Python 基础知识...",
      "highlight": "...学习 <mark>Python</mark> 编程...",
      "score": 0.95
    }
  ]
}
```

---

### 3.6 评论管理 Tools

#### 3.6.1 list_comments
**功能**: 列出评论

**输入参数**:
- `post_name` (string, optional): 文章名称，留空则返回所有评论
- `page` (integer, optional): 页码
- `size` (integer, optional): 每页大小
- `approved_only` (boolean, optional): 仅显示已审核评论，默认 false

**输出示例**:
```json
{
  "total": 20,
  "items": [
    {
      "name": "comment-123",
      "author": "张三",
      "email": "zhangsan@example.com",
      "content": "写得很好！",
      "approved": true,
      "create_time": "2024-01-01T12:00:00Z",
      "post_name": "post-python-guide"
    }
  ]
}
```

#### 3.6.2 approve_comment
**功能**: 审核通过评论

**输入参数**:
- `name` (string, required): 评论名称

#### 3.6.3 delete_comment
**功能**: 删除评论

**输入参数**:
- `name` (string, required): 评论名称

---

## 4. MCP Resources 设计

### 4.1 资源列表

#### 4.1.1 站点配置资源
**URI**: `halo://config`

**描述**: 返回 Halo 站点的基本配置信息

**返回内容**:
```json
{
  "title": "我的博客",
  "subtitle": "分享技术与生活",
  "url": "https://blog.example.com",
  "logo": "https://blog.example.com/logo.png",
  "timezone": "Asia/Shanghai",
  "language": "zh-CN"
}
```

#### 4.1.2 文章内容资源
**URI**: `halo://posts/{post-name}`

**描述**: 返回指定文章的完整内容

**返回内容**: 与 `get_post` Tool 相同

#### 4.1.3 分类树资源
**URI**: `halo://categories`

**描述**: 返回所有分类的树形结构

**返回内容**:
```json
{
  "categories": [
    {
      "name": "category-tech",
      "display_name": "技术",
      "post_count": 25,
      "children": [
        {
          "name": "category-python",
          "display_name": "Python",
          "post_count": 10
        }
      ]
    }
  ]
}
```

#### 4.1.4 标签云资源
**URI**: `halo://tags`

**描述**: 返回所有标签及其使用频率

**返回内容**:
```json
{
  "tags": [
    {
      "name": "tag-python",
      "display_name": "Python",
      "post_count": 15,
      "color": "#3776AB"
    }
  ]
}
```

#### 4.1.5 最新文章资源
**URI**: `halo://posts/recent`

**描述**: 返回最近发布的文章列表

**参数**: `?limit=10`

---

## 5. MCP Prompts 设计

### 5.1 Prompt 模板列表

#### 5.1.1 写作助手
**名称**: `halo-writing-assistant`

**描述**: 帮助用户撰写和发布博客文章

**参数**:
- `topic` (string): 文章主题
- `style` (string): 写作风格（technical/lifestyle/casual）
- `length` (string): 文章长度（short/medium/long）
- `target_audience` (string): 目标读者（beginner/intermediate/expert）

**Prompt 模板**:
```
我需要你帮我写一篇关于「{topic}」的博客文章。

要求：
- 写作风格：{style}
- 文章长度：{length}
- 目标读者：{target_audience}

请按以下步骤进行：
1. 先规划文章大纲
2. 撰写完整内容（使用 Markdown 格式）
3. 添加合适的分类和标签
4. 使用 create_post 工具创建文章
5. 询问我是否立即发布

请开始吧！
```

#### 5.1.2 内容优化助手
**名称**: `halo-content-optimizer`

**描述**: 优化现有文章的内容和结构

**参数**:
- `post_name` (string): 文章名称
- `optimization_type` (string): 优化类型（seo/readability/structure）

**Prompt 模板**:
```
请帮我优化文章「{post_name}」。

优化重点：{optimization_type}

步骤：
1. 使用 get_post 获取文章内容
2. 分析当前内容的问题
3. 提供具体的优化建议
4. 如果我同意，使用 update_post 更新文章

开始分析吧！
```

#### 5.1.3 批量发布助手
**名称**: `halo-batch-publisher`

**描述**: 批量处理和发布多篇文章

**参数**:
- `articles` (array): 文章列表
- `schedule` (string): 发布计划（immediate/daily/weekly）

**Prompt 模板**:
```
我要批量发布以下文章：
{articles}

发布计划：{schedule}

请帮我：
1. 检查每篇文章的格式
2. 创建所有文章
3. 根据计划安排发布时间
4. 报告处理结果

开始执行吧！
```

#### 5.1.4 SEO 优化助手
**名称**: `halo-seo-optimizer`

**描述**: 优化文章的 SEO 表现

**参数**:
- `post_name` (string): 文章名称

**Prompt 模板**:
```
请帮我优化文章「{post_name}」的 SEO。

需要检查：
1. 标题是否包含关键词
2. 摘要是否吸引人
3. 标签和分类是否合理
4. 内容结构是否清晰
5. 内部链接是否充分

给出具体的优化建议。
```

#### 5.1.5 内容同步助手
**名称**: `halo-content-sync`

**描述**: 从其他平台同步内容到 Halo

**参数**:
- `source_url` (string): 源文章 URL
- `platform` (string): 平台类型（medium/notion/wordpress）

**Prompt 模板**:
```
请帮我从 {platform} 同步文章到 Halo。

源地址：{source_url}

步骤：
1. 获取源文章内容
2. 转换为 Markdown 格式
3. 下载并上传图片
4. 创建文章
5. 保留原始链接引用

开始同步吧！
```

---

## 6. 配置管理

### 6.1 环境变量配置

创建 `.env` 文件:

```env
# ========== Halo 服务器配置 ==========
# Halo 服务器地址
HALO_BASE_URL=http://localhost:8091

# 认证方式 1: 使用 Token（推荐）
HALO_TOKEN=your_bearer_token_here

# 认证方式 2: 使用用户名密码
# HALO_USERNAME=admin
# HALO_PASSWORD=your_password

# ========== MCP 服务配置 ==========
# MCP 服务器名称
MCP_SERVER_NAME=halo-mcp-server

# 日志级别: DEBUG, INFO, WARNING, ERROR
MCP_LOG_LEVEL=INFO

# HTTP 请求超时时间（秒）
MCP_TIMEOUT=30

# ========== 功能开关 ==========
# 启用草稿自动保存
ENABLE_DRAFT_AUTO_SAVE=true

# 启用图片自动压缩
ENABLE_IMAGE_COMPRESSION=true

# 压缩后图片最大宽度（像素）
IMAGE_MAX_WIDTH=1920

# 图片质量（1-100）
IMAGE_QUALITY=85

# 最大上传文件大小（MB）
MAX_UPLOAD_SIZE_MB=10

# ========== 高级配置 ==========
# HTTP 连接池大小
HTTP_POOL_SIZE=10

# 请求重试次数
MAX_RETRIES=3

# 重试间隔（秒）
RETRY_DELAY=1

# 启用请求缓存
ENABLE_CACHE=true

# 缓存过期时间（秒）
CACHE_TTL=300
```

### 6.2 Claude Desktop 配置

#### Windows 配置路径
`%APPDATA%\Claude\claude_desktop_config.json`

#### macOS 配置路径
`~/Library/Application Support/Claude/claude_desktop_config.json`

#### Linux 配置路径
`~/.config/Claude/claude_desktop_config.json`

#### 配置示例

```json
{
  "mcpServers": {
    "halo": {
      "command": "python",
      "args": [
        "-m",
        "halo-mcp-server"
      ],
      "env": {
        "HALO_BASE_URL": "http://localhost:8091",
        "HALO_TOKEN": "your_bearer_token_here",
        "MCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

#### 使用虚拟环境的配置

```json
{
  "mcpServers": {
    "halo": {
      "command": "D:\\Python\\venv\\Scripts\\python.exe",
      "args": [
        "-m",
        "halo-mcp-server"
      ],
      "env": {
        "HALO_BASE_URL": "http://localhost:8091",
        "HALO_TOKEN": "your_token"
      }
    }
  }
}
```

---

## 7. 安全设计

### 7.1 认证机制

#### 7.1.1 Token 认证（推荐）
- 使用 Bearer Token 进行 API 认证
- Token 存储在环境变量中，不硬编码
- 支持 Token 过期检测和提示

#### 7.1.2 用户名密码认证
- 仅用于开发环境
- 密码使用环境变量存储
- 登录后获取 Token 并缓存

#### 7.1.3 Token 刷新机制
- 自动检测 Token 过期（401 响应）
- 尝试使用用户名密码重新登录
- 失败后提示用户更新配置

### 7.2 权限控制

#### 7.2.1 基于 Halo RBAC
- 遵循 Halo 的角色权限系统
- 操作前验证用户权限
- 权限不足时友好提示

#### 7.2.2 敏感操作确认
- 删除操作需要确认
- 批量操作需要确认
- 发布操作可选确认

### 7.3 数据安全

#### 7.3.1 敏感信息保护
- 密码和 Token 仅存储在环境变量
- 日志中不记录敏感信息
- 错误信息不暴露系统细节

#### 7.3.2 传输安全
- 生产环境强制使用 HTTPS
- 开发环境可使用 HTTP
- 支持自签名证书（开发环境）

#### 7.3.3 输入验证
- 所有用户输入进行验证
- 防止 XSS 攻击
- 防止 SQL 注入（虽然不直接操作数据库）

### 7.4 异常处理

#### 7.4.1 错误分类
```python
class HaloMCPError(Exception):
    """基础异常类"""
    pass

class AuthenticationError(HaloMCPError):
    """认证失败"""
    pass

class PermissionError(HaloMCPError):
    """权限不足"""
    pass

class ResourceNotFoundError(HaloMCPError):
    """资源不存在"""
    pass

class NetworkError(HaloMCPError):
    """网络错误"""
    pass

class ValidationError(HaloMCPError):
    """数据验证错误"""
    pass
```

#### 7.4.2 错误处理策略
- 网络错误：自动重试（最多3次）
- 认证错误：提示用户检查配置
- 权限错误：提示所需权限
- 资源不存在：提示检查名称
- 验证错误：详细说明问题

#### 7.4.3 日志记录
```python
# 不同级别的日志
logger.debug("详细的调试信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("错误信息")
```

---

## 8. 性能优化

### 8.1 请求优化

#### 8.1.1 连接池复用
```python
import httpx

# 使用连接池
client = httpx.AsyncClient(
    limits=httpx.Limits(
        max_connections=10,
        max_keepalive_connections=5
    )
)
```

#### 8.1.2 批量操作
- 批量创建文章时合并请求
- 批量更新时使用异步并发
- 分页查询时预取下一页

#### 8.1.3 请求缓存
```python
from functools import lru_cache
from datetime import datetime, timedelta

class Cache:
    def __init__(self, ttl=300):
        self.cache = {}
        self.ttl = ttl
    
    def get(self, key):
        if key in self.cache:
            value, timestamp = self.cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self.ttl):
                return value
        return None
    
    def set(self, key, value):
        self.cache[key] = (value, datetime.now())
```

### 8.2 并发控制

#### 8.2.1 异步请求
```python
import asyncio

async def batch_create_posts(posts):
    tasks = [create_post(post) for post in posts]
    results = await asyncio.gather(*tasks)
    return results
```

#### 8.2.2 并发限制
```python
from asyncio import Semaphore

# 限制同时最多5个并发请求
semaphore = Semaphore(5)

async def limited_request():
    async with semaphore:
        return await make_request()
```

#### 8.2.3 请求队列
- 超过限流阈值时排队等待
- 优先级队列（发布 > 更新 > 查询）
- 失败请求自动重试

### 8.3 资源管理

#### 8.3.1 大文件处理
```python
# 分块上传
async def upload_large_file(file_path, chunk_size=1024*1024):
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            await upload_chunk(chunk)
```

#### 8.3.2 图片压缩
```python
from PIL import Image

def compress_image(image_path, max_width=1920, quality=85):
    img = Image.open(image_path)
    
    # 按比例缩放
    if img.width > max_width:
        ratio = max_width / img.width
        new_size = (max_width, int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)
    
    # 保存压缩后的图片
    img.save(output_path, quality=quality, optimize=True)
```

#### 8.3.3 临时文件清理
```python
import atexit
import tempfile
import shutil

temp_dir = tempfile.mkdtemp()

# 程序退出时清理
@atexit.register
def cleanup():
    shutil.rmtree(temp_dir, ignore_errors=True)
```

---

## 9. 开发计划

### Phase 1: 基础框架（Week 1-2）

**目标**: 搭建项目基础架构

**任务清单**:
- [x] 项目目录结构设计
- [ ] 基础 HTTP 客户端实现
- [ ] 认证模块开发
- [ ] 配置管理系统
- [ ] 日志系统搭建
- [ ] 错误处理框架
- [ ] MCP Server 基础框架
- [ ] 单元测试环境搭建

**交付物**:
- 可运行的 MCP Server 骨架
- 完整的项目文档
- 基础测试用例

### Phase 2: 核心功能（Week 3-4）

**目标**: 实现文章管理核心功能

**任务清单**:
- [ ] PostManager 实现
- [ ] 文章 CRUD Tools 开发
- [ ] 草稿管理功能
- [ ] 发布/取消发布功能
- [ ] 文章列表查询
- [ ] 文章详情获取
- [ ] 集成测试

**交付物**:
- 完整的文章管理功能
- API 对接文档
- 功能测试报告

### Phase 3: 扩展功能（Week 5-6）

**目标**: 实现分类、标签、附件管理

**任务清单**:
- [ ] CategoryManager 实现
- [ ] TagManager 实现
- [ ] AttachmentManager 实现
- [ ] 分类 CRUD Tools
- [ ] 标签 CRUD Tools
- [ ] 附件上传 Tools
- [ ] 从 URL 导入附件
- [ ] 集成测试

**交付物**:
- 分类标签管理功能
- 附件上传功能
- 完整的 Tools 文档

### Phase 4: 高级功能（Week 7-8）

**目标**: 搜索、评论、Prompts

**任务清单**:
- [ ] SearchManager 实现
- [ ] CommentManager 实现
- [ ] 搜索 Tools 开发
- [ ] 评论管理 Tools
- [ ] Prompt 模板系统
- [ ] Resources 系统
- [ ] 性能优化

**交付物**:
- 搜索和评论功能
- Prompt 模板库
- 性能测试报告

### Phase 5: 优化和发布（Week 9-10）

**目标**: 优化、测试、文档、发布

**任务清单**:
- [ ] 代码重构和优化
- [ ] 完整的单元测试
- [ ] 集成测试和 E2E 测试
- [ ] 用户文档编写
- [ ] API 文档生成
- [ ] 示例代码编写
- [ ] PyPI 打包发布
- [ ] 发布公告

**交付物**:
- 生产就绪的 1.0 版本
- 完整的用户文档
- PyPI 包发布

---

## 10. 测试策略

### 10.1 单元测试

#### 10.1.1 测试覆盖目标
- 代码覆盖率 > 80%
- 核心模块覆盖率 > 95%
- 所有公开 API 100% 覆盖

#### 10.1.2 测试框架
```python
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock

@pytest.mark.asyncio
async def test_create_post():
    # Mock Halo API
    mock_client = AsyncMock()
    mock_client.post.return_value = {
        "metadata": {"name": "test-post"}
    }
    
    # 测试创建文章
    manager = PostManager(mock_client)
    result = await manager.create_post(
        title="Test Post",
        content="Test Content"
    )
    
    assert result["name"] == "test-post"
```

#### 10.1.3 Mock 策略
- Mock Halo API 响应
- Mock 文件系统操作
- Mock 网络请求

### 10.2 集成测试

#### 10.2.1 测试环境
- 使用 Docker 部署 Halo 测试实例
- 配置测试数据库
- 准备测试数据

#### 10.2.2 测试场景
```python
@pytest.mark.integration
async def test_post_lifecycle():
    """测试文章完整生命周期"""
    # 1. 创建文章
    post = await create_post(title="Test", content="Content")
    
    # 2. 更新草稿
    await update_draft(post["name"], content="Updated")
    
    # 3. 发布文章
    await publish_post(post["name"])
    
    # 4. 验证发布状态
    result = await get_post(post["name"])
    assert result["status"] == "PUBLISHED"
    
    # 5. 取消发布
    await unpublish_post(post["name"])
    
    # 6. 删除文章
    await delete_post(post["name"])
```

### 10.3 性能测试

#### 10.3.1 并发测试
```python
import asyncio

async def test_concurrent_requests():
    """测试并发请求性能"""
    tasks = [create_post(f"Post {i}", "Content") for i in range(100)]
    
    start = time.time()
    results = await asyncio.gather(*tasks)
    duration = time.time() - start
    
    # 100 个并发请求应在 10 秒内完成
    assert duration < 10
    assert len(results) == 100
```

#### 10.3.2 大文件测试
```python
async def test_large_file_upload():
    """测试大文件上传"""
    # 创建 10MB 测试文件
    test_file = create_test_file(size_mb=10)
    
    start = time.time()
    result = await upload_attachment(test_file)
    duration = time.time() - start
    
    # 10MB 文件应在 30 秒内上传完成
    assert duration < 30
    assert result["success"] == True
```

---

## 11. 部署和使用

### 11.1 系统要求

- **Python**: 3.10 或更高版本
- **操作系统**: Windows 10+, macOS 10.15+, Linux (Ubuntu 20.04+)
- **内存**: 最小 512MB，推荐 1GB
- **Halo**: 2.0+ 版本

### 11.2 安装方式

#### 方式 1: PyPI 安装（推荐）

```bash
# 安装最新版本
pip install halo-mcp-server

# 安装指定版本
pip install halo-mcp-server==1.0.0

# 升级到最新版本
pip install --upgrade halo-mcp-server
```

#### 方式 2: 源码安装

```bash
# 克隆仓库
git clone https://github.com/Huangwh826/halo_mcp_server.git
cd halo-mcp-server

# 安装依赖
pip install -e .

# 开发模式（包含开发依赖）
pip install -e ".[dev]"
```

#### 方式 3: Docker 部署

```bash
# 构建镜像
docker build -t halo-mcp-server .

# 运行容器
docker run -d \
  -e HALO_BASE_URL=http://halo:8091 \
  -e HALO_TOKEN=your_token \
  halo-mcp-server
```

### 11.3 配置步骤

#### 步骤 1: 获取 Halo Token

1. 登录 Halo 后台
2. 进入"个人中心" → "个人令牌"
3. 点击"创建令牌"
4. 填写令牌名称（如"MCP Server"）
5. 选择权限范围（建议选择"文章管理"相关权限）
6. 保存并复制生成的令牌

#### 步骤 2: 配置 Claude Desktop

编辑 Claude Desktop 配置文件:

**Windows**:
```
%APPDATA%\Claude\claude_desktop_config.json
```

**macOS**:
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

添加配置:
```json
{
  "mcpServers": {
    "halo": {
      "command": "python",
      "args": ["-m", "halo-mcp-server"],
      "env": {
        "HALO_BASE_URL": "http://localhost:8091",
        "HALO_TOKEN": "your_token_here"
      }
    }
  }
}
```

#### 步骤 3: 重启 Claude Desktop

重启 Claude Desktop 使配置生效。

#### 步骤 4: 验证安装

在 Claude 中输入:
```
请列出我的所有文章
```

如果能正常返回文章列表，说明配置成功！

### 11.4 使用示例

详细使用示例请参考 [使用示例文档](examples/usage_examples.md)

---

## 12. 故障排除

### 12.1 常见问题

#### 问题 1: Claude 无法识别 Halo MCP

**症状**: 在 Claude 中提到 Halo 但没有调用相关 Tools

**原因**:
- MCP Server 未正确启动
- 配置文件格式错误
- Python 环境问题

**解决方案**:
1. 检查 Claude Desktop 配置文件语法
2. 确认 Python 命令路径正确
3. 查看 Claude Desktop 日志
4. 重启 Claude Desktop

#### 问题 2: 认证失败

**症状**: 提示"Authentication failed"

**原因**:
- Token 无效或过期
- Halo 服务器地址错误
- 网络连接问题

**解决方案**:
1. 重新生成 Halo Token
2. 检查 HALO_BASE_URL 是否正确
3. 测试网络连接: `ping localhost` 或 `curl http://localhost:8091`
4. 检查 Halo 服务是否运行

#### 问题 3: 上传文件失败

**症状**: 附件上传返回错误

**原因**:
- 文件过大超过限制
- 文件类型不支持
- 存储空间不足

**解决方案**:
1. 检查文件大小，调整 MAX_UPLOAD_SIZE_MB
2. 确认文件类型在允许列表中
3. 检查 Halo 存储空间
4. 启用图片压缩: ENABLE_IMAGE_COMPRESSION=true

#### 问题 4: 请求超时

**症状**: 操作时提示"Request timeout"

**原因**:
- 网络延迟过高
- Halo 服务器响应慢
- 超时设置过短

**解决方案**:
1. 增加超时时间: MCP_TIMEOUT=60
2. 检查网络连接质量
3. 优化 Halo 服务器性能
4. 减少单次请求的数据量

### 12.2 日志调试

#### 启用调试日志

```env
MCP_LOG_LEVEL=DEBUG
```

#### 查看日志文件

日志位置:
- Windows: `%APPDATA%\halo-mcp-server\logs\`
- macOS/Linux: `~/.halo-mcp-server/logs/`

#### 日志分析

```bash
# 查看最新日志
tail -f ~/.halo-mcp/logs/halo_mcp_server.log

# 搜索错误
grep ERROR ~/.halo-mcp-server/logs/halo_mcp_server.log

# 统计请求数量
grep "API Request" ~/.halo-mcp-server/logs/halo_mcp_server.log | wc -l
```

---

## 13. 贡献指南

### 13.1 开发环境设置

```bash
# 1. Fork 项目并克隆
git clone https://github.com/Huangwh826/halo_mcp_server.git
cd halo-mcp-server

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装开发依赖
pip install -e ".[dev]"

# 4. 安装 pre-commit hooks
pre-commit install

# 5. 运行测试
pytest
```

### 13.2 代码规范

#### 13.2.1 Python 代码风格

- 遵循 [PEP 8](https://peps.python.org/pep-0008/)
- 使用 [Black](https://github.com/psf/black) 格式化代码
- 使用 [isort](https://pycqa.github.io/isort/) 排序导入
- 使用 [mypy](http://mypy-lang.org/) 类型检查

```bash
# 格式化代码
black src/

# 排序导入
isort src/

# 类型检查
mypy src/
```

#### 13.2.2 文档规范

- 所有公开 API 必须有 docstring
- 使用 Google 风格的 docstring
- 示例:

```python
def create_post(title: str, content: str) -> dict:
    """创建文章
    
    Args:
        title: 文章标题
        content: 文章内容（Markdown 格式）
    
    Returns:
        包含文章信息的字典
    
    Raises:
        ValidationError: 参数验证失败
        AuthenticationError: 认证失败
    
    Example:
        >>> result = create_post("Hello", "World")
        >>> print(result["name"])
        post-hello
    """
    pass
```

#### 13.2.3 测试规范

- 新功能必须包含测试
- 测试覆盖率不低于 80%
- 测试命名: `test_<功能>_<场景>`

```python
def test_create_post_success():
    """测试创建文章成功的场景"""
    pass

def test_create_post_invalid_title():
    """测试标题无效时返回错误"""
    pass
```

### 13.3 提交规范

#### 13.3.1 Commit Message 格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type 类型**:
- `feat`: 新功能
- `fix`: 修复 Bug
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

**示例**:
```
feat(post): 添加文章批量发布功能

实现了批量发布多篇文章的功能，支持:
- 批量创建文章
- 按计划发布
- 错误处理和回滚

Closes #123
```

#### 13.3.2 Pull Request 流程

1. 创建功能分支: `git checkout -b feat/your-feature`
2. 开发并提交代码
3. 推送到 Fork 仓库: `git push origin feat/your-feature`
4. 创建 Pull Request
5. 等待 Code Review
6. 根据反馈修改
7. 合并到主分支

### 13.4 发布流程

```bash
# 1. 更新版本号
# 编辑 pyproject.toml 中的 version

# 2. 更新 CHANGELOG
# 编辑 CHANGELOG.md

# 3. 提交变更
git add .
git commit -m "chore: release v1.0.0"

# 4. 创建标签
git tag -a v1.0.0 -m "Release v1.0.0"

# 5. 推送
git push origin main --tags

# 6. 构建并发布到 PyPI
python -m build
python -m twine upload dist/*
```

---

## 14. 路线图

### 2024 Q1 - 基础版本

**目标**: 发布 v1.0.0，实现核心功能

- [x] 项目架构设计
- [ ] 文章管理功能
- [ ] 分类标签管理
- [ ] 附件上传
- [ ] 基础文档
- [ ] 第一个稳定版本

### 2024 Q2 - 功能增强

**目标**: v1.1.0，增强用户体验

- [ ] 搜索功能优化
- [ ] 评论管理
- [ ] Prompt 模板库
- [ ] 批量操作支持
- [ ] 性能优化
- [ ] 完善文档和示例

### 2024 Q3 - 生态建设

**目标**: v1.2.0，扩展生态

- [ ] 插件系统支持
- [ ] 主题管理功能
- [ ] 数据备份和迁移
- [ ] 多语言支持
- [ ] CI/CD 集成
- [ ] 社区建设

### 2024 Q4 - 企业特性

**目标**: v2.0.0，企业级功能

- [ ] 团队协作支持
- [ ] 权限精细化控制
- [ ] 审计日志
- [ ] 高级分析功能
- [ ] 性能监控
- [ ] 企业级支持

---

## 15. 附录

### 附录 A: API 映射表

| MCP Tool | Halo API Endpoint | HTTP Method | 说明 |
|----------|-------------------|-------------|------|
| list_my_posts | /apis/uc.api.content.halo.run/v1alpha1/posts | GET | 列出我的文章 |
| get_post | /apis/uc.api.content.halo.run/v1alpha1/posts/{name} | GET | 获取文章详情 |
| create_post | /apis/uc.api.content.halo.run/v1alpha1/posts | POST | 创建文章 |
| update_post | /apis/uc.api.content.halo.run/v1alpha1/posts/{name} | PUT | 更新文章 |
| get_post_draft | /apis/uc.api.content.halo.run/v1alpha1/posts/{name}/draft | GET | 获取草稿 |
| update_post_draft | /apis/uc.api.content.halo.run/v1alpha1/posts/{name}/draft | PUT | 更新草稿 |
| publish_post | /apis/uc.api.content.halo.run/v1alpha1/posts/{name}/publish | PUT | 发布文章 |
| unpublish_post | /apis/uc.api.content.halo.run/v1alpha1/posts/{name}/unpublish | PUT | 取消发布 |
| delete_post | /apis/uc.api.content.halo.run/v1alpha1/posts/{name}/recycle | DELETE | 删除文章 |
| list_categories | /apis/api.content.halo.run/v1alpha1/categories | GET | 列出分类 |
| list_tags | /apis/api.content.halo.run/v1alpha1/tags | GET | 列出标签 |
| upload_attachment | /apis/api.console.halo.run/v1alpha1/attachments/upload | POST | 上传附件 |
| upload_from_url | /apis/api.console.halo.run/v1alpha1/attachments/-/upload-from-url | POST | 从URL上传 |
| search_posts | /apis/api.halo.run/v1alpha1/indices/-/search | POST | 搜索文章 |
| list_comments | /apis/api.console.halo.run/v1alpha1/comments | GET | 列出评论 |

### 附录 B: 依赖包列表

```toml
[project]
dependencies = [
    "mcp>=0.1.0",
    "httpx>=0.25.0",
    "pydantic>=2.0.0",
    "python-dotenv>=1.0.0",
    "loguru>=0.7.0",
    "aiofiles>=23.0.0",
    "Pillow>=10.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "black>=23.7.0",
    "isort>=5.12.0",
    "mypy>=1.5.0",
    "pre-commit>=3.3.0",
]
```

### 附录 C: 许可证

本项目采用 MIT 许可证。

```
MIT License

Copyright (c) 2024 Halo MCP Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

**文档版本**: 1.0.0  
**最后更新**: 2024-01-01  
**维护者**: Halo MCP Team
