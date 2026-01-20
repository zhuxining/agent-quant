# Agent Quant API 文档

本文档提供了 Agent Quant 系统 HTTP API 端点的完整参考。

---

## 目录

- [认证](#认证)
  - [登录](#登录)
  - [注册](#注册)
  - [重置密码](#重置密码)
  - [验证邮箱](#验证邮箱)
- [用户管理](#用户管理)
  - [获取当前用户](#获取当前用户)
  - [更新用户信息](#更新用户信息)
- [帖子管理](#帖子管理)
  - [创建帖子](#创建帖子)
  - [读取帖子列表](#读取帖子列表)
  - [读取单个帖子](#读取单个帖子)
  - [更新帖子](#更新帖子)
  - [删除帖子](#删除帖子)
- [关注列表管理](#关注列表管理)
  - [获取关注分组](#获取关注分组)
  - [创建关注分组](#创建关注分组)
  - [更新关注分组](#更新关注分组)
- [技术面 Prompt](#技术面-prompt)
  - [生成技术面 Prompt](#生成技术面-prompt)
- [回测配置](#回测配置)
  - [获取策略配置](#获取策略配置)
  - [保存策略配置](#保存策略配置)

---

## 认证

所有认证端点使用 FastAPI-Users 提供的认证功能。

### 基础信息

- **Base URL**: `/api/v1/auth`
- **认证方式**: JWT Bearer Token
- **错误响应**: 统一使用 ResponseEnvelope 包装

### 端点列表

| 端点 | 方法 | 路径 | 描述 | 认证 |
|--------|------|------|------|--------|
| 登录 | POST | `/api/v1/auth/jwt/login` | 使用邮箱和密码登录 | 否 |
| 注册 | POST | `/api/v1/auth/register` | 创建新用户 | 否 |
| 重置密码 | POST | `/api/v1/auth/forgot-password` | 发送重置密码邮件 | 否 |
| 验证邮箱 | POST | `/api/v1/auth/verify` | 验证邮箱 token | 否 |

### 登录

**端点**: `POST /api/v1/auth/jwt/login`

**请求体**:
```json
{
  "email": "user@example.com",
  "password": "your_password"
}
```

**响应**: `200 OK`
```json
{
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "is_active": true,
      "is_superuser": false
    }
  },
  "message": "登录成功",
  "error": null
}
```

**错误响应**:
```json
{
  "data": null,
  "message": "邮箱或密码错误",
  "error": {
    "code": "INVALID_CREDENTIALS",
    "detail": "..."
  }
}
```

### 注册

**端点**: `POST /api/v1/auth/register`

**请求体**:
```json
{
  "email": "user@example.com",
  "password": "your_password",
  "is_superuser": false
}
```

**响应**: `201 Created`
```json
{
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "is_active": true,
    "is_superuser": false
  },
  "message": "注册成功",
  "error": null
}
```

**错误响应**:
- `400`: 邮箱已存在
- `422`: 请求参数无效

---

## 用户管理

### 基础信息

- **Base URL**: `/api/v1/user`
- **认证方式**: JWT Bearer Token

### 端点列表

| 端点 | 方法 | 路径 | 描述 | 认证 |
|--------|------|------|------|--------|
| 获取当前用户 | GET | `/api/v1/user/me` | 获取当前登录用户信息 | 是 |
| 更新用户信息 | PUT | `/api/v1/user/me` | 更新用户昵称等信息 | 是 |

### 获取当前用户

**端点**: `GET /api/v1/user/me`

**请求头**:
```http
Authorization: Bearer YOUR_JWT_TOKEN
```

**响应**: `200 OK`
```json
{
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "is_active": true,
    "is_superuser": false,
    "nickname": "用户昵称"
  },
  "message": "查询成功",
  "error": null
}
```

### 更新用户信息

**端点**: `PUT /api/v1/user/me`

**请求头**:
```http
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json
```

**请求体**:
```json
{
  "nickname": "新昵称"
}
```

**响应**: `200 OK`
```json
{
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "is_active": true,
    "is_superuser": false,
    "nickname": "新昵称"
  },
  "message": "更新成功",
  "error": null
}
```

---

## 帖子管理

### 基础信息

- **Base URL**: `/api/v1/post`
- **认证方式**: JWT Bearer Token（所有端点）
- **错误响应**: 统一使用 ResponseEnvelope 包装

### 端点列表

| 端点 | 方法 | 路径 | 描述 | 认证 |
|--------|------|------|------|--------|
| 创建帖子 | POST | `/api/v1/post` | 创建新帖子 | 是 |
| 读取帖子列表 | GET | `/api/v1/post` | 获取帖子列表（分页） | 否 |
| 读取单个帖子 | GET | `/api/v1/post/{post_id}` | 根据 ID 获取帖子 | 否 |
| 更新帖子 | PUT | `/api/v1/post/{post_id}` | 更新帖子内容 | 是 |
| 删除帖子 | DELETE | `/api/v1/post/{post_id}` | 删除帖子 | 是 |

### 创建帖子

**端点**: `POST /api/v1/post`

**请求头**:
```http
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json
```

**请求体**:
```json
{
  "title": "帖子标题",
  "content": "帖子内容",
  "is_published": true
}
```

**响应**: `201 Created`
```json
{
  "data": {
    "id": "uuid",
    "title": "帖子标题",
    "content": "帖子内容",
    "is_published": true,
    "author_id": "user-uuid",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": null
  },
  "message": "创建成功",
  "error": null
}
```

### 读取帖子列表

**端点**: `GET /api/v1/post`

**查询参数**:
- `limit`: 每页数量（默认 100，最大 100）
- `offset`: 偏移量（默认 0）
- `order_by`: 排序方式（默认 "created_at"）

**请求示例**:
```http
GET /api/v1/post?limit=20&offset=0&order_by=created_at
Authorization: Bearer YOUR_JWT_TOKEN
```

**响应**: `200 OK`
```json
{
  "data": [
    {
      "id": "uuid",
      "title": "帖子标题",
      "content": "帖子内容",
      "is_published": true,
      "author_id": "user-uuid",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "message": "查询成功",
  "error": null
}
```

### 读取单个帖子

**端点**: `GET /api/v1/post/{post_id}`

**路径参数**:
- `post_id`: 帖子 UUID

**请求示例**:
```http
GET /api/v1/post/uuid-here
Authorization: Bearer YOUR_JWT_TOKEN
```

**响应**: `200 OK`
```json
{
  "data": {
    "id": "uuid",
    "title": "帖子标题",
    "content": "帖子内容",
    "is_published": true,
    "author_id": "user-uuid",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-02T10:00:00Z"
  },
  "message": "查询成功",
  "error": null
}
```

**错误响应**:
```json
{
  "data": null,
  "message": "帖子不存在",
  "error": {
    "code": "POST_NOT_FOUND",
    "detail": "..."
  }
}
```

### 更新帖子

**端点**: `PUT /api/v1/post/{post_id}`

**路径参数**:
- `post_id`: 帖子 UUID

**请求头**:
```http
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json
```

**请求体**:
```json
{
  "title": "更新后的标题",
  "content": "更新后的内容",
  "is_published": true
}
```

**响应**: `200 OK`
```json
{
  "data": {
    "id": "uuid",
    "title": "更新后的标题",
    "content": "更新后的内容",
    "is_published": true,
    "author_id": "user-uuid",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-02T15:00:00Z"
  },
  "message": "更新成功",
  "error": null
}
```

**错误响应**:
- `404`: 帖子不存在
- `403`: 权限不足（非作者）

### 删除帖子

**端点**: `DELETE /api/v1/post/{post_id}`

**路径参数**:
- `post_id`: 帖子 UUID

**请求头**:
```http
Authorization: Bearer YOUR_JWT_TOKEN
```

**请求示例**:
```http
DELETE /api/v1/post/uuid-here
Authorization: Bearer YOUR_JWT_TOKEN
```

**响应**: `200 OK`
```json
{
  "data": {
    "deleted": true
  },
  "message": "删除成功",
  "error": null
}
```

**错误响应**:
- `404`: 帖子不存在
- `403`: 权限不足（非作者）

---

## 关注列表管理

### 基础信息

- **Base URL**: `/api/v1/watchlist`
- **认证方式**: JWT Bearer Token
- **数据源**: Longport API

### 端点列表

| 端点 | 方法 | 路径 | 描述 | 认证 |
|--------|------|------|------|--------|
| 获取关注分组 | GET | `/api/v1/watchlist/{group_id}` | 根据 ID 获取分组 | 是 |
| 创建关注分组 | POST | `/api/v1/watchlist` | 创建新的自选分组 | 是 |
| 更新关注分组 | PUT | `/api/v1/watchlist/{group_id}` | 更新分组名称或证券列表 | 是 |

### 获取关注分组

**端点**: `GET /api/v1/watchlist/{group_id}`

**路径参数**:
- `group_id`: 分组 ID

**请求头**:
```http
Authorization: Bearer YOUR_JWT_TOKEN
```

**响应**: `200 OK`
```json
{
  "data": {
    "id": 1,
    "name": "我的自选",
    "securities": [
      {
        "symbol": "700.HK",
        "market": "HK",
        "name": "腾讯控股",
        "watched_price": 350.5,
        "watched_at": "2024-01-01T10:00:00Z"
      }
    ]
  },
  "message": "查询成功",
  "error": null
}
```

**错误响应**:
```json
{
  "data": null,
  "message": "分组不存在",
  "error": {
    "code": "WATCHLIST_GROUP_NOT_FOUND",
    "detail": "..."
  },
  "status_code": 404
}
```

### 创建关注分组

**端点**: `POST /api/v1/watchlist`

**请求头**:
```http
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json
```

**请求体**:
```json
{
  "name": "我的自选",
  "securities": [
    {
      "symbol": "700.HK",
      "market": "HK"
    }
  ]
}
```

**响应**: `200 OK`
```json
{
  "data": {
    "id": 1
    "name": "我的自选"
    "securities": [
      {
        "symbol": "700.HK",
        "market": "HK"
      }
    ]
  },
  "message": "创建成功",
  "error": null
}
```

### 更新关注分组

**端点**: `PUT /api/v1/watchlist/{group_id}`

**路径参数**:
- `group_id`: 分组 ID

**请求头**:
```http
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json
```

**请求体**:
```json
{
  "name": "更新后的名称",
  "securities": [
    {
      "symbol": "700.HK",
      "market": "HK"
    }
  ],
  "mode": "add"
}
```

**更新模式** (`mode` 参数):
- `"add"`: 添加证券到分组
- `"remove"`: 从分组移除证券
- `"replace"`: 替换分组中的证券列表

**响应**: `200 OK`
```json
{
  "data": {
    "id": 1,
    "name": "更新后的名称",
    "securities": [
      {
        "symbol": "700.HK",
        "market": "HK"
      }
    ]
  },
  "message": "更新成功",
  "error": null
}
```

---

## 技术面 Prompt

### 基础信息

- **Base URL**: `/api/v1/prompt`
- **认证方式**: JWT Bearer Token
- **缓存**: 60 秒 TTI 缓存

### 端点列表

| 端点 | 方法 | 路径 | 描述 | 认证 |
|--------|------|------|------|--------|
| 生成技术面 Prompt | GET | `/api/v1/prompt/technical` | 为指定股票生成技术面分析 prompt | 是 |

### 生成技术面 Prompt

**端点**: `GET /api/v1/prompt/technical`

**查询参数**:
- `symbols`: 逗号分隔的股票代码列表（必需）
- `template`: 技术面模板类型（可选，默认 "single_period_only_latest_txt"）

**请求示例**:
```http
GET /api/v1/prompt/technical?symbols=159300.SZ,159500.SZ&template=single_period_only_latest_txt
Authorization: Bearer YOUR_JWT_TOKEN
```

**模板类型**:
- `"single_period_only_latest_txt"`: 仅单周期，最新数据
- `"multi_period_only_latest_txt"`: 多周期，最新数据
- `"multi_period_with_history_txt"`: 多周期，包含历史数据

**响应**: `200 OK`
```json
{
  "data": {
    "prompt": "【技术面分析】\n\n标的：159300.SZ, 159500.SZ\n\n...",
    "template": "single_period_only_latest_txt",
    "symbols": [
      "159300.SZ",
      "159500.SZ"
    ],
    "cached": true
  },
  "message": "生成成功",
  "error": null
}
```

**错误响应**:
- `400`: symbols 参数为空

---

## 回测配置

### 基础信息

- **Base URL**: `/api/v1/backtest`
- **认证方式**: JWT Bearer Token
- **支持模式**: Vectorized（向量化）, Virtual（虚拟交易）

### 端点列表

| 端点 | 方法 | 路径 | 描述 | 认证 |
|--------|------|------|------|--------|
| 获取策略配置 | GET | `/api/v1/backtest/config/strategies` | 获取默认向量化策略配置 | 是 |
| 保存策略配置 | POST | `/api/v1/backtest/config/strategies` | 保存自定义策略配置 | 是 |

### 获取策略配置

**端点**: `GET /api/v1/backtest/config/strategies`

**请求头**:
```http
Authorization: Bearer YOUR_JWT_TOKEN
```

**响应**: `200 OK`
```json
{
  "data": {
    "ema_short": 5,
    "ema_long": 20,
    "stop_loss_pct": null,
    "take_profit_pct": null
  },
  "message": "查询成功",
  "error": null
}
```

### 保存策略配置

**端点**: `POST /api/v1/backtest/config/strategies`

**请求头**:
```http
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json
```

**请求体**:
```json
{
  "ema_short": 10,
  "ema_long": 30,
  "stop_loss_pct": 0.02,
  "take_profit_pct": 0.05
}
```

**策略参数说明**:
- `ema_short`: 短期 EMA 周期（默认 5）
- `ema_long`: 长期 EMA 周期（默认 20）
- `stop_loss_pct`: 止损比例（0-1，默认 null）
- `take_profit_pct`: 止盈比例（0-1，默认 null）

**响应**: `200 OK`
```json
{
  "data": {
    "message": "策略配置已保存（功能开发中）"
  },
  "message": "策略配置已保存（功能开发中）",
  "error": null
}
```

---

## 通用错误响应格式

### ResponseEnvelope 结构

所有 API 响应都使用统一包装格式：

```json
{
  "data": {...},        // 成功时返回的数据
  "message": "操作结果描述",
  "error": {           // 错误时返回的详细信息
    "code": "ERROR_CODE",
    "detail": "错误详情"
  }
}
```

### 常见错误码

| 错误码 | HTTP 状态 | 描述 |
|---------|-----------|------|
| `INVALID_CREDENTIALS` | 401 | 邮箱或密码错误 |
| `POST_NOT_FOUND` | 404 | 帖子不存在 |
| `WATCHLIST_GROUP_NOT_FOUND` | 404 | 关注分组不存在 |
| `NOT_OWNER` | 403 | 权限不足（非作者）|
| `NOT_ENOUGH_PERMISSIONS` | 403 | 权限不足 |

---

## 使用示例

### Python (requests)

```python
import requests

# 1. 登录
response = requests.post(
    "http://localhost:8000/api/v1/auth/jwt/login",
    json={
        "email": "user@example.com",
        "password": "password"
    }
)
token = response.json()["data"]["access_token"]

# 2. 使用 token 获取帖子
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    "http://localhost:8000/api/v1/post",
    headers=headers
)
posts = response.json()["data"]
```

### Python (httpx)

```python
import httpx

async with httpx.AsyncClient() as client:
    # 登录
    response = await client.post(
        "http://localhost:8000/api/v1/auth/jwt/login",
        json={
            "email": "user@example.com",
            "password": "password"
        }
    )
    token = response.json()["data"]["access_token"]
    
    # 创建帖子
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.post(
        "http://localhost:8000/api/v1/post",
        headers=headers,
        json={
            "title": "新帖子",
            "content": "帖子内容",
            "is_published": True
        }
    )
    post = response.json()["data"]
```

### cURL

```bash
# 登录
curl -X POST http://localhost:8000/api/v1/auth/jwt/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# 获取帖子（需要先登录获取 token）
curl http://localhost:8000/api/v1/post \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 创建帖子
curl -X POST http://localhost:8000/api/v1/post \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "新帖子",
    "content": "帖子内容",
    "is_published": true
  }'
```

---

## 开发说明

### 本地开发服务器

```bash
# 启动开发服务器
uv run serve.py

# 服务器将在 http://localhost:8000 启动
```

### API 文档

FastAPI 提供了自动生成的交互式 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 请求头规范

所有需要认证的端点都需要在请求头中包含：

```http
Authorization: Bearer YOUR_JWT_TOKEN
```

### 分页规范

支持分页的列表端点使用以下参数：

- `limit`: 每页返回数量（默认 100）
- `offset`: 偏移量（默认 0）

**计算方式**：
- 下一页: `offset += limit`
- 总页数: `ceil(total / limit)`

---

## 注意事项

### 认证

1. 登录后获取的 `access_token` 和 `refresh_token` 有效期默认为 30 天
2. 需要在请求头中携带 `Authorization: Bearer <token>`
3. 超级用户具有所有权限，普通用户只能操作自己的资源

### 数据验证

1. 所有 POST/PUT 请求体应使用 `Content-Type: application/json`
2. 必填字段未提供时返回 `400 Bad Request`
3. 数据格式错误时返回 `422 Unprocessable Entity`

### 错误处理

1. 使用统一的 `ResponseEnvelope` 包装响应
2. 错误信息使用中文描述
3. 返回适当的 HTTP 状态码

### 性能优化

1. 技术面 Prompt 端点支持 60 秒缓存
2. 使用缓存时会在响应中标注 `"cached": true`

---

## 更新日志

- **2024-01-20**: 初始版本，完整 API 文档
