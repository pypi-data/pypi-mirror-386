# Halo MCP Phase 1 功能文档

## 概述

Phase 1 为 Halo MCP 服务器添加了全面的博客管理功能，包括分类管理、标签管理、附件管理和智能写作助手。

## 🗂️ 分类管理工具

### 可用工具

| 工具名称 | 功能描述 | 主要参数 |
|---------|---------|---------|
| `list_categories` | 列出所有分类 | `keyword`, `page`, `size` |
| `get_category` | 获取分类详情 | `name` (必填) |
| `create_category` | 创建新分类 | `display_name` (必填), `description`, `slug` |
| `update_category` | 更新分类信息 | `name` (必填), `display_name`, `description` |
| `delete_category` | 删除分类 | `name` (必填) |
| `get_category_posts` | 获取分类下的文章 | `name` (必填), `page`, `size` |

### 使用示例

```python
# 创建新分类
await create_category(
    display_name="技术分享",
    description="分享技术心得和经验",
    slug="tech-sharing"
)

# 列出所有分类
categories = await list_categories(
    keyword="技术",
    page=0,
    size=20
)

# 获取分类下的文章
posts = await get_category_posts(
    name="tech-sharing",
    page=0,
    size=10
)
```

## 🏷️ 标签管理工具

### 可用工具

| 工具名称 | 功能描述 | 主要参数 |
|---------|---------|---------|
| `list_tags` | 列出所有标签 | `keyword`, `page`, `size` |
| `get_tag` | 获取标签详情 | `name` (必填) |
| `create_tag` | 创建新标签 | `display_name` (必填), `color`, `slug` |
| `update_tag` | 更新标签信息 | `name` (必填), `display_name`, `color` |
| `delete_tag` | 删除标签 | `name` (必填) |
| `get_tag_posts` | 获取标签下的文章 | `name` (必填), `page`, `size` |
| `list_console_tags` | 列出控制台标签 | `keyword`, `page`, `size` |

### 使用示例

```python
# 创建新标签
await create_tag(
    display_name="Python",
    color="#3776ab",
    slug="python"
)

# 搜索标签
tags = await list_tags(
    keyword="Python",
    page=0,
    size=50
)

# 获取标签下的文章
posts = await get_tag_posts(
    name="python",
    page=0,
    size=10
)
```

## 📎 附件管理工具

### 可用工具

| 工具名称 | 功能描述 | 主要参数 |
|---------|---------|---------|
| `list_attachments` | 搜索和列出附件 | `keyword`, `accepts`, `group_name` |
| `get_attachment` | 获取附件详情 | `name` (必填) |
| `upload_attachment` | 上传本地文件 | `file_path` (必填), `group_name` |
| `upload_attachment_from_url` | 从URL上传文件 | `url` (必填), `group_name` |
| `delete_attachment` | 删除附件 | `name` (必填) |
| `create_attachment_group` | 创建附件分组 | `display_name` (必填) |
| `get_attachment_policies` | 获取存储策略 | 无参数 |

### 使用示例

```python
# 上传本地文件
attachment = await upload_attachment(
    file_path="/path/to/image.jpg",
    group_name="blog-images"
)

# 从URL上传文件
attachment = await upload_attachment_from_url(
    url="https://example.com/image.jpg",
    group_name="external-images"
)

# 搜索图片附件
images = await list_attachments(
    keyword="screenshot",
    accepts=["image/*"],
    page=0,
    size=20
)

# 创建附件分组
group = await create_attachment_group(
    display_name="博客配图"
)
```

## ✨ MCP Prompts - 智能写作助手

### 可用 Prompts

| Prompt 名称 | 功能描述 | 主要参数 |
|------------|---------|---------|
| `halo_blog_writing_assistant` | 博客写作助手 | `topic`, `style`, `target_audience` |
| `halo_content_optimizer` | 内容优化器 | `content`, `optimization_goals` |
| `halo_seo_optimizer` | SEO优化器 | `content`, `target_keywords` |
| `halo_title_generator` | 标题生成器 | `content`, `style`, `count` |
| `halo_excerpt_generator` | 摘要生成器 | `content`, `max_length` |
| `halo_tag_suggester` | 标签建议器 | `content`, `max_tags` |
| `halo_category_suggester` | 分类建议器 | `content`, `existing_categories` |
| `halo_content_translator` | 内容翻译器 | `content`, `target_language` |
| `halo_content_proofreader` | 内容校对器 | `content`, `language` |
| `halo_series_planner` | 系列规划器 | `topic`, `target_audience`, `article_count` |

### 使用示例

```python
# 使用写作助手
writing_help = await halo_blog_writing_assistant(
    topic="Python异步编程",
    style="技术教程",
    target_audience="中级开发者"
)

# 生成文章标题
titles = await halo_title_generator(
    content="这是一篇关于Python异步编程的文章...",
    style="吸引人的",
    count=5
)

# 建议标签
tags = await halo_tag_suggester(
    content="文章内容...",
    max_tags=8
)

# SEO优化
seo_content = await halo_seo_optimizer(
    content="原始内容...",
    target_keywords=["Python", "异步编程", "asyncio"]
)

# 规划文章系列
series_plan = await halo_series_planner(
    topic="Python进阶教程",
    target_audience="中高级开发者",
    article_count=10
)
```

## 🚀 快速开始

### 1. 启动服务器

```bash
cd src
python -m halo_mcp_server.server
```

### 2. 配置环境变量

确保 `.env` 文件包含必要的配置：

```env
HALO_BASE_URL=https://your-halo-site.com
HALO_TOKEN=your-api-token
# 或者使用用户名密码
HALO_USERNAME=your-username
HALO_PASSWORD=your-password
```

### 3. 验证功能

运行测试脚本验证所有功能：

```bash
python test_phase1.py
```

## 📋 功能特性

### ✅ 已实现功能

- **完整的分类管理** - 创建、读取、更新、删除分类
- **全面的标签管理** - 支持颜色、搜索、分组管理
- **强大的附件系统** - 本地上传、URL上传、分组管理
- **智能写作助手** - 10个专业的写作和优化工具
- **MCP标准兼容** - 完全符合MCP协议规范
- **错误处理** - 完善的异常处理和错误信息
- **类型安全** - 完整的类型注解和验证

### 🔄 工作流程集成

所有工具都可以无缝集成到写作工作流程中：

1. **内容创作** → 使用写作助手和系列规划器
2. **内容优化** → 使用SEO优化器和内容优化器  
3. **分类整理** → 使用分类和标签管理工具
4. **媒体管理** → 使用附件管理工具
5. **发布准备** → 使用标题生成器和摘要生成器

## 🛠️ 技术实现

- **模块化设计** - 每个功能模块独立，易于维护
- **异步支持** - 所有API调用都支持异步操作
- **缓存优化** - 智能缓存减少API调用
- **错误恢复** - 自动重试和错误恢复机制
- **扩展性** - 易于添加新功能和工具

## 📚 更多资源

- [API文档](./halo_apis_docs/)
- [使用示例](./examples/)
- [开发指南](./DEVELOPMENT.md)
- [项目总结](./PROJECT_SUMMARY.md)