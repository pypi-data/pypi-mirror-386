# SkyPlatform IAM SDK

SkyPlatform IAM认证SDK，提供FastAPI中间件和认证路由，简化第三方服务的认证集成。

## 功能特性

- 🔐 **FastAPI中间件**: 自动拦截请求进行Token验证和权限检查
- 🚀 **统一初始化**: 使用 `init_skyplatform_iam` 一键设置认证功能
- 🔧 **全局客户端**: 通过 `get_iam_client()` 在任何地方访问IAM功能
- 🛡️ **懒加载支持**: 使用 `create_lazy_iam_client()` 解决初始化顺序问题
- ⚙️ **灵活配置**: 支持环境变量和代码配置
- 🛡️ **白名单机制**: 支持配置无需认证的路径
- 🔧 **完整兼容**: 基于现有ConnectAgenterraIam类，保持完全兼容
- 📝 **类型提示**: 完整的TypeScript风格类型提示
- 🚨 **异常处理**: 完善的错误处理和自定义异常

## 快速开始

### 安装

```bash
pip install skyplatform-iam
```

### 环境变量配置

创建 `.env` 文件或设置环境变量：

```bash
AGENTERRA_IAM_HOST=https://your-iam-host.com
AGENTERRA_SERVER_NAME=your-server-name
AGENTERRA_ACCESS_KEY=your-access-key
```

### 基本使用

#### 方式1：统一初始化（推荐）

```python
from fastapi import FastAPI
from skyplatform_iam import init_skyplatform_iam, AuthConfig

app = FastAPI()

# 一键设置认证中间件和路由
config = AuthConfig(
    agenterra_iam_host="http://127.0.0.1:5001",
    server_name="Agenterra_shop",
    access_key="zYqZwWEAW7iCi6qjVcVlnjrK5GxAkmk8"
)

init_skyplatform_iam(app, config)

@app.get("/protected")
async def protected_endpoint(request):
    # 获取用户信息（由中间件自动设置）
    user = request.state.user
    return {"message": "访问成功", "user": user}
```

#### 方式2：从环境变量初始化

```python
from fastapi import FastAPI
from skyplatform_iam import init_skyplatform_iam, AuthConfig

app = FastAPI()

# 从环境变量加载配置
config = AuthConfig.from_env()
init_skyplatform_iam(app, config)
```

#### 方式3：自定义配置

```python
from skyplatform_iam import init_skyplatform_iam, AuthConfig

# 自定义配置
config = AuthConfig(
    agenterra_iam_host="https://your-iam-host.com",
    server_name="your-server-name",
    access_key="your-access-key",
    whitelist_paths=[
        "/docs", "/redoc", "/openapi.json",
        "/health", "/public",
        "/auth/register", "/auth/login"
    ],
    enable_debug=True
)

init_skyplatform_iam(app, config)
```

### 在业务代码中使用IAM客户端

初始化SDK后，您可以在任何地方使用IAM客户端：

```python
from typing import Optional, Dict, Any
import logging
from skyplatform_iam import get_iam_client

logger = logging.getLogger(__name__)

class AuthService:
    """认证服务类，提供统一的登录验证功能"""
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """验证用户账号密码
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            验证成功返回IAM响应数据，失败返回None
        """
        try:
            result = get_iam_client().login_with_password(
                username=username,
                password=password
            )
            return result
        except Exception as e:
            logger.error(f"用户认证失败: {str(e)}")
            return None
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户信息"""
        try:
            return get_iam_client().get_user_by_id(user_id)
        except Exception as e:
            logger.error(f"获取用户信息失败: {str(e)}")
            return None

# 创建全局认证服务实例
auth_service = AuthService()
```

### 避免初始化顺序问题

如果您需要在模块级别使用IAM客户端，推荐使用懒加载方式：

```python
from skyplatform_iam import create_lazy_iam_client

# 在模块级别安全使用（推荐用于解决导入顺序问题）
iam_client = create_lazy_iam_client()

class AuthService:
    def __init__(self):
        # 使用懒加载客户端，避免初始化顺序问题
        self.iam_client = create_lazy_iam_client()
    
    def authenticate_user(self, username: str, password: str):
        # 只有在实际调用时才会初始化IAM客户端
        return self.iam_client.login_with_password(username, password)
```

#### 传统方式（已废弃，仅供参考）

```python
# ⚠️ 已废弃：请使用 init_skyplatform_iam 替代
from skyplatform_iam import setup_auth

app = FastAPI()
setup_auth(app)  # 不推荐使用
```

## 内置方法

ConnectAgenterraIam 类提供以下内置方法：

### 用户认证相关
- `register(cred_type, cred_value, password=None, nickname=None, avatar_url=None)` - 用户注册
- `login_with_password(cred_type, cred_value, password, ip_address=None, user_agent=None)` - 账号密码登录
- `login_without_password(cred_type, cred_value, ip_address=None, user_agent=None)` - 免密登录
- `logout(token)` - 用户登出

### Token管理
- `verify_token(token, api, method, server_ak="", server_sk="")` - Token验证和权限检查
- `refresh_token(refresh_token)` - 刷新Token

### 密码管理
- `reset_password(cred_type, cred_value, new_password)` - 重置密码

### 角色管理
- `assign_role_to_user(user_id, role_name)` - 为用户分配角色

### 用户信息
- `get_userinfo_by_token(token)` - 通过Token获取用户信息
- `get_user_by_credential(cred_type, cred_value)` - 通过凭证获取用户信息

### 用户配置
- `add_custom_config(user_id, config_key, config_value)` - 添加用户自定义配置
- `get_custom_configs(user_id, config_key=None)` - 获取用户自定义配置
- `delete_custom_config(user_id, config_key)` - 删除用户自定义配置

### 凭证管理
- `merge_credential(primary_cred_type, primary_cred_value, secondary_cred_type, secondary_cred_value)` - 凭证合并

### 使用示例

```python
from skyplatform_iam import get_iam_client

# 获取IAM客户端
iam_client = get_iam_client()

# 用户注册
result = iam_client.register(
    cred_type="username",
    cred_value="testuser",
    password="password123",
    nickname="测试用户"
)

# 用户登录
response = iam_client.login_with_password(
    cred_type="username",
    cred_value="testuser",
    password="password123"
)

# Token验证
user_info = iam_client.verify_token(
    token="user_token",
    api="/api/protected",
    method="GET"
)
```

## 中间件功能

### 自动Token验证

中间件会自动：
1. 检查请求路径是否在白名单中
2. 从请求头提取Authorization Token
3. 调用IAM服务验证Token和权限
4. 将用户信息设置到 `request.state.user`

### 白名单配置

默认白名单路径：
- `/docs`, `/redoc`, `/openapi.json` - API文档
- `/health` - 健康检查
- `/auth/*` - 认证相关接口

添加自定义白名单：

```python
config = AuthConfig.from_env()
config.add_whitelist_path("/public")
config.add_whitelist_path("/status")
```

### 获取用户信息

在受保护的路由中获取用户信息：

```python
@app.get("/user-profile")
async def get_user_profile(request):
    if hasattr(request.state, 'user'):
        user = request.state.user
        return {
            "user_id": user["user_id"],
            "username": user["username"],
            "session_id": user["session_id"]
        }
    else:
        raise HTTPException(status_code=401, detail="未认证")
```

## 异常处理

SDK提供完整的异常处理：

```python
from skyplatform_iam.exceptions import (
    AuthenticationError,    # 认证失败
    AuthorizationError,     # 权限不足
    TokenExpiredError,      # Token过期
    TokenInvalidError,      # Token无效
    ConfigurationError,     # 配置错误
    IAMServiceError,        # IAM服务错误
    NetworkError           # 网络错误
)
```

## 配置选项

### AuthConfig参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `agenterra_iam_host` | str | ✓ | IAM服务地址 |
| `server_name` | str | ✓ | 服务名称 |
| `access_key` | str | ✓ | 访问密钥 |
| `whitelist_paths` | List[str] | ✗ | 白名单路径 |
| `token_header` | str | ✗ | Token请求头名称（默认：Authorization） |
| `token_prefix` | str | ✗ | Token前缀（默认：Bearer ） |
| `enable_debug` | bool | ✗ | 启用调试模式 |

## 开发和测试

### 运行测试

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
python examples/test_sdk.py
```

### 运行示例

```bash
# 启动示例应用
python examples/basic_usage.py

# 访问 http://localhost:8000/docs 查看API文档
```

## 兼容性

- Python 3.8+
- FastAPI 0.68.0+
- 完全兼容现有的 `ConnectAgenterraIam` 类

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 迁移指南

### 从旧版本迁移到新版本

如果您正在使用旧版本的 `setup_auth` 函数，请按照以下步骤迁移：

#### 旧版本代码：
```python
from skyplatform_iam import setup_auth
setup_auth(app)
```

#### 新版本代码：
```python
from skyplatform_iam import init_skyplatform_iam, AuthConfig

config = AuthConfig.from_env()  # 或者手动创建配置
init_skyplatform_iam(app, config)
```

### 常见问题解决

#### 1. 初始化顺序问题

**错误示例：**
```python
# ❌ 错误：在模块导入时直接调用
from skyplatform_iam import get_iam_client
iam_client = get_iam_client()  # 可能导致初始化错误
```

**正确示例：**
```python
# ✅ 正确：在函数内部调用
from skyplatform_iam import get_iam_client

def some_function():
    iam_client = get_iam_client()  # 在函数内部调用
    return iam_client.login_with_password(...)

# 或者使用懒加载
from skyplatform_iam import create_lazy_iam_client
iam_client = create_lazy_iam_client()  # 安全的模块级别使用
```

#### 2. 配置管理

推荐使用环境变量管理配置：

```bash
# .env 文件
AGENTERRA_IAM_HOST=http://127.0.0.1:5001
AGENTERRA_SERVER_NAME=your_service_name
AGENTERRA_ACCESS_KEY=your_access_key
```

```python
# Python 代码
from skyplatform_iam import init_skyplatform_iam, AuthConfig

config = AuthConfig.from_env()
init_skyplatform_iam(app, config)
```

## 更新日志

### v2.0.0
- 🚀 新增 `init_skyplatform_iam` 统一初始化函数
- 🔧 新增 `get_iam_client` 全局客户端获取函数
- 🛡️ 新增 `create_lazy_iam_client` 懒加载客户端
- 📚 改进文档和使用示例
- ⚠️ 废弃 `setup_auth` 函数（保持向后兼容）
- 🐛 修复模块导入顺序问题

### v1.0.0
- 初始版本发布
- 提供FastAPI中间件和认证路由
- 支持完整的认证功能
- 兼容现有ConnectAgenterraIam类