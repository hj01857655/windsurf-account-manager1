# Windsurf Account Manager 项目进度

## 1. 项目概览

- **目标**：开发一个基于 Python Tkinter 的桌面工具，用于管理 Windsurf 账号 / 机器码 / MCP / Rules，并支持在切换账号时自动完成登录（通过配置切换或外部登录脚本 Hook）。
- **主要功能模块**：
  - **账号管理**：导入、展示、编辑、批量删除、导出、切号。
  - **机器码 / 配置管理**：备份、恢复、重置（需要先确认 Windsurf 本地路径和协议）。
  - **MCP / Rules 管理**：本地配置的备份 / 恢复 / 添加 / 编辑 / 删除。
  - **登录流程集成**：基于 email/password 的自动登录流程 Hook（配置切换 / 外部脚本），不在本项目内部实现自动登录脚本本身。

---

## 2. 运行与环境

- **Python 版本**：建议 Python 3.10+（当前开发环境为 Python 3.12）。
- **依赖管理**：使用 venv + `requirements.txt`。

### 2.1 环境准备

```bash
cd /home/zhengxueen/workspace/windsurf-tool/windsurf-account-manager

# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境（bash/zsh）
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

> 注：Tkinter 需要通过系统包安装（例如 Debian/Ubuntu 上 `sudo apt-get install python3-tk`），不是 pip 包。

### 2.2 启动应用

```bash
cd /home/zhengxueen/workspace/windsurf-tool/windsurf-account-manager
source .venv/bin/activate
python main.py
```

---

## 3. 当前代码结构

- `main.py`：应用入口，负责创建 Tk 主窗口并运行 UI。
- `windsurf_account_manager/`
  - `__init__.py`
  - `models.py`：数据模型
    - `Account`：本地账号对象，包含 `id/email/password/note/plan_*` 等字段。
    - `McpServerConfig`：MCP 服务器配置模型。
    - `RuleConfig`：规则配置模型。
    - `AppSettings`：应用设置（MCP/Rules 路径、Windsurf 配置路径、重启命令等）。
  - `storage.py`：账号本地存储
    - `load_accounts()` / `save_accounts()`：读写 `data/accounts.json`。
    - `import_from_windsurf_json(path, existing)`：从 `windsurf.json` 导入账号列表（按 email 去重）。
    - `export_accounts(path, accounts)`：导出账号列表为 JSON。
  - `ui_main.py`：Tkinter 主界面
    - Tab1「账号管理」：账号列表与相关操作。
    - Tab2「MCP / Rules」：占位（待实现实际管理 UI）。
  - `api_client.py`：远程 API 客户端占位（后续可接 gRPC/HTTP 调用）。
  - `mcp_rules.py`：MCP / Rules 的本地 JSON 读写工具。
  - `machine_code.py`：机器码备份/恢复的占位函数（待确定 Windsurf 配置路径后实现）。

---

## 4. 已完成功能

### 4.1 Tkinter 应用骨架

- 已实现：
  - 创建主窗口（标题、大小）。
  - 使用 `Notebook` 分出「账号管理」和「MCP / Rules」两个 Tab。

### 4.2 账号管理模块（Tab: 账号管理）

- **账号持久化**：
  - 启动时从 `data/accounts.json` 加载账号列表（如果文件不存在则视为空）。
  - 所有更改自动写回 `data/accounts.json`。

- **导入 / 导出**：
  - 「从 windsuf.json 导入」：
    - 选择一个 JSON 文件（例如工作区根目录的 `windsurf.json`）。
    - 支持按 email 去重导入账号，自动为新账号生成 `id`。
  - 「导出账号」：
    - 将当前账号列表导出为 JSON（可自定义保存路径）。

- **列表展示**：
  - 使用 `Treeview` 展示账号：
    - 列：邮箱、备注、计划名、到期时间。

- **批量删除**：
  - 支持多选删除账号，并持久化到本地。

- **快捷勾选**：
  - 「全选」：选中当前表格所有账号行。
  - 「全不选」：清空当前选中状态。

- **账号详情编辑**：
  - 方式一：选中一行，点击「编辑详情」。
  - 方式二：双击账号行。
  - 弹出对话框：
    - 邮箱：只读显示。
    - 备注：可编辑。
    - 点击「保存」后更新本地数据并刷新列表。

- **切号 Hook / 当前账号标记**：
  - 「切换到选中账号」按钮：
    - 选中单个账号后点击，设置该账号为当前账号。
    - 当前账号在列表中会以淡蓝色背景高亮显示。
    - 弹出提示说明：后续“切号相关操作”（例如配置切换或外部登录脚本）会基于该账号执行。
  - 当前版本尚未真正改动 Windsurf 配置或触发登录，只负责**状态标记和 UI 提示**，作为后续自动登录/配置切换的 Hook。

---

## 5. 进行中的工作

### 5.1 MCP / Rules 管理 UI

- 目标：在「MCP / Rules」Tab 内实现：
  - MCP server 列表展示、添加、编辑、删除。
  - Rules 列表展示、添加、编辑、删除。
  - 从本地 JSON 文件加载 / 保存 MCP 与 Rules 配置。
  - 支持备份 / 恢复配置快照。
- 当前状态：
  - `mcp_rules.py` 中已有基础 JSON 读写函数。
  - UI 仍为占位 Label，准备增强为完整配置管理界面。

### 5.2 登录流程逆向分析文档

- 目标：
  - 基于现有 gRPC proto（`seat_management_pb.proto`, `codeium_common_pb.proto`, `v1.proto`）和 axios 测试脚本，梳理从 email/password 到各类 token 的流程：
    - `firebase_id_token`
    - `auth_token`（`GetOneTimeAuthToken`）
    - `User` / `PlanInfo` / `PlanStatus`（`GetCurrentUser`）
    - `api_key`（`RegisterUser` / `GetPrimaryApiKeyForDevsOnly`）
    - `GetCurrentPeriodUsage` 所需 Bearer token
  - 输出为一份中文文档，说明涉及的接口、请求字段和依赖关系，**不提供可直接运行的自动登录脚本**。
- 当前状态：
  - 已完成 proto/示例代码的初步阅读与关键字段梳理。
  - 正在整理文档结构和内容提纲。

### 5.3 Linux 上 Windsurf 本地配置路径调研

- 目标：
  - 找到或合理推断 Windsurf 在 Linux 上使用的配置目录及文件（包含账号配置、MCP、Rules、设备指纹/机器码等）。
  - 为后续“切号 = 切换配置快照 + 可选重启 Windsurf”提供基础。
- 当前状态：
  - 尚未在本项目中写入自动探测逻辑。
  - 计划参考常见 Electron/桌面应用路径（如 `~/.config/...`）并结合实际安装情况验证。

---

## 6. 后续计划

短期目标：

1. **完善 MCP / Rules 管理 Tab**：
   - 完成 MCP/Rules 的本地 JSON 编辑 UI。
   - 添加配置快照的备份/恢复功能。

2. **完成登录流程逆向分析文档**：
   - 将接口和数据结构整理为可读文档，协助编写外部登录脚本。

3. **初步实现“切号 = 配置切换”流程（Linux 优先）**：
   - 探测并确认 Linux 下的 Windsurf 配置路径。
   - 为每个账号提供“备份当前配置为此账号快照”的能力。
   - 在“切换到选中账号”时：
     - 恢复对应账号的配置快照到 Windsurf 配置目录。
     - 可选执行用户配置的 Windsurf 重启命令。

中期目标：

- 将登录流程文档中分析出的接口封装为 `api_client.py` 中的调用（在合规范围内）；
- 为外部登录脚本预留更灵活的 Hook（自定义命令模板、日志展示等）；
- 丰富 UI（过滤、搜索账号，按 plan 或备注分组显示等）。

---

## 7. 使用建议

- 项目目前处于**快速迭代阶段**：
  - 建议将实际登录逻辑放在独立脚本中，通过本工具传参调用，避免违反服务条款和安全约束；
  - 对机器码 / 配置相关操作，先做足路径与文件结构验证，并确保每一步都有备份（本项目会优先实现“配置快照”能力）。

- 如需在文档中补充更多内容（例如：
  - 登录流程的详细抓包截图说明；
  - 各操作系统上的实际配置路径；
  - 更细粒度的开发计划），可以直接在此文件追加对应章节。
