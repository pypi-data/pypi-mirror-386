# JDCat (pip package)

JDCat 提供一个命令行入口，包装并启动本地助手 FastAPI 服务（来自 sensitive-check-local 项目），不更改任何业务逻辑。

## 安装与使用

### 快速安装（推荐）

如果遇到 `externally-managed-environment` 错误，这是现代Python环境管理的安全特性（PEP 668），请使用以下任一方法安装：

#### 方法1：使用 pipx（推荐）
```bash
# 安装 pipx（如果未安装）
python -m pip install --user pipx
python -m pipx ensurepath

# 使用 pipx 安装 jdcat
pipx install jdcat

# 验证安装
jdcat --help
```

#### 方法2：使用虚拟环境
```bash
# 创建虚拟环境
python -m venv jdcat-env

# 激活虚拟环境
# macOS/Linux:
source jdcat-env/bin/activate
# Windows:
# jdcat-env\Scripts\activate

# 安装 jdcat
python -m pip install jdcat

# 验证安装
jdcat --help
```

#### 方法3：使用 uv（现代包管理器）
```bash
# 安装 uv（如果未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 使用 uv 运行 jdcat
uv run --from jdcat jdcat start --port 17866 --host 127.0.0.1

# 或创建 uv 项目环境
uv init jdcat-project
cd jdcat-project
uv add jdcat
uv run jdcat --help
```

#### 方法4：系统级安装（不推荐）
⚠️ **仅在确实需要时使用，可能影响系统Python环境**
```bash
# 使用 --break-system-packages 标志
python -m pip install --break-system-packages jdcat

# 或使用 --user 安装到用户目录
python -m pip install --user jdcat
```

### 开发者安装（从源码）

- 构建（在仓库根目录）：
  ```bash
  uv pip install -U build
  cd jdcat
  python -m build
  ```

- 本地安装（开发验证）：
  ```bash
  # 使用 uv（推荐）
  uv pip install .
  
  # 或在虚拟环境中
  python -m venv dev-env
  source dev-env/bin/activate  # macOS/Linux
  python -m pip install .
  ```

### 启动服务

安装完成后，可以通过以下方式启动：

```bash
# 方式1：命令入口
jdcat start --port 17866 --host 127.0.0.1

# 方式2：模块执行
python -m jdcat start --port 17866 --host 127.0.0.1

# 方式3：使用 uv（如果通过 uv 安装）
uv run --from jdcat jdcat start --port 17866 --host 127.0.0.1
```

### 验证安装

```bash
# 检查版本
jdcat --version

# 查看帮助
jdcat --help

# 测试启动（会在后台启动服务）
jdcat start --port 17866
```

## 说明

- 本包仅提供 CLI 入口与打包配置，业务逻辑均由 sensitive-check-local 提供。
- 入口会通过 uvicorn 启动 `sensitive_check_local.api:app`，默认监听 `127.0.0.1:17866`。
- 资源文件的打包策略在 `pyproject.toml` 中进行配置（package-data），确保 wheel 安装后可用。

## 运行要求

- Python: 3.10 - 3.14
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

- **externally-managed-environment 错误**：
  - 现象：`error: externally-managed-environment × This environment is externally managed`
  - 原因：现代Python发行版（如macOS Homebrew Python、Ubuntu 23.04+等）实施PEP 668标准，防止直接在系统Python环境中安装包，避免与系统包管理器冲突
  - 解决：请参考上方"快速安装"部分，推荐使用pipx或虚拟环境安装
    ```bash
    # 推荐方案：使用 pipx
    pipx install jdcat
    
    # 或使用虚拟环境
    python -m venv jdcat-env
    source jdcat-env/bin/activate
    python -m pip install jdcat
    ```

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