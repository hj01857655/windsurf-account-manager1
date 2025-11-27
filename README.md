# Windsurf Account Manager

Windsurf Account Manager 是一个使用 **Python + Tkinter** 开发的桌面工具，用于在本地集中管理多个 Windsurf 账号，以及与账号相关的 MCP / Rules / 配置快照等信息，为后续实现“切号自动登录”提供基础设施。

> 本项目只提供本地账号与配置管理、登录流程分析文档以及配置快照切换方案，不内置可直接运行的自动登录脚本。

---

## 1. 功能概览

- **账号管理**
  - 从 `windsurf.json` 导入账号（email/password 列表）。
  - 本地保存账号到 `data/accounts.json`。
  - 列表展示账号（邮箱、备注、计划信息占位等）。
  - 批量删除、本地导出账号列表。
  - 快捷操作：全选 / 全不选。
  - 编辑账号备注（双击或“编辑详情”按钮）。
  - “切换到选中账号”Hook：
    - 在 UI 中高亮当前账号；
    - 作为后续“自动登录 / 配置切换”的入口。

- **MCP / Rules 配置管理**
  - MCP Servers：
    - 打开/保存 MCP 配置 JSON。
    - 新建 / 编辑 / 删除 MCP server（ID、名称、命令、参数、环境变量、启用状态）。
    - 备份 MCP 配置到任意路径。
  - Rules：
    - 打开/保存 Rules 配置 JSON（`[{ id, prompt }]` 结构）。
    - 新建 / 编辑 / 删除 Rule。
    - 备份 Rules 配置到任意路径。

- **登录流程逆向分析文档**
  - 位于 `docs/LOGIN_AND_CONFIG_ANALYSIS.md`。
  - 内容包括：
    - 从 `email/password` 到 `firebase_id_token` / `auth_token` / `api_key` / Bearer token 的推测性链路；
    - 相关 gRPC proto 与 axios 示例的字段说明；
    - 建议的外部登录脚本结构（命令行工具形式）；
    - Linux 下 Windsurf 配置路径的推断方法；
    - “切号 = 配置快照切换”方案设计。

- **项目进度与规划文档**
  - 位于 `PROJECT_STATUS.md`。
  - 记录：已完成功能、进行中的工作、后续计划（ROADMAP）。

---

## 2. 环境与安装

### 2.1 前置要求

- Python 版本：建议 **Python 3.10+**（当前开发环境为 3.12）。
- 系统：Linux（当前优先适配环境）。
- Tkinter：需要通过系统包安装，而不是通过 pip。

在 Debian/Ubuntu 上可以执行：

```bash
sudo apt-get update
sudo apt-get install python3-tk
```

确认 Tkinter 正常：

```bash
python3 -c "import tkinter; print('tk ok')"
```

### 2.2 创建虚拟环境并安装依赖

在项目根目录 `windsurf-account-manager/` 下：

```bash
cd /home/zhengxueen/workspace/windsurf-tool/windsurf-account-manager

# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境（bash/zsh）
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

当前 `requirements.txt` 只包含：

```text
requests>=2.31.0
```

后续如需增加依赖，可以在此文件中补充。

---

## 3. 启动应用

激活虚拟环境后，在项目根目录执行：

```bash
cd /home/zhengxueen/workspace/windsurf-tool/windsurf-account-manager
source .venv/bin/activate
python main.py
```

启动后会打开一个 Tkinter 主窗口，包含两个 Tab：

- 「账号管理」
- 「MCP / Rules」

---

## 4. 使用说明

### 4.1 账号管理 Tab

- **导入账号**
  - 点击「从 windsuf.json 导入」，选择你的 `windsurf.json`：
    - 预期结构为 `[{ "email": "...", "password": "..." }, ...]`。
    - 按 `email` 去重导入，自动为新账号生成唯一 `id`。
  - 导入后账号会保存到 `data/accounts.json`。

- **账号列表**
  - 列：
    - 邮箱
    - 备注
    - 计划名（占位字段，可后续通过 API 填充）
    - 到期时间（占位字段，可后续通过 API 填充）

- **批量操作与编辑**
  - 「全选」：选中表格中所有账号。
  - 「全不选」：清空当前选中。
  - 「批量删除」：删除选中的账号，并写回 `data/accounts.json`。
  - 「导出账号」：将当前账号列表导出为 JSON 文件。
  - 「编辑详情」：
    - 选中单个账号后点击按钮，或直接双击该行；
    - 弹出对话框，可修改备注（邮箱只读显示）。

- **切号 Hook（当前账号标记）**
  - 「切换到选中账号」：
    - 选中单个账号后点击按钮；
    - 在 UI 内将该账号标记为“当前账号”，并以淡蓝色背景高亮显示；
    - 弹出提示说明当前后续的“切号相关操作”会基于该账号进行。
  - 当前版本仅做**状态标记和 UI 提示**，不直接修改 Windsurf 的真实配置或发起登录。
  - 后续可以在此基础上扩展为：
    - 调用外部登录脚本（传入 email/password）；
    - 切换到该账号的配置快照并重启 Windsurf。

### 4.2 MCP / Rules Tab

该 Tab 采用左右分栏：

- 左侧：MCP Servers
- 右侧：Rules

#### 4.2.1 MCP Servers

- **打开 MCP 文件**
  - 点击「打开 MCP 文件」，选择一个 JSON 文件；
  - JSON 结构应与 `McpServerConfig` 对应：
    - `id: str`
    - `name: str`
    - `command: str`
    - `args: List[str]`
    - `env: Dict[str, str]`
    - `enabled: bool`

- **保存/备份 MCP 文件**
  - 「保存 MCP 文件」：
    - 如果之前是通过「打开」加载的，会覆盖原路径；
    - 否则会提示选择一个保存路径。
  - 「备份 MCP…」：
    - 将当前内存中的 MCP 列表写入你选择的备份 JSON 文件。

- **编辑 MCP**
  - 「新建」：
    - 弹出对话框填写：ID、名称、命令、参数（空格分隔）、环境变量（每行 `KEY=VALUE`）、启用状态。
  - 「编辑」或**双击表格行**：
    - 修改上述字段后保存即可。
  - 「删除」：
    - 支持多选删除，然后可再选择保存或备份。

#### 4.2.2 Rules

- **打开 Rules 文件**
  - 点击「打开 Rules 文件」，选择一个 JSON 文件；
  - 预期结构：`[{ "id": "...", "prompt": "..." }, ...]`。

- **保存/备份 Rules 文件**
  - 「保存 Rules 文件」：
    - 覆盖当前路径或另存为。
  - 「备份 Rules…」：
    - 将当前 Rules 列表写入备份 JSON 文件。

- **编辑 Rules**
  - 「新建」：
    - 设置 `ID` 和多行 `prompt` 文本。
  - 「编辑」或**双击行**：
    - 修改已有 Rule 的 ID / prompt。
  - 「删除」：
    - 支持多选删除，然后可再选择保存或备份。

> 目前 MCP / Rules Tab 侧重于本地 JSON 配置管理。后续可以根据实际 Windsurf 配置文件格式，增加“从 Windsurf 导入 / 导出到 Windsurf”的映射逻辑。

---

## 5. 目录结构

项目主要结构如下：

```text
windsurf-account-manager/
├── main.py                    # 应用入口
├── requirements.txt
├── PROJECT_STATUS.md          # 项目进度与 ROADMAP 文档
├── docs/
│   └── LOGIN_AND_CONFIG_ANALYSIS.md  # 登录流程逆向分析 & Linux 配置路径推断
└── windsurf_account_manager/
    ├── __init__.py
    ├── models.py              # 数据模型: Account, McpServerConfig, RuleConfig, AppSettings
    ├── storage.py             # 账号本地存储（accounts.json 导入/导出）
    ├── ui_main.py             # Tkinter 主界面与交互逻辑
    ├── api_client.py          # 远程 API 客户端占位
    ├── mcp_rules.py           # MCP / Rules JSON 读写辅助函数
    └── machine_code.py        # 机器码备份/恢复占位（待集成真实路径和协议）
```

> 账号数据会存放在 `windsurf_account_manager/data/accounts.json`（运行时自动创建目录和文件）。

---

## 6. 相关文档

- **登录流程逆向分析 & Linux 配置路径推断**  
  `docs/LOGIN_AND_CONFIG_ANALYSIS.md`

  包含：
  - 从 email/password 到各类 token 的推测性链路；
  - gRPC proto 中相关 RPC 与字段说明；
  - 推荐的外部登录脚本结构；
  - 在 Linux 上查找 Windsurf 配置文件的建议方法；
  - “切号 = 配置快照切换”的详细方案。

- **项目进度 / ROADMAP**  
  `PROJECT_STATUS.md`

  包含：
  - 当前已完成功能；
  - 正在进行的任务；
  - 短期与中期计划；
  - 使用建议与注意事项。

---

## 7. 后续计划（简要）

- 在 Tkinter 应用中增加：
  - 应用设置界面：配置 Windsurf 本地路径、MCP/Rules 实际路径、重启命令、外部登录脚本命令模板等；
  - “为当前账号保存配置快照”按钮；
  - “一键从快照切号”逻辑（包含配置备份与恢复）。
- 根据实际抓到的 Windsurf 配置文件结构：
  - 将 MCP / Rules Tab 的 JSON 结构与真实结构对齐；
  - 实现“从 Windsurf 读取/写回 MCP & Rules”。
- 在合规范围内，对 `api_client.py` 进行封装，用于：
  - 获取当前用户、Plan 信息、额度使用情况；
  - 为 UI 提供实时数据展示能力。

---

## 8. 免责声明

- 本项目仅用于学习与个人研究目的；
- 登录流程分析基于公开资料与推测，不保证完全准确；
- 请在使用本项目及任何相关脚本时，自行确保遵守 Windsurf / Codeium / Firebase 及操作系统的相关条款与法律规定，并自行承担风险。
