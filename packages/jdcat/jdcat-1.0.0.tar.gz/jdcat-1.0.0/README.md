# JDCat (pip package)

JDCat 提供一个命令行入口，包装并启动本地助手 FastAPI 服务（来自 sensitive-check-local 项目），不更改任何业务逻辑。

## 安装与使用

- 构建（在仓库根目录）：
  ```bash
  uv pip install -U build
  cd jdcat
  python -m build
  ```

- 本地安装（开发验证）：
  ```bash
  uv pip install .
  ```
  或使用 pip：
  ```bash
  python -m pip install .
  ```

- 启动服务（二选一）：
  ```bash
  # 方式1：命令入口
  jdcat start --port 17866 --host 127.0.0.1

  # 方式2：模块执行
  python -m jdcat start --port 17866 --host 127.0.0.1
  ```

## 说明

- 本包仅提供 CLI 入口与打包配置，业务逻辑均由 sensitive-check-local 提供。
- 入口会通过 uvicorn 启动 `sensitive_check_local.api:app`，默认监听 `127.0.0.1:17866`。
- 资源文件的打包策略在 `pyproject.toml` 中进行配置（package-data），确保 wheel 安装后可用。

## 运行要求

- Python: 3.10 - 3.11
- 依赖：fastapi、uvicorn、httpx、mitmproxy、PyYAML、rumps 等（详见 pyproject）

## 开源信息

- 作者：Sensitive Check Team
## 停止服务

- 命令行停止（推荐）：
  ```bash
  jdcat stop --port 17866 --host 127.0.0.1
  ```

- 模块方式停止（等效）：
  ```bash
  python -m jdcat stop --port 17866 --host 127.0.0.1
  ```

说明：
- 停止命令会向 `http://127.0.0.1:17866/stop` 发起 `POST` 请求，调用本地服务的停止接口 [`sensitive_check_local.api.stop()`](jdcat/sensitive_check_local/api.py:442) 实现优雅退出并恢复系统代理。

## 常见问题与排查

- pip 命令不可用：
  - 现象：`zsh: command not found: pip`
  - 解决：使用 `python -m pip`（已在文档中统一建议）
    ```bash
    python -m pip install .
    ```

- mitmdump 不存在：
  - 现象：启动时报错 `mitmdump not found`
  - 解决：安装 mitmproxy（例如 macOS 使用 Homebrew）
    ```bash
    brew install mitmproxy
    ```
  - 安装后请确保 `mitmdump` 在 `PATH` 中；本地服务通过 [`sensitive_check_local.process.start_capture()`](jdcat/sensitive_check_local/process.py:167) 调用 mitmdump，并加载打包内置插件 [`jdcat/mitmproxy/local_bridge_addon.py`](jdcat/mitmproxy/local_bridge_addon.py)。

- 端口占用：
  - 现象：启动报错 `port 17866 is already in use`
  - 解决：指定其它端口，例如：
    ```bash
    jdcat start --port 18000
    ```

- 版本号说明：
  - 分发包版本：[`jdcat.__init__.__version__`](jdcat/__init__.py:8) 为 1.0.0
  - 本地服务模块版本：[`sensitive_check_local.__version__`](jdcat/sensitive_check_local/__init__.py:6) 与包版本保持一致（1.0.0）