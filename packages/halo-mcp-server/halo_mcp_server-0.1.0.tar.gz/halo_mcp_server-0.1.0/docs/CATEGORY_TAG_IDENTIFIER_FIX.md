# Halo MCP 分类和标签标识符修复说明

## 问题描述

在使用 Halo MCP 工具更新文章的分类和标签时，发现了一个容易导致错误的问题：

**错误用法**：使用显示名称（display_name）作为分类和标签的标识符
```json
{
  "categories": ["开发", "Linux"],
  "tags": ["Halo", "Docker"]
}
```

**正确用法**：必须使用内部标识符（metadata.name）
```json
{
  "categories": ["category-kfyBb", "category-yJfRu"],
  "tags": ["c33ceabb-d8f1-4711-8991-bb8f5c92ad7c", "tag-wgSGm"]
}
```

## 问题原因

Halo 系统内部使用唯一的内部标识符（name字段）来关联文章与分类/标签，而不是使用用户可见的显示名称（displayName字段）。虽然更新操作使用显示名称不会报错，但实际上不会正确关联到分类和标签对象。

## 解决方案

### 1. 更新工具描述

已在以下文件中更新了工具描述，明确说明必须使用内部标识符：

#### `src/halo-mcp-server/tools/post_tools.py`

**create_post 工具**：
- `categories` 参数描述更新为：
  > 分类内部标识符列表（必须使用分类的 metadata.name 字段，而非 displayName！例如：['category-yJfRu', 'category-kfyBb']）。可通过 list_categories 工具获取所有分类的标识符。

- `tags` 参数描述更新为：
  > 标签内部标识符列表（必须使用标签的 metadata.name 字段，而非 displayName！例如：['tag-LrsQn', 'c33ceabb-d8f1-4711-8991-bb8f5c92ad7c']）。可通过 list_tags 工具获取所有标签的标识符。

**update_post 工具**：
- 同样更新了 `categories` 和 `tags` 参数的描述，说明必须使用内部标识符。

#### `src/halo-mcp-server/tools/category_tools.py`

**list_categories 工具**：
- 描述更新为：
  > 列出所有分类，支持分页和关键词搜索。返回结果中 items 列表的每个分类对象包含：'name' 字段（内部标识符，如 'category-yJfRu'）和 'display_name' 字段（显示名称，如 'Linux'）。重要：创建或更新文章时必须使用 'name' 字段作为分类标识符，而非 'display_name'。

#### `src/halo-mcp-server/tools/tag_tools.py`

**list_tags 工具**：
- 描述更新为：
  > 列出所有标签，支持分页和关键词搜索。返回结果中 items 列表的每个标签对象包含：metadata.name 字段（内部标识符，如 'tag-LrsQn' 或 'c33ceabb-d8f1-4711-8991-bb8f5c92ad7c'）和 spec.displayName 字段（显示名称，如 'Linux'）。重要：创建或更新文章时必须使用 metadata.name 字段作为标签标识符，而非 spec.displayName。

### 2. 使用流程

#### 步骤 1：获取分类和标签的内部标识符

**获取所有分类**：
```bash
list_categories()
```

返回示例：
```json
{
  "items": [
    {
      "name": "category-yJfRu",         // 内部标识符（使用这个！）
      "display_name": "Linux",          // 显示名称（不要用）
      "slug": "linux",
      "post_count": 8
    },
    {
      "name": "category-kfyBb",
      "display_name": "开发",
      "slug": "kai-fa",
      "post_count": 6
    }
  ]
}
```

**获取所有标签**：
```bash
list_tags()
```

返回示例：
```json
{
  "items": [
    {
      "metadata": {
        "name": "tag-LrsQn"             // 内部标识符（使用这个！）
      },
      "spec": {
        "displayName": "Linux"          // 显示名称（不要用）
      }
    },
    {
      "metadata": {
        "name": "c33ceabb-d8f1-4711-8991-bb8f5c92ad7c"
      },
      "spec": {
        "displayName": "Halo"
      }
    }
  ]
}
```

#### 步骤 2：使用内部标识符更新文章

```bash
update_post(
  name="post-20251023220745",
  categories=["category-kfyBb"],                                    # 使用内部标识符
  tags=["c33ceabb-d8f1-4711-8991-bb8f5c92ad7c"]                    # 使用内部标识符
)
```

### 3. 标识符映射示例

基于实际数据的映射表：

**分类映射**：
| 显示名称 | 内部标识符 | Slug |
|---------|-----------|------|
| Linux | `category-yJfRu` | linux |
| 开发 | `category-kfyBb` | kai-fa |
| 默认分类 | `76514a40-6ef1-4ed9-b58a-e26945bde3ca` | default |

**标签映射**：
| 显示名称 | 内部标识符 | Slug |
|---------|-----------|------|
| Linux | `tag-LrsQn` | linux |
| Docker | `tag-wgSGm` | docker |
| Halo | `c33ceabb-d8f1-4711-8991-bb8f5c92ad7c` | halo |
| Java | `tag-DbWCh` | java |
| Git | `tag-RsHFe` | git |
| Mysql | `tag-fEujv` | mysql |
| Kafka | `tag-fuyQR` | kafka |
| 梯子 | `tag-ExpaT` | ti-zi |
| Nas | `tag-Nlpql` | nas |
| 威联通 | `tag-HvhsG` | wei-lian-tong |

## 验证方法

### 验证分类和标签是否正确关联

1. 更新文章后，使用 `get_post` 查看文章详情：
```bash
get_post(name="post-20251023220745")
```

2. 检查返回的 `spec.categories` 和 `spec.tags` 字段是否包含正确的内部标识符：
```json
{
  "spec": {
    "categories": ["category-kfyBb"],                              // ✅ 正确
    "tags": ["c33ceabb-d8f1-4711-8991-bb8f5c92ad7c"]              // ✅ 正确
  }
}
```

3. 使用 `list_categories` 检查分类的文章数是否更新：
```json
{
  "name": "category-kfyBb",
  "display_name": "开发",
  "post_count": 6,              // 如果关联成功，这个数字应该增加
  "visible_post_count": 6
}
```

## 相关经验教训

已将此经验添加到记忆系统：

**记忆标题**：Halo分类标签更新规范

**记忆内容**：
更新Halo文章的分类和标签时，必须使用其内部标识符（name字段），而非显示名称（display_name或displayName），否则会导致关联失败。

## 总结

此次更新确保了AI助手在使用Halo MCP工具时能够：

1. ✅ 清楚地知道必须使用内部标识符而不是显示名称
2. ✅ 了解如何通过 `list_categories` 和 `list_tags` 获取内部标识符
3. ✅ 看到具体的示例说明正确的格式
4. ✅ 避免使用错误的参数导致分类和标签关联失败

这将大大减少因参数使用错误而导致的操作失败，提升用户体验。
