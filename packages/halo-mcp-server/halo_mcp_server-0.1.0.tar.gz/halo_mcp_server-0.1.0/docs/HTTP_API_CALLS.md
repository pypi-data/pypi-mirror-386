# Halo MCP Server - 实际 HTTP API 调用详情

## 概述

本文档详细说明 Halo MCP Server 在更新文章时产生的实际 HTTP 调用。

---

## 1. 获取文章草稿 (GET Draft)

### HTTP 请求

```http
GET /apis/uc.api.content.halo.run/v1alpha1/posts/{post_name}/draft?patched=false HTTP/1.1
Host: www.huangwh.com
Authorization: Bearer pat_eyJraWQiOiIzdjBYZzh5Z1lWMV9uZm...
Content-Type: application/json
Accept: application/json
```

### curl 命令

```bash
curl -X GET \
  'https://www.huangwh.com/apis/uc.api.content.halo.run/v1alpha1/posts/post-20251023202023/draft?patched=false' \
  -H 'Authorization: Bearer YOUR_TOKEN_HERE' \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json'
```

### 响应示例

```json
{
  "spec": {
    "content": "{\"raw\":\"...\",\"content\":\"...\",\"rawType\":\"markdown\"}",
    "contentUpdateTimestamp": "2025-10-23T12:46:00Z"
  },
  "apiVersion": "content.halo.run/v1alpha1",
  "kind": "Snapshot",
  "metadata": {
    "name": "...",
    "creationTimestamp": "..."
  }
}
```

---

## 2. 更新文章草稿 (PUT Draft)

### HTTP 请求

```http
PUT /apis/uc.api.content.halo.run/v1alpha1/posts/{post_name}/draft HTTP/1.1
Host: www.huangwh.com
Authorization: Bearer pat_eyJraWQiOiIzdjBYZzh5Z1lWMV9uZm...
Content-Type: application/json
Accept: application/json
```

### 请求体结构 (Request Body)

**关键点：`spec.content` 是一个字典对象，httpx 会自动序列化为 JSON**

```python
{
  "spec": {
    "content": {                          # ← 注意：这里是字典对象，不是JSON字符串
      "raw": "# 标题\n\n内容...",          # ← 原始 Markdown
      "content": "# 标题\n\n内容...",      # ← 同样是 Markdown（Halo 会自己渲染）
      "rawType": "markdown"                # ← 标记为 markdown 类型
    },
    "contentUpdateTimestamp": "2025-10-23T12:46:00Z"
  },
  "apiVersion": "content.halo.run/v1alpha1",
  "kind": "Snapshot",
  "metadata": {
    "name": "post-20251023202023-snapshot-xyz",
    "creationTimestamp": "2025-10-23T12:20:00Z"
  }
}
```

### 完整 JSON 请求体示例

```json
{
  "spec": {
    "content": {
      "raw": "# Halo MCP Server - 让 AI 助手管理你的博客\n\n## 🎉 项目简介\n\n**Halo MCP Server** 是一个基于 Model Context Protocol (MCP) 的博客管理工具。\n\n### ✨ 核心特性\n\n- 🤖 **AI 驱动**\n- 📝 **文章管理**",
      "content": "# Halo MCP Server - 让 AI 助手管理你的博客\n\n## 🎉 项目简介\n\n**Halo MCP Server** 是一个基于 Model Context Protocol (MCP) 的博客管理工具。\n\n### ✨ 核心特性\n\n- 🤖 **AI 驱动**\n- 📝 **文章管理**",
      "rawType": "markdown"
    },
    "contentUpdateTimestamp": "2025-10-23T12:46:00Z"
  },
  "apiVersion": "content.halo.run/v1alpha1",
  "kind": "Snapshot",
  "metadata": {
    "name": "post-20251023202023-snapshot-abc123",
    "creationTimestamp": "2025-10-23T12:20:00Z",
    "labels": {},
    "annotations": {}
  }
}
```

### curl 命令（使用文件）

```bash
# 1. 将上面的 JSON 保存为 draft_body.json

# 2. 执行更新
curl -X PUT \
  'https://www.huangwh.com/apis/uc.api.content.halo.run/v1alpha1/posts/post-20251023202023/draft' \
  -H 'Authorization: Bearer YOUR_TOKEN_HERE' \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json' \
  -d @draft_body.json
```

### curl 命令（直接传递数据）

```bash
curl -X PUT \
  'https://www.huangwh.com/apis/uc.api.content.halo.run/v1alpha1/posts/post-20251023202023/draft' \
  -H 'Authorization: Bearer YOUR_TOKEN_HERE' \
  -H 'Content-Type: application/json' \
  -d '{
    "spec": {
      "content": {
        "raw": "# 测试标题\n\n测试内容",
        "content": "# 测试标题\n\n测试内容",
        "rawType": "markdown"
      }
    },
    "apiVersion": "content.halo.run/v1alpha1",
    "kind": "Snapshot",
    "metadata": {
      "name": "test-snapshot"
    }
  }'
```

---

## 3. 发布文章 (PUT Publish)

### HTTP 请求

```http
PUT /apis/uc.api.content.halo.run/v1alpha1/posts/{post_name}/publish HTTP/1.1
Host: www.huangwh.com
Authorization: Bearer pat_eyJraWQiOiIzdjBYZzh5Z1lWMV9uZm...
Content-Type: application/json
Accept: application/json
```

### curl 命令

```bash
curl -X PUT \
  'https://www.huangwh.com/apis/uc.api.content.halo.run/v1alpha1/posts/post-20251023202023/publish' \
  -H 'Authorization: Bearer YOUR_TOKEN_HERE' \
  -H 'Content-Type: application/json'
```

---

## 4. Python httpx 示例代码

### 完整示例

```python
import httpx
import asyncio


async def update_halo_post():
    """使用 httpx 更新 Halo 文章"""
    
    base_url = "https://www.huangwh.com"
    token = "YOUR_TOKEN_HERE"
    post_name = "post-20251023202023"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient(base_url=base_url) as client:
        # 1. 获取草稿
        draft_url = f"/apis/uc.api.content.halo.run/v1alpha1/posts/{post_name}/draft"
        response = await client.get(
            draft_url,
            params={"patched": "false"},
            headers=headers
        )
        draft = response.json()
        print(f"✓ 获取草稿成功: {response.status_code}")
        
        # 2. 更新内容
        new_content = """# 测试标题

## 测试二级标题

- 列表项 1
- 列表项 2

```python
print("Hello World")
```
"""
        
        # 关键：直接赋值字典对象，不要使用 json.dumps()
        draft["spec"]["content"] = {
            "raw": new_content,
            "content": new_content,
            "rawType": "markdown"
        }
        
        # 3. 发送更新请求
        response = await client.put(
            draft_url,
            headers=headers,
            json=draft  # httpx 会自动序列化为 JSON
        )
        print(f"✓ 更新草稿成功: {response.status_code}")
        
        # 4. 发布文章
        publish_url = f"/apis/uc.api.content.halo.run/v1alpha1/posts/{post_name}/publish"
        response = await client.put(
            publish_url,
            headers=headers
        )
        print(f"✓ 发布文章成功: {response.status_code}")


# 运行
asyncio.run(update_halo_post())
```

---

## 5. JavaScript/Node.js fetch 示例

```javascript
async function updateHaloPost() {
  const baseUrl = "https://www.huangwh.com";
  const token = "YOUR_TOKEN_HERE";
  const postName = "post-20251023202023";
  
  const headers = {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json",
    "Accept": "application/json"
  };
  
  // 1. 获取草稿
  const draftUrl = `${baseUrl}/apis/uc.api.content.halo.run/v1alpha1/posts/${postName}/draft?patched=false`;
  let response = await fetch(draftUrl, { headers });
  const draft = await response.json();
  console.log("✓ 获取草稿成功");
  
  // 2. 更新内容
  const newContent = `# 测试标题

## 测试二级标题

- 列表项 1
- 列表项 2
`;
  
  draft.spec.content = {
    raw: newContent,
    content: newContent,
    rawType: "markdown"
  };
  
  // 3. 发送更新请求
  response = await fetch(draftUrl, {
    method: "PUT",
    headers,
    body: JSON.stringify(draft)
  });
  console.log("✓ 更新草稿成功");
  
  // 4. 发布文章
  const publishUrl = `${baseUrl}/apis/uc.api.content.halo.run/v1alpha1/posts/${postName}/publish`;
  response = await fetch(publishUrl, {
    method: "PUT",
    headers
  });
  console.log("✓ 发布文章成功");
}

updateHaloPost();
```

---

## 6. 关键注意事项

### ⚠️ JSON 序列化问题

**错误做法（会导致双重编码）：**

```python
# ❌ 错误：不要这样做
draft["spec"]["content"] = json.dumps({
    "raw": content,
    "content": content,
    "rawType": "markdown"
})
# 这会导致 \n 被转义成 \\n
```

**正确做法：**

```python
# ✅ 正确：直接赋值字典对象
draft["spec"]["content"] = {
    "raw": content,
    "content": content,
    "rawType": "markdown"
}
# httpx 的 json= 参数会自动序列化
```

### ⚠️ Markdown 处理

- **raw**: 原始 Markdown 文本（用于编辑器）
- **content**: 也是 Markdown 文本（Halo 会自动渲染成 HTML）
- **rawType**: 必须设置为 `"markdown"`

**不需要手动将 Markdown 转换为 HTML**，Halo 会自己处理！

### ⚠️ 认证 Token

获取方式：
1. 登录 Halo 后台
2. 进入"个人中心" → "个人令牌"
3. 创建新令牌
4. 格式：`pat_xxx...`

---

## 7. 测试步骤

### 使用 curl 测试

```bash
# 设置变量
BASE_URL="https://www.huangwh.com"
TOKEN="pat_your_token_here"
POST_NAME="post-20251023202023"

# 1. 获取草稿
curl -X GET \
  "${BASE_URL}/apis/uc.api.content.halo.run/v1alpha1/posts/${POST_NAME}/draft?patched=false" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  | jq '.' > draft.json

# 2. 编辑 draft.json，修改 spec.content

# 3. 更新草稿
curl -X PUT \
  "${BASE_URL}/apis/uc.api.content.halo.run/v1alpha1/posts/${POST_NAME}/draft" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d @draft.json

# 4. 发布文章
curl -X PUT \
  "${BASE_URL}/apis/uc.api.content.halo.run/v1alpha1/posts/${POST_NAME}/publish" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json"
```

---

## 8. 完整的请求体示例文件

将以下内容保存为 `draft_update.json` 并用于测试：

```json
{
  "spec": {
    "content": {
      "raw": "# Halo MCP Server\n\n测试内容\n\n## 功能特性\n\n- 功能 1\n- 功能 2\n\n```python\nprint('Hello')\n```",
      "content": "# Halo MCP Server\n\n测试内容\n\n## 功能特性\n\n- 功能 1\n- 功能 2\n\n```python\nprint('Hello')\n```",
      "rawType": "markdown"
    },
    "contentUpdateTimestamp": "2025-10-23T12:46:00Z"
  },
  "apiVersion": "content.halo.run/v1alpha1",
  "kind": "Snapshot",
  "metadata": {
    "name": "your-snapshot-name-here"
  }
}
```

---

## 总结

MCP Server 更新文章的完整流程：

1. **GET** - 获取当前草稿
2. **修改** - 更新 `spec.content` 字典对象
3. **PUT** - 发送更新后的草稿
4. **PUT** - 发布文章

**关键点**：
- 使用字典对象，不要手动 `json.dumps()`
- Markdown 内容放在 `raw` 和 `content` 字段
- `rawType` 必须是 `"markdown"`
- Halo 会自动渲染 Markdown 为 HTML
