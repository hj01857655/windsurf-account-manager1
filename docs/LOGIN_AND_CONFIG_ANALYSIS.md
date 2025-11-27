# Windsurf / Codeium 登录流程逆向分析与 Linux 配置路径推断

> 本文档基于现有 gRPC proto（`seat_management_pb.proto`, `codeium_common_pb.proto`, `v1.proto`）、axios 测试脚本和通用 Firebase Auth / gRPC over HTTP 经验进行**推测性分析**，用于帮助你理解整体流程与接口。

---

## 1. 整体目标与限制

- **目标 1：理解从 email/password 到各类 token 的典型链路**
  - email/password → `firebase_id_token`
  - `firebase_id_token` → `auth_token`（通过 `GetOneTimeAuthToken`）
  - `auth_token` → 用户信息与 plan（`GetCurrentUser`）
  - `session_token`? → `api_key`（`GetPrimaryApiKeyForDevsOnly`）
  - Bearer token → `GetCurrentPeriodUsage`（额度查询）

---

## 2. 关键 proto 与已有示例回顾

### 2.1 SeatManagementService（用户/座位相关）

`proto/seat_management_pb.proto` 中关键 RPC：

```proto
service SeatManagementService {
  rpc UserSSOLoginRedirect(UserSSOLoginRedirectRequest) returns (UserSSOLoginRedirectResponse);
  rpc GetCurrentUser(GetCurrentUserRequest) returns (GetCurrentUserResponse);
  rpc GetOneTimeAuthToken(GetOneTimeAuthTokenRequest) returns (GetOneTimeAuthTokenResponse);
  rpc RegisterUser(RegisterUserRequest) returns (RegisterUserResponse);
}
```

常见字段（从 pbs.js / proto 中可见）：

- `GetOneTimeAuthTokenRequest` 中含：`firebase_id_token`（Firebase 登录得到的 `idToken`）
- `GetCurrentUserRequest` 中含：`auth_token`，同时 HTTP 头里有 `X-Auth-Token`
- `RegisterUserRequest` 可能也带有 `firebase_id_token` 类字段
- 还有 `GetPrimaryApiKeyForDevsOnlyRequest { session_token }` 等接口，用于取得 dev-only API Key

### 2.2 用户与计划信息结构

在 `GetCurrentUserResponse` / `UserStatus` / `PlanInfo` / `PlanStatus` 等 message 中：

- `User`：包含 `api_key`, `email`, `pro`, `id`, `team_id`, 各种偏好字段等
- `PlanInfo`：`plan_name`, `teams_tier`, `monthly_prompt_credits`, `monthly_flow_credits`, `cascade_web_search_enabled` 等
- `PlanStatus`：`plan_start`, `plan_end`, `available_credits`, `used_prompt_credits`, `used_flow_credits` 等
- `UserStatus`：汇总了 plan 状态、权限、`has_fingerprint_set` 等

这些字段是**你桌面应用展示账号信息 / 额度状态的主要数据源**。

### 2.3 DashboardService / GetCurrentPeriodUsage

`proto/v1.proto` 中：

```proto
service DashboardService {
  rpc GetCurrentPeriodUsage(GetCurrentPeriodUsageRequest)
      returns (GetCurrentPeriodUsageResponse);
}
```

已有 axios 示例（TypeScript）显示：

- URL：`https://api2.cursor.sh/aiserver.v1.DashboardService/GetCurrentPeriodUsage`
- 请求体：空（`GetCurrentPeriodUsageRequest {}`）
- 头部：`Authorization: Bearer <token>`

这里的 `<token>` 很可能是某种 **会话 JWT / cursor_jwt**，具体来源需结合实际网络流量确认。

---

## 3. 从 email/password 到 firebase_id_token（Firebase Auth 通用流程）

> 本节基于标准 Firebase Auth REST API 公开文档，**不是**来自 Windsurf 私有实现代码。Windsurf 的 Web 登录很可能使用类似机制。

### 3.1 获取 Firebase 项目配置

在典型前端 SPA（React/Vue）项目中，入口 HTML / JS 包含类似：

```js
const firebaseConfig = {
  apiKey: "...",
  authDomain: "...",
  projectId: "...",
  // ...
};
```

在浏览器中打开 Windsurf / Cursor 登陆页面时，通过 DevTools：

- 在 `Sources` / `Network` / `Page` 里搜索 `firebaseConfig`、`apiKey`、`authDomain`；
- 或在 `window` 全局对象 / 打包输出 JS 中查找 `firebase.initializeApp` 调用；
- 这样可以定位 Windsurf 使用的 Firebase 项目 `apiKey`。

### 3.2 Firebase REST 登录接口（通用）

Firebase 官方支持通过 REST API 登录邮箱密码用户：

- Endpoint（示例）：

  ```text
  POST https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=<FIREBASE_API_KEY>
  ```

- 请求体（JSON）：

  ```json
  {
    "email": "user@example.com",
    "password": "***",
    "returnSecureToken": true
  }
  ```

- 返回体（简化）：

  ```json
  {
    "idToken": "<FIREBASE_ID_TOKEN>",
    "refreshToken": "...",
    "expiresIn": "3600",
    "localId": "...",
    "email": "user@example.com"
  }
  ```

其中：

- `idToken` 即常见的 **Firebase ID Token**（JWT），在 Windsurf proto 里通常对应 `firebase_id_token` 字段；
- 你可以在浏览器里通过登录操作+抓包来验证他们是否使用这个或类似接口；
- 如果 Windsurf 使用 SSO / OAuth / 其他 IdP，流程会稍有不同，但**核心仍是从前端拿到一个 Firebase 或自有的 ID Token**。

### 3.3 风险与注意事项

- 不要在不可信环境中硬编码邮箱/密码和 `apiKey`；
- 使用此类接口编写脚本时，你需要：
  - 自己承担账号安全风险；
  - 遵守 Firebase 与 Windsurf 的服务条款；
  - 对异常 / 多因素登录 / 设备指纹校验做好处理。

---

## 4. firebase_id_token → auth_token → 用户信息

### 4.1 GetOneTimeAuthToken（ID Token 换应用 auth_token）

根据 proto / pbs.js 中的结构：

```proto
message GetOneTimeAuthTokenRequest {
  string firebase_id_token = 1;
  // ... 可能还有 metadata 等字段
}

message GetOneTimeAuthTokenResponse {
  string auth_token = 1;
}
```

HTTP 访问方式（推测，参考 axios-protobuf-advanced 示例）：

- URL 模式：`https://api2.cursor.sh/exa.seat_management.v1.SeatManagementService/GetOneTimeAuthToken`
- Method：`POST`
- Body：
  - content-type: `application/proto`
  - 使用 protobuf 序列化后的 `GetOneTimeAuthTokenRequest` 二进制
- 无需额外认证（或只依赖公共 metadata）

**推测流程**：

1. 客户端已持有 `firebase_id_token`；
2. 构造 `GetOneTimeAuthTokenRequest { firebase_id_token: "..." }`；
3. 调用 `SeatManagementService.GetOneTimeAuthToken`；
4. 得到 `auth_token`（Windsurf 自己的会话 token / 用户 auth token）。

> 注意：具体 URL（`api2.cursor.sh`）与 service 名称需要结合实际生成的 TypeScript 客户端或浏览器抓包确认。

### 4.2 GetCurrentUser（通过 auth_token 拉取完整账号信息）

axios 示例（仓库中已有）：

- Body：`GetCurrentUserRequest`，内含字段：
  - `auth_token`
  - `generateProfilePictureUrl`
  - `createIfNotExist`
  - `includeSubscription`
- Header：
  - `X-Auth-Token: <auth_token>`

**流程**：

1. 持有 `auth_token`；
2. 调用 `SeatManagementService.GetCurrentUser`；
3. 得到 `GetCurrentUserResponse`：
   - `user`（含 `api_key`, `email`, `pro`, `id`, `team_id` 等）；
   - `plan_info`, `subscription`, `permissions`, `user_team_details` 等；
4. 这些字段可以直接用于你的桌面应用 UI 显示：
   - 账号等级 / 是否 Pro；
   - 各种 plan 特性（是否开启 web search、能否自动运行命令等）。

---

## 5. api_key 与 session_token / dev-only 接口（推测）

### 5.1 GetPrimaryApiKeyForDevsOnly

proto 中存在：

```proto
message GetPrimaryApiKeyForDevsOnlyRequest {
  string session_token = 1;
}

message GetPrimaryApiKeyForDevsOnlyResponse {
  string api_key = 1;
}
```

这表明：

- 存在一条链路：`session_token` → 开发者 Primary API Key；
- 但 **仓库中目前没有** 从 `auth_token` 获取 `session_token` 的直接示例；
- 很可能在 Web 前端登录流程中，通过某些浏览器接口 / cookies / 重定向才能获得。

### 5.2 实际可用的信息来源

对你当前的桌面应用来说，更重要的是：

- `GetCurrentUserResponse.user.api_key`：
  - 如果后端仍在返回此字段，你可以通过 `auth_token` + `GetCurrentUser` 直接拿到；
- 不一定需要走 `GetPrimaryApiKeyForDevsOnly` 这条链，除非你要做和 dev console 一样的功能。

### 5.3 未知与 TODO

- `auth_token` 与 `session_token` 之间的精确关系：
  - 可能通过其他 RPC / 重定向 / cookie 交换；
  - 需要你在浏览器中登录 Windsurf 帐号，观察 Network 中的 gRPC / REST 请求来确认；
- `cursor_jwt` / Bearer token 的生成方式：
  - 同样需要抓包确认，是由 `auth_token` 换来的，还是登录时一次性返回。

---

## 6. GetCurrentPeriodUsage 所需 Bearer token（推测）

已有 TS 示例：

- URL：`https://api2.cursor.sh/aiserver.v1.DashboardService/GetCurrentPeriodUsage`
- Header：`Authorization: Bearer <token>`

常见可能：

1. `<token>` 是某种 **用户 JWT**（例如 `cursor_jwt`）；
2. 该 JWT 可能来源：
   - 登录成功后前端从某个 cookie / localStorage 中拿到；
   - 或通过一次专门的 `GetUserStatus` / `GetJwt` / `CreateSession` 类 RPC 获得。

要确认：

- 在浏览器里登录 Windsurf；
- 搜索所有对 `GetCurrentPeriodUsage` 的网络请求；
- 查看 Request Headers 中 `Authorization` 的值；
- 反向搜索这个 token 首次出现在哪个响应体 / Set-Cookie / redirect 中。

在桌面应用中，如果你已经有了对应 JWT：

- 你可以直接调用 `GetCurrentPeriodUsage`，返回 `GetCurrentPeriodUsageResponse`，再展示额度信息；
- 但 **如何安全地获取和更新这个 JWT**，需要你在外部脚本里自己设计（例如通过浏览器自动化 / 官方支持的 CLI / login flow）。

---

## 7. 外部登录脚本的推荐结构（高层设计）

> 本节只描述接口与数据流示意，不给出可直接运行的脚本实现。

建议你把真正的登录逻辑写成一个**命令行工具**，Tkinter 应用只负责调用它，比如：

```bash
python my_windsurf_login.py \
  --email <email> \
  --password <password> \
  --output-config /path/to/generated_config.json
```

推荐脚本内部的大致流程：

1. **通过 Firebase REST 或其它 IdP 接口**：
   - 输入：`email`, `password`；
   - 输出：`firebase_id_token`（或等价的 ID Token）。

2. **调用 SeatManagementService.GetOneTimeAuthToken**：
   - 使用 protobuf 客户端（TS / Python 都可以），构造请求：
     - `firebase_id_token: <上一步得到的 token>`；
   - 得到：`auth_token`。

3. **调用 SeatManagementService.GetCurrentUser**：
   - 请求体中填入 `auth_token`，并在 HTTP 头中带上 `X-Auth-Token`；
   - 得到 `GetCurrentUserResponse`，从中提取：
     - `user.api_key`（如果仍然存在）
     - `user.email`, `user.id` 等
     - `plan_info`, `plan_status` 等

4. **（可选）获取 Bearer JWT 与其他 token**：
   - 按实际抓包结果，补充执行对应的 RPC / REST 接口，拿到：
     - `cursor_jwt` / `session_token` / 其他 JWT；

5. **生成本地配置文件**（供 Windsurf 或你的桌面应用使用）：
   - 例如：

     ```json
     {
       "email": "...",
       "auth_token": "...",
       "api_key": "...",
       "cursor_jwt": "...",
       "plan_name": "...",
       "plan_end": 1735689600
     }
     ```

6. **由 Tkinter 应用在“切号”时调用该脚本**：
   - 你在设置中配置一条外部命令模板：

     ```text
     python my_windsurf_login.py --email {email} --password {password} --output-config /path/to/config_{id}.json
     ```

   - 切换账号时，桌面应用根据选中账号的 email/password 填充模板并执行，之后再按约定位置读取生成的配置。

---

## 8. Linux 下 Windsurf 本地配置路径推断

> 本节只给出**可能的路径模式与调查方法**，实际路径需要你在本机上验证。

### 8.1 常见桌面应用配置路径模式

在 Linux 上，Electron / 桌面应用一般会把配置放在：

- `~/.config/<AppName>`
- `~/.<appname>`
- `~/.local/share/<AppName>`

其中：

- Cursor / Windsurf 这类 IDE 可能用的 AppName 包括：`Cursor`、`Windsurf`、`cursor`、`windsurf` 等；
- 也有可能放在 `~/.config/Codeium` 或其他厂商品牌名目录下。

### 8.2 MCP / Rules 相关文件名线索

根据你当前工程和 proto 内容：

- MCP 服务器配置类型为 `McpServerConfig`；
- TeamConfig 中有字段 `allowed_mcp_servers`；
- 实际桌面应用中，MCP 配置很可能被序列化到类似：
  - `mcp_config.json`
  - 或某个更大的 `settings.json` / `config.json` 中的嵌套字段。

Rules 部分：

- proto 中定义了简单的 `Rule { string id; string prompt; }`；
- 桌面端可能：
  - 把它们存在单独的 `rules.json`；
  - 或放进统一配置文件内，如 `user_config.json` 的某个字段。

### 8.3 推荐的本机调查步骤（只读操作）

在你的 Linux 机器上，可以用只读命令查找线索（示意）：

1. **搜索可能的目录名：**

   ```bash
   ls ~/.config
   ls ~/.local/share
   ls ~
   ```

   关注目录名：`Cursor` / `Windsurf` / `windsurf` / `codeium` 等。

2. **在这些目录下搜索关键文件名：**

   ```bash
   find ~/.config -maxdepth 4 -iname "*windsurf*" -o -iname "*cursor*" -o -iname "*codeium*"
   find ~/.config -maxdepth 6 -iname "*mcp*" -o -iname "*rules*"
   ```

3. **在可疑目录中搜索关键词：**

   例如，在某个候选目录下：

   ```bash
   grep -R "mcp" ~/.config/Windsurf 2>/dev/null | head
   grep -R "rules" ~/.config/Windsurf 2>/dev/null | head
   grep -R "device_fingerprint" ~/.config/Windsurf 2>/dev/null | head
   ```

   - 如果是 JSON / SQLite 等，可以优先关注 `.json` 文件和 `settings` / `config` 命名的文件。

> 建议：**任何修改前都先备份整个目录**，例如：
>
> ```bash
> tar czf windsorf-config-backup-$(date +%s).tar.gz ~/.config/Windsurf
> ```

### 8.4 与 Tkinter 工具集成的思路

一旦你在 Linux 上确认了真实的 Windsurf 配置路径，例如：

- `~/.config/Windsurf/config.json`
- `~/.config/Windsurf/mcp_config.json`
- `~/.config/Windsurf/rules.json`

就可以在 Tkinter 应用中：

1. 在设置中存储这些路径（可写到 `AppSettings` 中）。
2. 在“切换到选中账号”时：
   - 如果该账号有一份独立的配置快照（例如 `snapshots/<account_id>/config.json`），则：
     - 先备份当前真实配置为 `backup/config.json.bak-<timestamp>`；
     - 再把快照复制覆盖真实路径；
   - 如果没有快照，则提示用户先为该账号创建配置快照（例如通过外部登录脚本或其他自动化方式生成配置）。
3. 可选：执行用户配置的「重启 Windsurf」命令，例如：

   ```text
   flatpak run dev.windsurf.app
   ```

---

## 9. “切号 = 配置快照切换”的推荐方案

结合上面的分析，一个相对安全、可控的策略是：

### 9.1 准备阶段（为每个账号创建至少一个配置快照）

1. 使用你选择的登录方式（推荐外部脚本或其他自动化流程），为目标账号获取有效的 token / 配置，并写入 Windsurf 使用的配置目录；
2. 在 Tkinter 工具中：
   - 选中对应账号；
   - 使用一个未来要实现的“保存当前配置为该账号快照”的功能：
     - 把 `~/.config/Windsurf/...` 中的关键配置文件复制到 `snapshots/<account_id>/...`；
     - 记录快照路径和时间戳。

对每个账号重复一次，就得到一组**配置快照**。

### 9.2 切号阶段

当你在 Tkinter 应用中点击“切换到选中账号”时：

1. 工具检查该账号是否已有快照：
   - 若无，提示你：
     - “此账号尚未创建配置快照，请先为该账号创建配置快照（例如通过外部脚本生成）”；
   - 若有，则继续。
2. 先为当前真实配置创建时间戳备份：

   ```text
   ~/.config/Windsurf/config.json -> backups/config.json.bak-<timestamp>
   ```

3. 把目标账号的快照文件复制覆盖真实配置路径；
4. 按需执行“重启 Windsurf”命令（你自己在设置中配置）。

**效果：**

- 对 Windsurf 来说，相当于你新打开时看到的是“另外一个账号最后一次退出时的本地状态”；
- 从外观上就实现了“切号并自动处于已登录状态”。

### 9.3 与外部登录脚本结合

如果你再加上外部登录脚本（见第 7 节）：

1. 当你觉得某个账号快照可能过期：
   - 通过外部登录脚本为该账号生成新的 token / 配置文件并更新 Windsurf 配置；
   - 然后再次在 Tkinter 工具里“保存为该账号快照”。
2. 这样：
   - 日常切号只做“配置快照切换”；
   - 偶尔更新一次登录状态时才需要用脚本真正登录一次。

---

## 10. 小结

- **登录链路（推测）**：
  - email/password → Firebase `idToken` (`firebase_id_token`)；
  - `firebase_id_token` → `auth_token` (`GetOneTimeAuthToken`)；
  - `auth_token` → `GetCurrentUser` → `User` / `PlanInfo` / `PlanStatus` / `api_key` 等；
  - 其他 token（`session_token` / `cursor_jwt` / Bearer）需要结合实际网络流量确认。

- **桌面工具职责**：
  - 账号本地管理（你已经有了）；
  - MCP / Rules JSON 管理（你已经有了）；
  - “切号 = 配置快照切换 + 可选执行外部命令”；
  - 登录脚本由你自行实现，工具只负责传入 email/password 或账号 ID。

- **Linux 配置路径**：
  - 很可能在 `~/.config/Windsurf` 或相近目录；
  - 建议通过只读方式查找、grep 关键词、确认 JSON 结构后再做任何写入操作；
  - 所有写操作前均应做时间戳备份。

后续如果你在 Linux 上找到了实际的 Windsurf 配置目录和关键 JSON 文件内容，可以把路径 + 示例结构贴出来，我可以再帮你：

- 对齐 Tkinter 工具中的 `McpServerConfig` / `RuleConfig` 字段；
- 设计具体的“导入自 Windsurf / 导出到 Windsurf”的桥接逻辑；
- 进一步细化“每个账号的配置快照”在磁盘上的目录和命名方案。
