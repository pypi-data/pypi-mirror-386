# MCP Prompts 使用指南

## 📋 概述

Halo MCP Server 提供了 **10个智能写作助手 Prompts**，已完全注册并可在 Claude Desktop 中使用。这些 Prompts 覆盖了博客写作的全流程，从创作到优化、从翻译到校对。

## ✅ 注册状态

所有10个Prompts都已在 [`server.py`](src/halo-mcp-server/server.py) 中通过以下方式注册：

```python
@app.list_prompts()
async def list_prompts() -> list[Prompt]:
    """List available MCP prompts."""
    return BLOG_PROMPTS  # 包含全部10个Prompts

@app.get_prompt()
async def get_prompt(name: str, arguments: Dict[str, str]) -> str:
    """Get prompt content with arguments."""
    # 为每个Prompt生成对应的指导内容
```

## 🎯 完整Prompts列表

### 1. 博客写作助手 (`halo_blog_writing_assistant`)

**功能**: 帮助创建高质量的博客文章

**使用示例**:
```
请使用 halo_blog_writing_assistant 帮我写一篇文章：
- 主题：Python异步编程入门
- 目标读者：中级开发者
- 文章类型：技术教程
- 期望字数：2000
- 写作风格：专业且易懂
```

**参数说明**:
- `topic` (必填): 文章主题或标题
- `target_audience` (可选): 目标读者群体
- `article_type` (可选): 文章类型（教程、经验分享等）
- `word_count` (可选): 期望字数
- `tone` (可选): 写作风格

---

### 2. 内容优化器 (`halo_content_optimizer`)

**功能**: 优化现有文章的结构、可读性和吸引力

**使用示例**:
```
请使用 halo_content_optimizer 优化以下文章：

[粘贴文章内容]

优化重点：提高可读性和结构清晰度
目标长度：保持不变
```

**参数说明**:
- `content` (必填): 需要优化的文章内容
- `optimization_focus` (可选): 优化重点（可读性、结构、吸引力等）
- `target_length` (可选): 目标长度（扩展、压缩、保持不变）

---

### 3. SEO优化器 (`halo_seo_optimizer`)

**功能**: 优化文章的搜索引擎可见性

**使用示例**:
```
请使用 halo_seo_optimizer 优化这篇文章的SEO：
- 标题：Python异步编程完全指南
- 目标关键词：Python,asyncio,异步编程,协程
- 元描述长度：160

[粘贴文章内容]
```

**参数说明**:
- `title` (必填): 文章标题
- `content` (必填): 文章内容
- `target_keywords` (可选): 目标关键词（逗号分隔）
- `meta_description_length` (可选): 元描述长度限制

---

### 4. 标题生成器 (`halo_title_generator`)

**功能**: 为文章生成吸引人的标题

**使用示例**:
```
请使用 halo_title_generator 生成标题：
- 内容摘要：介绍如何使用Python的asyncio库实现高效的异步编程
- 标题风格：多样化
- 生成数量：5
```

**参数说明**:
- `content_summary` (必填): 文章内容摘要或主要观点
- `title_style` (可选): 标题风格（问题式、数字式、对比式等）
- `title_count` (可选): 生成标题数量（默认5个）

---

### 5. 摘要生成器 (`halo_excerpt_generator`)

**功能**: 为文章生成简洁有效的摘要

**使用示例**:
```
请使用 halo_excerpt_generator 为这篇文章生成摘要：
- 摘要长度：中等长度
- 摘要风格：概述式

[粘贴文章内容]
```

**参数说明**:
- `content` (必填): 文章完整内容
- `excerpt_length` (可选): 摘要长度（短/中/长，或具体字数）
- `excerpt_style` (可选): 摘要风格（概述式、亮点式、问题式）

---

### 6. 标签建议器 (`halo_tag_suggester`)

**功能**: 根据文章内容推荐合适的标签

**使用示例**:
```
请使用 halo_tag_suggester 为这篇文章推荐标签：
- 标题：Python异步编程完全指南
- 现有标签：Python,编程,后端开发
- 建议数量：5-8

[粘贴文章内容]
```

**参数说明**:
- `title` (必填): 文章标题
- `content` (必填): 文章内容
- `existing_tags` (可选): 现有标签列表（逗号分隔）
- `tag_count` (可选): 建议标签数量

---

### 7. 分类建议器 (`halo_category_suggester`)

**功能**: 根据文章内容推荐合适的分类

**使用示例**:
```
请使用 halo_category_suggester 为这篇文章推荐分类：
- 标题：Python异步编程完全指南
- 现有分类：Python开发,后端技术,编程教程,Web开发

[粘贴文章内容]
```

**参数说明**:
- `title` (必填): 文章标题
- `content` (必填): 文章内容
- `existing_categories` (可选): 现有分类列表（逗号分隔）

---

### 8. 内容翻译器 (`halo_content_translator`)

**功能**: 翻译文章内容并保持格式和风格

**使用示例**:
```
请使用 halo_content_translator 将这篇文章翻译成英文：
- 目标语言：英文
- 保持格式：是
- 翻译风格：意译

[粘贴中文内容]
```

**参数说明**:
- `content` (必填): 需要翻译的内容
- `target_language` (必填): 目标语言（英文、日文、韩文等）
- `preserve_formatting` (可选): 是否保持Markdown格式
- `translation_style` (可选): 翻译风格（直译、意译、本地化）

---

### 9. 内容校对器 (`halo_content_proofreader`)

**功能**: 检查和修正文章的语法、拼写和表达

**使用示例**:
```
请使用 halo_content_proofreader 校对这篇文章：
- 内容语言：中文
- 校对重点：全面检查

[粘贴文章内容]
```

**参数说明**:
- `content` (必填): 需要校对的内容
- `language` (可选): 内容语言（中文、英文等）
- `check_focus` (可选): 校对重点（语法、拼写、表达、逻辑等）

---

### 10. 系列规划器 (`halo_series_planner`)

**功能**: 规划和组织系列文章的结构和内容

**使用示例**:
```
请使用 halo_series_planner 规划一个系列文章：
- 系列主题：Python Web开发从入门到实战
- 目标读者：初学者到中级开发者
- 文章数量：8
- 难度递进：由浅入深
```

**参数说明**:
- `series_topic` (必填): 系列文章主题
- `target_audience` (可选): 目标读者群体
- `article_count` (可选): 计划文章数量
- `difficulty_progression` (可选): 难度递进方式

---

## 💡 实际应用场景

### 场景1: 技术博客完整创作流程

```
# 步骤1: 规划系列文章
使用 halo_series_planner 规划"Docker容器化实践"系列

# 步骤2: 创作单篇文章
使用 halo_blog_writing_assistant 写第一篇"Docker基础入门"

# 步骤3: 生成标题选项
使用 halo_title_generator 生成5个吸引人的标题

# 步骤4: 优化内容
使用 halo_content_optimizer 优化可读性

# 步骤5: SEO优化
使用 halo_seo_optimizer 优化搜索引擎友好性

# 步骤6: 生成摘要
使用 halo_excerpt_generator 生成文章摘要

# 步骤7: 推荐标签和分类
使用 halo_tag_suggester 推荐标签
使用 halo_category_suggester 推荐分类

# 步骤8: 最终校对
使用 halo_content_proofreader 全面校对
```

### 场景2: 多语言内容创作

```
# 中文创作
使用 halo_blog_writing_assistant 创作中文文章

# 翻译为英文
使用 halo_content_translator 翻译为英文

# 校对英文版本
使用 halo_content_proofreader 校对英文内容

# 分别优化SEO
使用 halo_seo_optimizer 分别优化中英文SEO
```

### 场景3: 内容升级改造

```
# 优化旧文章
使用 halo_content_optimizer 优化结构和表达

# 更新标题
使用 halo_title_generator 生成新标题

# 重新规划标签
使用 halo_tag_suggester 推荐新标签

# SEO优化
使用 halo_seo_optimizer 提升搜索排名

# 最终校对
使用 halo_content_proofreader 确保质量
```

---

## 🔧 技术实现

### Prompts定义位置
- **定义文件**: [`src/halo-mcp-server/prompts/blog_prompts.py`](src/halo-mcp-server/prompts/blog_prompts.py)
- **注册文件**: [`src/halo-mcp-server/server.py`](src/halo-mcp-server/server.py)

### 工作流程
1. Claude Desktop 通过MCP协议请求可用Prompts
2. Server返回10个Prompts的定义和参数说明
3. 用户在对话中引用Prompt名称
4. Claude调用对应的Prompt生成器函数
5. 返回专业的写作指导内容

---

## 📚 更多资源

### 示例代码
- [MCP Prompts使用示例](examples/mcp_prompts_examples.py) - 完整的使用示例和场景演示

### 验证工具
运行以下命令验证Prompts是否正确注册：
```bash
python verify_prompts.py
```

### 文档参考
- [Phase 1完成报告](PHASE1_COMPLETION_REPORT.md) - 详细的功能说明
- [Phase 1功能清单](PHASE1_FEATURES.md) - 完整的功能列表
- [README.md](README.md) - 项目主文档

---

## ⚠️ 注意事项

1. **Prompts ≠ Tools**
   - Prompts提供写作指导和建议
   - Tools执行具体的API操作（创建文章、上传附件等）
   - 两者配合使用效果最佳

2. **使用方式**
   - 在Claude Desktop对话中直接引用Prompt名称
   - 不需要显式调用，Claude会自动识别和使用
   - 提供的参数越详细，生成的指导越精准

3. **配合MCP Tools使用**
   - 使用Prompt生成内容后
   - 可以直接使用 `create_post` 等Tools发布到博客
   - 实现从创作到发布的完整自动化流程

---

## 🎉 总结

✅ **10个MCP Prompts已完全实现并注册**  
✅ **覆盖博客写作全流程**  
✅ **可在Claude Desktop中直接使用**  
✅ **提供专业的AI写作辅助**  

开始使用这些强大的写作助手，让AI帮助你创作更优质的博客内容吧！🚀
