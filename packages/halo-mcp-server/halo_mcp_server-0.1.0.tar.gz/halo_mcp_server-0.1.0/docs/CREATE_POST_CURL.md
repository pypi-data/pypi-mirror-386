# Halo API - 创建文章的 curl 命令

## 1. 完整的 curl 命令（创建草稿）

```bash
curl -X POST \
  'https://www.huangwh.com/apis/uc.api.content.halo.run/v1alpha1/posts' \
  -H 'Authorization: Bearer YOUR_TOKEN_HERE' \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json' \
  -d '{
    "apiVersion": "content.halo.run/v1alpha1",
    "kind": "Post",
    "metadata": {
      "name": "post-20251023210000",
      "annotations": {
        "content.halo.run/content-json": "{\"raw\":\"# 测试文章\n\n这是文章内容\",\"content\":\"# 测试文章\n\n这是文章内容\",\"rawType\":\"markdown\"}"
      }
    },
    "spec": {
      "title": "测试文章标题",
      "slug": "test-article",
      "releaseSnapshot": "",
      "headSnapshot": "",
      "baseSnapshot": "",
      "owner": "",
      "template": "",
      "cover": "",
      "deleted": false,
      "publish": false,
      "publishTime": null,
      "pinned": false,
      "allowComment": true,
      "visible": "PUBLIC",
      "priority": 0,
      "excerpt": {
        "autoGenerate": true,
        "raw": ""
      },
      "categories": [],
      "tags": [],
      "htmlMetas": []
    }
  }'
```

## 2. 使用文件的方式（推荐）

### 步骤 1：创建请求体文件 `create_post.json`

```json
{
  "apiVersion": "content.halo.run/v1alpha1",
  "kind": "Post",
  "metadata": {
    "name": "post-20251023210000",
    "annotations": {
      "content.halo.run/content-json": "{\"raw\":\"# Halo MCP Server 测试文章\n\n## 项目简介\n\n这是一个测试文章，用于验证 MCP 创建功能。\n\n### 核心特性\n\n- 功能 1\n- 功能 2\n- 功能 3\n\n```python\nprint('Hello World')\n```\",\"content\":\"# Halo MCP Server 测试文章\n\n## 项目简介\n\n这是一个测试文章，用于验证 MCP 创建功能。\n\n### 核心特性\n\n- 功能 1\n- 功能 2\n- 功能 3\n\n```python\nprint('Hello World')\n```\",\"rawType\":\"markdown\"}"
    }
  },
  "spec": {
    "title": "Halo MCP Server 测试文章",
    "slug": "halo-mcp-test-article",
    "releaseSnapshot": "",
    "headSnapshot": "",
    "baseSnapshot": "",
    "owner": "",
    "template": "",
    "cover": "",
    "deleted": false,
    "publish": false,
    "publishTime": null,
    "pinned": false,
    "allowComment": true,
    "visible": "PUBLIC",
    "priority": 0,
    "excerpt": {
      "autoGenerate": true,
      "raw": "这是文章摘要"
    },
    "categories": ["技术教程", "工具推荐"],
    "tags": ["MCP", "Halo", "Python"],
    "htmlMetas": []
  }
}
```

### 步骤 2：使用 curl 发送请求

```bash
curl -X POST \
  'https://www.huangwh.com/apis/uc.api.content.halo.run/v1alpha1/posts' \
  -H 'Authorization: Bearer YOUR_TOKEN_HERE' \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json' \
  -d @create_post.json
```

## 3. 关键字段说明

### metadata.name
- 格式：`post-YYYYMMDDHHmmss`
- 示例：`post-20251023210000`
- 说明：文章的唯一标识符，使用时间戳生成

### metadata.annotations["content.halo.run/content-json"]
- 这是一个 **JSON 字符串**（注意：是字符串，不是对象）
- 包含文章内容的结构化信息
- 必须手动转义引号和换行符

**结构：**
```json
{
  "raw": "Markdown 原文",
  "content": "Markdown 原文（Halo 会自动渲染）",
  "rawType": "markdown"
}
```

**转义后的示例：**
```json
"{\"raw\":\"# 标题\n\n内容\",\"content\":\"# 标题\n\n内容\",\"rawType\":\"markdown\"}"
```

### spec 字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| title | string | 文章标题 | "测试文章" |
| slug | string | URL 别名 | "test-article" |
| cover | string | 封面图片 URL | "" |
| pinned | boolean | 是否置顶 | false |
| allowComment | boolean | 是否允许评论 | true |
| visible | string | 可见性 | "PUBLIC" / "PRIVATE" |
| categories | array | 分类列表 | ["技术", "教程"] |
| tags | array | 标签列表 | ["Python", "MCP"] |
| excerpt.raw | string | 文章摘要 | "这是摘要" |
| excerpt.autoGenerate | boolean | 自动生成摘要 | true |

## 4. Python 脚本生成 JSON 字符串

由于 `content.halo.run/content-json` 需要是 JSON 字符串，这里提供 Python 脚本来生成：

```python
import json

content = """# Halo MCP Server 测试文章

## 项目简介

这是一个测试文章，用于验证 MCP 创建功能。

### 核心特性

- 功能 1
- 功能 2
- 功能 3

```python
print('Hello World')
```
"""

# 构造内容对象
content_obj = {
    "raw": content,
    "content": content,
    "rawType": "markdown"
}

# 序列化为 JSON 字符串（这就是要放入 annotations 的值）
content_json_string = json.dumps(content_obj, ensure_ascii=False)

print("content.halo.run/content-json 的值：")
print(content_json_string)

# 完整的请求体
post_data = {
    "apiVersion": "content.halo.run/v1alpha1",
    "kind": "Post",
    "metadata": {
        "name": "post-20251023210000",
        "annotations": {
            "content.halo.run/content-json": content_json_string
        }
    },
    "spec": {
        "title": "Halo MCP Server 测试文章",
        "slug": "halo-mcp-test-article",
        "releaseSnapshot": "",
        "headSnapshot": "",
        "baseSnapshot": "",
        "owner": "",
        "template": "",
        "cover": "",
        "deleted": False,
        "publish": False,
        "publishTime": None,
        "pinned": False,
        "allowComment": True,
        "visible": "PUBLIC",
        "priority": 0,
        "excerpt": {
            "autoGenerate": True,
            "raw": "这是文章摘要"
        },
        "categories": ["技术教程", "工具推荐"],
        "tags": ["MCP", "Halo", "Python"],
        "htmlMetas": []
    }
}

# 输出完整请求体
print("\n完整请求体：")
print(json.dumps(post_data, ensure_ascii=False, indent=2))

# 保存到文件
with open("create_post.json", "w", encoding="utf-8") as f:
    json.dump(post_data, f, ensure_ascii=False, indent=2)

print("\n✓ 已保存到 create_post.json")
```

## 5. 实际测试步骤

### 步骤 1：设置环境变量

```bash
export HALO_BASE_URL="https://www.huangwh.com"
export HALO_TOKEN="pat_your_token_here"
```

### 步骤 2：创建文章（草稿）

```bash
curl -X POST \
  "${HALO_BASE_URL}/apis/uc.api.content.halo.run/v1alpha1/posts" \
  -H "Authorization: Bearer ${HALO_TOKEN}" \
  -H "Content-Type: application/json" \
  -d @create_post.json \
  | jq '.'
```

### 步骤 3：获取创建的文章名称

从响应中提取 `metadata.name`，例如：`post-20251023210000`

### 步骤 4：发布文章（可选）

```bash
POST_NAME="post-20251023210000"  # 替换为实际的文章名称

curl -X PUT \
  "${HALO_BASE_URL}/apis/uc.api.content.halo.run/v1alpha1/posts/${POST_NAME}/publish" \
  -H "Authorization: Bearer ${HALO_TOKEN}" \
  -H "Content-Type: application/json"
```

## 6. 完整的 bash 测试脚本

```bash
#!/bin/bash

# 配置
HALO_BASE_URL="https://www.huangwh.com"
HALO_TOKEN="YOUR_TOKEN_HERE"
TIMESTAMP=$(date +%Y%m%d%H%M%S)
POST_NAME="post-${TIMESTAMP}"

# 文章内容
CONTENT="# 测试文章

## 简介

这是通过 curl 创建的测试文章。

### 特性

- 特性 1
- 特性 2

\`\`\`python
print('Hello World')
\`\`\`
"

# 构造 content-json（需要转义）
CONTENT_JSON=$(cat <<EOF
{"raw":"${CONTENT}","content":"${CONTENT}","rawType":"markdown"}
EOF
)

# 创建请求体
REQUEST_BODY=$(cat <<EOF
{
  "apiVersion": "content.halo.run/v1alpha1",
  "kind": "Post",
  "metadata": {
    "name": "${POST_NAME}",
    "annotations": {
      "content.halo.run/content-json": $(echo "${CONTENT_JSON}" | jq -R .)
    }
  },
  "spec": {
    "title": "Curl 测试文章 ${TIMESTAMP}",
    "slug": "curl-test-${TIMESTAMP}",
    "releaseSnapshot": "",
    "headSnapshot": "",
    "baseSnapshot": "",
    "owner": "",
    "template": "",
    "cover": "",
    "deleted": false,
    "publish": false,
    "publishTime": null,
    "pinned": false,
    "allowComment": true,
    "visible": "PUBLIC",
    "priority": 0,
    "excerpt": {
      "autoGenerate": true,
      "raw": ""
    },
    "categories": [],
    "tags": ["测试"],
    "htmlMetas": []
  }
}
EOF
)

echo "正在创建文章..."
echo "文章名称: ${POST_NAME}"

# 发送请求
RESPONSE=$(curl -s -X POST \
  "${HALO_BASE_URL}/apis/uc.api.content.halo.run/v1alpha1/posts" \
  -H "Authorization: Bearer ${HALO_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "${REQUEST_BODY}")

echo "响应:"
echo "${RESPONSE}" | jq '.'

# 检查是否成功
if echo "${RESPONSE}" | jq -e '.metadata.name' > /dev/null 2>&1; then
    echo "✓ 文章创建成功！"
    echo "文章名称: $(echo "${RESPONSE}" | jq -r '.metadata.name')"
else
    echo "✗ 文章创建失败！"
    exit 1
fi
```

## 7. 关键注意事项

### ⚠️ JSON 字符串转义

`content.halo.run/content-json` 字段的值必须是 **JSON 字符串**，不是 JSON 对象！

**错误示例：**
```json
{
  "annotations": {
    "content.halo.run/content-json": {
      "raw": "内容",
      "content": "内容"
    }
  }
}
```

**正确示例：**
```json
{
  "annotations": {
    "content.halo.run/content-json": "{\"raw\":\"内容\",\"content\":\"内容\",\"rawType\":\"markdown\"}"
  }
}
```

### ⚠️ Markdown 换行符

在 JSON 字符串中，换行符必须转义为 `\n`：

```json
"{\"raw\":\"# 标题\n\n内容\",\"content\":\"# 标题\n\n内容\",\"rawType\":\"markdown\"}"
```

### ⚠️ metadata.name 必须唯一

每次创建文章时，`metadata.name` 必须是唯一的，建议使用时间戳：

```python
from datetime import datetime
post_name = f"post-{datetime.now().strftime('%Y%m%d%H%M%S')}"
```

## 8. 响应示例

成功创建后，API 会返回：

```json
{
  "apiVersion": "content.halo.run/v1alpha1",
  "kind": "Post",
  "metadata": {
    "name": "post-20251023210000",
    "creationTimestamp": "2025-10-23T13:00:00Z",
    "labels": {},
    "annotations": {
      "content.halo.run/content-json": "{...}"
    }
  },
  "spec": {
    "title": "测试文章标题",
    "slug": "test-article",
    ...
  },
  "status": {
    "phase": "DRAFT",
    "permalink": "https://www.huangwh.com/archives/test-article",
    ...
  }
}
```

从响应中可以获取：
- `metadata.name` - 文章标识符
- `status.phase` - 文章状态（DRAFT/PUBLISHED）
- `status.permalink` - 文章链接
