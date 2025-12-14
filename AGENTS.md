# AGENTS.md

本文档用于说明在本仓库中协作开发的基本约定与实践。

## 模块概览

| 路径                | 角色说明             | 关键备注                                                                           |
| ------------------- | -------------------- | ---------------------------------------------------------------------------------- |
| `app/main.py`       | FastAPI + AgentOS 入口 | 初始化日志/DB/默认用户与交易账户,加载 AgentOS,挂载路由与中间件。                    |
| `app/core/`         | 配置与基础设施        | 配置(`config.py`)、数据库(`db.py`)、依赖(`deps.py`)、初始化数据(`init_data.py`)。    |
| `app/api/`          | HTTP 对外接口        | `__init__.py` 汇总路由; `routes/` 按功能划分(auth/user/post)。                      |
| `app/agent/`        | Agent 定义与工厂     | 提供可用模型表、示例 Agent、交易 Agent 初始化函数。                                |
| `app/data_source/`  | 市场数据源适配       | 统一对接外部行情源(如 Longport)。                                                   |
| `app/data_feed/`    | 行情加工与指标       | 组合数据源、计算技术指标/情绪/新闻等扩展数据。                                      |
| `app/prompt_build/` | Prompt 片段生成      | 组装账户与技术面快照,提供给 Agent 的上下文片段。                                   |
| `app/models/`       | 数据库与 API 模型    | SQLModel 实体与对应 Pydantic 校验/输出模型,含虚拟交易相关实体。                     |
| `app/virtual_trade/`| 虚拟交易业务         | 账户/订单/持仓业务逻辑,与模型对应。                                                |
| `app/workflow/`     | 工作流与调度         | 工作流入口(如 `nof1_workflow.py`) 串联数据、Agent、交易。                            |
| `app/utils/`        | 跨层工具             | 响应封装、异常、日志、指标计算等通用方法。                                          |
| `tests/`            | 测试                 | `conftest.py` 统一依赖; `tests/utils/` 存放测试工具与鉴权辅助。                      |
| `serve.py`          | 本地运行入口         | 通过 `uv` 启动应用的便捷脚本。                                                      |
| `logs/`             | 运行日志             | 应用写入的日志文件。                                                                |

## 开发常用命令

- `uv run serve.py` —— 启动服务
- `uv run ruff check --fix` —— 使用 Ruff 进行格式化与静态检查
- `uv run pytest` —— 运行测试

## 数据库与 Pydantic 校验模型

- 模型拆分成三层:公共字段(`*Base`),数据库实体(`table=True`),以及 Pydantic 校验模型(`Create/Update/Read`)。保持字段来源清晰,避免重复定义。
- `app/models/base_model.py` 提供统一的主键和审计列,新的数据库模型必须继承它,并复用其中的列约定。
- 单文件仅维护一个实体,文件名使用实体名(如 `post.py`),数据库表名(`__tablename__`)一律使用该实体的单数形式。
- Pydantic 模型基于 SQLModel/Pydantic v2 写法,`Create/Update` 仅暴露可写字段,`Read` 通过继承 `BaseModel` 追加只读字段和 ID,不需要配置 `model_config = ConfigDict(from_attributes=True)`。
- 参考 `app/models/post.py` 的层次结构、注释与 `Field` 配置,新增模型时保持同样的注释、类型提示和 `sa_column_kwargs` 说明,以便数据库与文档同步。

## API请求流程说明

- 所有请求从 `app/api/routes/*` 进入,并在 `app/api/__init__.py` 中完成路由注册。
- 共享依赖(数据库会话、鉴权上下文等)集中在 `app/core/deps.py`,通过依赖注入传入路由处理函数。
- 路由处理函数调用 `app/models/*` 进行 ORM 交互,并在需要时复用 `app/utils/` 中的工具。
- 响应沿路由返回,由 `app/main.py` 中的中间件与异常处理器完成最终输出。
- 标准响应通过 `app/utils/responses.py` 中的 `ResponseEnvelope/success_response/error_response` 构建,所有 API 都应返回统一 envelope。
- 业务异常需继承 `app/utils/exceptions.py` 的基类(如 `AppException/NotFoundException/ForbiddenException`),并在 `register_exception_handlers` 中自动转换为标准响应。
- 日志相关逻辑封装在 `app/utils/logging.py`,`setup_logging` 统一初始化 Loguru,`RequestLoggingMiddleware` 负责记录请求耗时;如需自定义日志,请复用现有 logger 配置。

## 测试规范与执行

- 测试结构遵循 `tests/<模块>/...`,其中 `tests/api/routes/` 用于 API 行为测试、`tests/utils/` 保存测试依赖(如 `user_deps.py`、`auth.py` 等)。
- `tests/conftest.py` 创建临时 SQLite 数据库,并通过 `UserFactory` 生成受控的激活用户;所有需要登录的用例应复用 `test_user` fixture,不得手动插入散乱数据。
- 需要授权的测试通过 `tests/utils/auth.py` 的 `get_auth_headers` 函数,从真实登录接口获取 JWT,确保鉴权链路与生产一致。
- 如需自定义测试数据,请优先扩展工厂或局部 fixture,避免在测试中直接依赖生产环境状态。

## API更新建议

- 新增路由应放在 `app/api/routes/` 下的独立模块,导出 router,并在 `app/api/__init__.py` 中挂载。
- 在 `app/models/` 中扩展新的 SQLModel/SQLAlchemy 实体,并尽量与对应的 Pydantic 模型同文件维护,避免遗漏导入。
- 环境配置变更需同步更新 `.env`、`.env.example` 与 `app/core/config.py`,保持环境一致。
- 新命令或工作流应补充在本文档对应段落,确保该指南始终准确。

## 代码生产规范

- 需遵循现有的路由组织模式。
- 禁止使用已弃用的`typing`。
- 生成或修改代码前,优先通过 MCP `context7` 获取官方最佳实践。
- 完成修改后务必运行 `uv run ruff check --fix` 并清理警告。

## **Important Notes**

- 所有的响应与回复用中文
- 不要过度设计,保证代码简洁易懂,简单实用
- 写代码时,要注意圈复杂度,代码尽可能复用
- 写代码时,注意模块设计,尽量使用设计模式
- 改动时最小化修改,尽量不修改到其他模块代码
