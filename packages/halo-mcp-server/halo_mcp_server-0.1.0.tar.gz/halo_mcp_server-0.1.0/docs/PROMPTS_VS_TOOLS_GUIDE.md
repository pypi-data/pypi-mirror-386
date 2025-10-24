# Prompts vs Tools 使用指南

## 🤔 常见疑问解答

### Q1: 为什么在MCP工具列表中看不到10个写作助手Prompts？

**答**：这是MCP协议的设计特性，不是bug！

MCP定义了两种不同的能力：

| 类型 | 显示位置 | 用途 | 调用方式 |
|------|---------|------|---------|
| **Tools** | ✅ 工具列表中可见 | 执行具体操作（API调用） | Claude主动调用 |
| **Prompts** | ❌ 工具列表中隐藏 | 生成内容指导 | 自然对话触发 |

**您看到的30个接口** = Tools（文章、分类、标签等操作）  
**10个写作助手** = Prompts（内容生成指导）

---

### Q2: 用户真的需要输入 `halo_blog_writing_assistant` 这样的长串吗？

**答**：**完全不需要！**这正是MCP的优势所在。

#### ❌ 错误理解（不需要这样做）
```
使用 halo_blog_writing_assistant 帮我写一篇关于Python的文章，
参数：topic=Python异步编程，target_audience=中级开发者...
```

#### ✅ 正确使用（自然对话）
```
帮我写一篇关于Python异步编程的技术教程
```

**Claude会自动**：
1. 理解您想要"写作"
2. 内部调用 `halo_blog_writing_assistant` Prompt
3. 生成专业的文章内容

---

### Q3: Prompts和Tools有什么区别？

#### 🔧 **Tools（30个）** - 执行操作

**特点**：
- 直接与Halo API交互
- 执行CRUD操作（创建、读取、更新、删除）
- 可以看到调用日志

**示例**：
```python
# create_post Tool
async def create_post_tool(client, arguments):
    # 调用Halo API创建文章
    response = await client.post("/apis/...", json=data)
    return response
```

**用户使用**：
```
创建一篇文章（Claude调用create_post）
列出所有分类（Claude调用list_categories）
上传图片（Claude调用upload_attachment）
```

---

#### 💡 **Prompts（10个）** - 生成内容

**特点**：
- 不调用API，只生成文本
- 提供专业的写作指导
- 帮助Claude更好地理解需求

**示例**：
```python
# halo_blog_writing_assistant Prompt
def _generate_writing_assistant_prompt(args):
    return f"""你是一位专业的博客写作助手。
    请根据以下要求创建文章：
    - 主题：{args['topic']}
    - 目标读者：{args['target_audience']}
    ..."""
```

**用户使用**：
```
写一篇关于Python的教程（触发写作Prompt）
优化这篇文章（触发优化Prompt）
生成SEO标题（触发标题生成Prompt）
```

---

## 🎯 实际使用场景

### 场景1: 完整的博客创作流程

```
用户：帮我写一篇关于"如何设计短链系统"的Java技术文章并发布

Claude做了什么：
1. 触发 halo_blog_writing_assistant Prompt
   → 生成2000字的专业文章
   
2. 自动调用 halo_tag_suggester Prompt
   → 推荐标签：Java、系统设计、短链系统...
   
3. 自动调用 halo_category_suggester Prompt
   → 推荐分类：Java开发、系统设计
   
4. 调用 create_post Tool
   → 发布文章到Halo博客
   
5. 返回结果：文章已发布成功！
```

**用户只需要一句话**，Claude自动完成全部流程！

---

### 场景2: 内容优化

```
用户：这篇文章太专业了，帮我改得更通俗易懂

Claude做了什么：
1. 调用 get_post Tool
   → 获取文章内容
   
2. 触发 halo_content_optimizer Prompt
   → 生成优化后的内容（更通俗的表达）
   
3. 调用 update_post_draft Tool
   → 保存优化后的草稿
   
4. 调用 publish_post Tool
   → 重新发布
```

---

### 场景3: SEO优化

```
用户：帮我优化这篇文章的SEO

Claude做了什么：
1. 调用 get_post Tool
   → 获取文章内容
   
2. 触发 halo_seo_optimizer Prompt
   → 生成SEO优化建议：
     - 优化后的标题
     - Meta描述
     - 关键词布局建议
     
3. 触发 halo_title_generator Prompt
   → 生成5个SEO友好的标题选项
   
4. 询问用户选择哪个标题
   
5. 调用 update_post Tool
   → 应用优化
```

---

## 💬 自然对话示例

### 写作相关

| 用户输入 | 触发的Prompt | 效果 |
|---------|-------------|------|
| "帮我写一篇Python教程" | `halo_blog_writing_assistant` | 生成完整文章 |
| "这篇文章太长了，精简一下" | `halo_content_optimizer` | 优化内容长度 |
| "写5个吸引人的标题" | `halo_title_generator` | 生成标题选项 |
| "生成文章摘要" | `halo_excerpt_generator` | 生成摘要 |
| "推荐合适的标签" | `halo_tag_suggester` | 推荐标签 |

### 管理相关

| 用户输入 | 调用的Tool | 效果 |
|---------|-----------|------|
| "创建一篇文章" | `create_post` | 创建文章 |
| "列出所有文章" | `list_my_posts` | 列出文章 |
| "发布这篇文章" | `publish_post` | 发布文章 |
| "上传图片" | `upload_attachment` | 上传附件 |
| "删除草稿" | `delete_post` | 删除文章 |

---

## 🎨 10个Prompts详细说明

### 1. 博客写作助手 (`halo_blog_writing_assistant`)

**触发方式**：
- "写一篇关于XXX的文章"
- "帮我创作XXX主题的教程"
- "生成一篇XXX类型的博客"

**参数（Claude自动识别）**：
- 主题
- 目标读者
- 文章类型
- 字数要求
- 写作风格

---

### 2. 内容优化器 (`halo_content_optimizer`)

**触发方式**：
- "优化这篇文章"
- "让这篇文章更通俗"
- "改进文章结构"

**优化方向**：
- 可读性
- 结构清晰度
- 吸引力
- 专业性

---

### 3. SEO优化器 (`halo_seo_optimizer`)

**触发方式**：
- "优化SEO"
- "提升搜索排名"
- "让文章更容易被搜索到"

**优化内容**：
- 标题优化
- Meta描述
- 关键词布局
- 内部链接建议

---

### 4. 标题生成器 (`halo_title_generator`)

**触发方式**：
- "生成标题"
- "给我几个标题选项"
- "写个吸引人的标题"

**生成风格**：
- 问题式
- 数字式
- 对比式
- 悬念式

---

### 5. 摘要生成器 (`halo_excerpt_generator`)

**触发方式**：
- "生成摘要"
- "写一段简介"
- "提炼文章要点"

**长度选项**：
- 短（80-120字）
- 中（120-200字）
- 长（200-300字）

---

### 6. 标签建议器 (`halo_tag_suggester`)

**触发方式**：
- "推荐标签"
- "这篇文章适合什么标签"
- "生成相关标签"

**推荐依据**：
- 文章内容分析
- 技术栈识别
- 主题关联

---

### 7. 分类建议器 (`halo_category_suggester`)

**触发方式**：
- "推荐分类"
- "这篇文章属于什么类别"
- "选择合适的分类"

**推荐逻辑**：
- 内容主题匹配
- 现有分类体系
- 层级关系

---

### 8. 内容翻译器 (`halo_content_translator`)

**触发方式**：
- "翻译成英文"
- "将这篇文章翻译为日文"
- "生成多语言版本"

**支持语言**：
- 英文、日文、韩文等
- 保持Markdown格式
- 技术术语准确

---

### 9. 内容校对器 (`halo_content_proofreader`)

**触发方式**：
- "校对文章"
- "检查语法错误"
- "修正拼写问题"

**检查项目**：
- 语法错误
- 拼写错误
- 表达优化
- 逻辑一致性

---

### 10. 系列规划器 (`halo_series_planner`)

**触发方式**：
- "规划一个系列文章"
- "设计XXX专题的文章计划"
- "创建系列教程大纲"

**规划内容**：
- 文章数量
- 主题分配
- 难度递进
- 学习路径

---

## 🔄 Prompts与Tools的配合

### 完整工作流示例

```
用户：帮我写一篇关于Docker容器化的文章并发布

流程：
┌─────────────────────────────────────────┐
│ 1. halo_blog_writing_assistant Prompt  │
│    → 生成Docker容器化文章（2000字）      │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ 2. halo_title_generator Prompt         │
│    → 生成5个标题选项                    │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ 3. halo_tag_suggester Prompt           │
│    → 推荐标签：Docker、容器化、DevOps   │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ 4. halo_category_suggester Prompt      │
│    → 推荐分类：云原生、系统运维          │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ 5. halo_seo_optimizer Prompt           │
│    → 优化关键词和Meta描述               │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ 6. create_post Tool                    │
│    → 调用Halo API创建文章               │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ 7. publish_post Tool                   │
│    → 调用Halo API发布文章               │
└─────────────────────────────────────────┘

结果：文章创建并发布成功！✅
```

**用户只需一句话**，Claude自动完成7个步骤！

---

## ✨ 总结

### 为什么看不到Prompts？

✅ **这是正确的设计**  
- Prompts是"隐形的智能助手"
- 通过自然对话自动触发
- 无需记忆复杂命令

### 如何使用Prompts？

✅ **用自然语言描述需求**  
- "写一篇XXX文章" → 自动触发写作Prompt
- "优化文章" → 自动触发优化Prompt
- "生成标题" → 自动触发标题生成Prompt

### Prompts vs Tools的关系

✅ **完美配合**  
- **Prompts** = 内容生成（AI智慧）
- **Tools** = 操作执行（API调用）
- **结合** = 完整的自动化流程

---

## 📚 相关文档

- [MCP_PROMPTS_GUIDE.md](MCP_PROMPTS_GUIDE.md) - Prompts详细使用指南
- [README.md](README.md) - 项目主文档
- [examples/mcp_prompts_examples.py](examples/mcp_prompts_examples.py) - 代码示例

---

**记住**：MCP的魅力在于"隐形的强大"——用户不需要了解底层实现，只需用自然语言描述需求，Claude会自动选择合适的Prompts和Tools完成任务！🚀
