from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from .models import Account, McpServerConfig, RuleConfig
from . import storage, mcp_rules


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Windsurf Account Manager")
        self.root.geometry("900x600")

        self.accounts: List[Account] = storage.load_accounts()
        self.active_account_id = None

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.accounts_frame = ttk.Frame(self.notebook)
        self.mcp_rules_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.accounts_frame, text="账号管理")
        self.notebook.add(self.mcp_rules_frame, text="MCP / Rules")

        self._build_accounts_tab()
        self._build_mcp_rules_tab()

    def _build_accounts_tab(self) -> None:
        toolbar = ttk.Frame(self.accounts_frame)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=8, pady=4)

        btn_import = ttk.Button(toolbar, text="从 windsuf.json 导入", command=self.on_import_windsurf_json)
        btn_export = ttk.Button(toolbar, text="导出账号", command=self.on_export_accounts)
        btn_delete = ttk.Button(toolbar, text="批量删除", command=self.on_delete_selected)
        btn_refresh = ttk.Button(toolbar, text="刷新列表", command=self.refresh_accounts_view)
        btn_select_all = ttk.Button(toolbar, text="全选", command=self.on_select_all)
        btn_clear_sel = ttk.Button(toolbar, text="全不选", command=self.on_clear_selection)
        btn_edit = ttk.Button(toolbar, text="编辑详情", command=self.on_edit_selected)
        btn_switch = ttk.Button(toolbar, text="切换到选中账号", command=self.on_switch_account)

        btn_import.pack(side=tk.LEFT, padx=4)
        btn_export.pack(side=tk.LEFT, padx=4)
        btn_delete.pack(side=tk.LEFT, padx=4)
        btn_refresh.pack(side=tk.LEFT, padx=4)
        btn_select_all.pack(side=tk.LEFT, padx=4)
        btn_clear_sel.pack(side=tk.LEFT, padx=4)
        btn_edit.pack(side=tk.LEFT, padx=4)
        btn_switch.pack(side=tk.LEFT, padx=4)

        columns = ("email", "note", "plan_name", "plan_end")
        self.tree = ttk.Treeview(self.accounts_frame, columns=columns, show="headings", selectmode="extended")

        self.tree.heading("email", text="邮箱")
        self.tree.heading("note", text="备注")
        self.tree.heading("plan_name", text="计划")
        self.tree.heading("plan_end", text="到期时间")

        self.tree.column("email", width=260)
        self.tree.column("note", width=200)
        self.tree.column("plan_name", width=140)
        self.tree.column("plan_end", width=160)

        vsb = ttk.Scrollbar(self.accounts_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.accounts_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.tag_configure("active_account", background="#d0f0ff")
        self.tree.bind("<Double-1>", self.on_tree_double_click)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0), pady=4)
        vsb.pack(side=tk.LEFT, fill=tk.Y, pady=4)
        hsb.pack(side=tk.BOTTOM, fill=tk.X, padx=8)

        self.refresh_accounts_view()

    def _build_mcp_rules_tab(self) -> None:
        self.mcp_servers: List[McpServerConfig] = []
        self.rules: List[RuleConfig] = []
        self.mcp_config_path: Optional[Path] = None
        self.rules_config_path: Optional[Path] = None

        paned = ttk.PanedWindow(self.mcp_rules_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # MCP 区域
        frame_mcp = ttk.Frame(paned)
        paned.add(frame_mcp, weight=1)

        mcp_toolbar = ttk.Frame(frame_mcp)
        mcp_toolbar.pack(side=tk.TOP, fill=tk.X)

        btn_mcp_open = ttk.Button(mcp_toolbar, text="打开 MCP 文件", command=self.on_open_mcp_file)
        btn_mcp_save = ttk.Button(mcp_toolbar, text="保存 MCP 文件", command=self.on_save_mcp_file)
        btn_mcp_backup = ttk.Button(mcp_toolbar, text="备份 MCP...", command=self.on_backup_mcp)
        btn_mcp_add = ttk.Button(mcp_toolbar, text="新建", command=self.on_add_mcp)
        btn_mcp_edit = ttk.Button(mcp_toolbar, text="编辑", command=self.on_edit_mcp)
        btn_mcp_delete = ttk.Button(mcp_toolbar, text="删除", command=self.on_delete_mcp)

        for btn in (btn_mcp_open, btn_mcp_save, btn_mcp_backup, btn_mcp_add, btn_mcp_edit, btn_mcp_delete):
            btn.pack(side=tk.LEFT, padx=4, pady=4)

        mcp_columns = ("id", "name", "command", "enabled")
        self.tree_mcp = ttk.Treeview(frame_mcp, columns=mcp_columns, show="headings", selectmode="extended")

        self.tree_mcp.heading("id", text="ID")
        self.tree_mcp.heading("name", text="名称")
        self.tree_mcp.heading("command", text="命令")
        self.tree_mcp.heading("enabled", text="启用")

        self.tree_mcp.column("id", width=170)
        self.tree_mcp.column("name", width=140)
        self.tree_mcp.column("command", width=240)
        self.tree_mcp.column("enabled", width=60, anchor=tk.CENTER)

        mcp_vsb = ttk.Scrollbar(frame_mcp, orient="vertical", command=self.tree_mcp.yview)
        self.tree_mcp.configure(yscrollcommand=mcp_vsb.set)

        self.tree_mcp.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=(4, 0))
        mcp_vsb.pack(side=tk.LEFT, fill=tk.Y, pady=(4, 0))

        self.tree_mcp.bind("<Double-1>", self.on_tree_mcp_double_click)

        # Rules 区域
        frame_rules = ttk.Frame(paned)
        paned.add(frame_rules, weight=1)

        rules_toolbar = ttk.Frame(frame_rules)
        rules_toolbar.pack(side=tk.TOP, fill=tk.X)

        btn_rules_open = ttk.Button(rules_toolbar, text="打开 Rules 文件", command=self.on_open_rules_file)
        btn_rules_save = ttk.Button(rules_toolbar, text="保存 Rules 文件", command=self.on_save_rules_file)
        btn_rules_backup = ttk.Button(rules_toolbar, text="备份 Rules...", command=self.on_backup_rules)
        btn_rules_add = ttk.Button(rules_toolbar, text="新建", command=self.on_add_rule)
        btn_rules_edit = ttk.Button(rules_toolbar, text="编辑", command=self.on_edit_rule)
        btn_rules_delete = ttk.Button(rules_toolbar, text="删除", command=self.on_delete_rules)

        for btn in (btn_rules_open, btn_rules_save, btn_rules_backup, btn_rules_add, btn_rules_edit, btn_rules_delete):
            btn.pack(side=tk.LEFT, padx=4, pady=4)

        rules_columns = ("id", "prompt")
        self.tree_rules = ttk.Treeview(frame_rules, columns=rules_columns, show="headings", selectmode="extended")

        self.tree_rules.heading("id", text="ID")
        self.tree_rules.heading("prompt", text="提示词")

        self.tree_rules.column("id", width=170)
        self.tree_rules.column("prompt", width=260)

        rules_vsb = ttk.Scrollbar(frame_rules, orient="vertical", command=self.tree_rules.yview)
        self.tree_rules.configure(yscrollcommand=rules_vsb.set)

        self.tree_rules.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=(4, 0))
        rules_vsb.pack(side=tk.LEFT, fill=tk.Y, pady=(4, 0))

        self.tree_rules.bind("<Double-1>", self.on_tree_rules_double_click)

        self.refresh_mcp_view()
        self.refresh_rules_view()

    def refresh_accounts_view(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for acc in self.accounts:
            tags = ("active_account",) if acc.id == self.active_account_id else ()
            self.tree.insert(
                "",
                tk.END,
                iid=acc.id,
                values=(acc.email, acc.note, acc.plan_name or "", acc.plan_end or ""),
                tags=tags,
            )

    def on_import_windsurf_json(self) -> None:
        path_str = filedialog.askopenfilename(
            title="选择 windsuf.json",
            filetypes=(("JSON 文件", "*.json"), ("所有文件", "*.*")),
        )
        if not path_str:
            return
        path = Path(path_str)
        try:
            self.accounts = storage.import_from_windsurf_json(path, self.accounts)
            storage.save_accounts(self.accounts)
            self.refresh_accounts_view()
        except Exception as exc:
            messagebox.showerror("导入失败", f"导入 windsuf.json 失败: {exc}")

    def on_export_accounts(self) -> None:
        path_str = filedialog.asksaveasfilename(
            title="导出账号",
            defaultextension=".json",
            filetypes=(("JSON 文件", "*.json"), ("所有文件", "*.*")),
        )
        if not path_str:
            return
        path = Path(path_str)
        try:
            storage.export_accounts(path, self.accounts)
        except Exception as exc:
            messagebox.showerror("导出失败", f"导出账号失败: {exc}")

    def on_delete_selected(self) -> None:
        selected = list(self.tree.selection())
        if not selected:
            return
        if not messagebox.askyesno("确认删除", f"确定要删除选中的 {len(selected)} 个账号吗？"):
            return
        remaining = [a for a in self.accounts if a.id not in selected]
        self.accounts = remaining
        if self.active_account_id in selected:
            self.active_account_id = None
        storage.save_accounts(self.accounts)
        self.refresh_accounts_view()

    def on_select_all(self) -> None:
        items = self.tree.get_children()
        if not items:
            return
        self.tree.selection_set(items)

    def on_clear_selection(self) -> None:
        self.tree.selection_remove(self.tree.selection())

    def on_edit_selected(self) -> None:
        selected = list(self.tree.selection())
        if not selected:
            messagebox.showinfo("编辑详情", "请先选择一个账号。")
            return
        if len(selected) > 1:
            messagebox.showinfo("编辑详情", "一次仅支持编辑一个账号，请只选择一个账号。")
            return
        self._edit_account(selected[0])

    def on_tree_double_click(self, _event: tk.Event) -> None:  # type: ignore[override]
        item_id = self.tree.focus()
        if not item_id:
            return
        self._edit_account(item_id)

    def _edit_account(self, acc_id: str) -> None:
        acc = next((a for a in self.accounts if a.id == acc_id), None)
        if acc is None:
            return

        win = tk.Toplevel(self.root)
        win.title("编辑账号详情")
        win.transient(self.root)
        win.grab_set()

        frm = ttk.Frame(win)
        frm.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        ttk.Label(frm, text="邮箱:").grid(row=0, column=0, sticky=tk.W, pady=4)
        email_var = tk.StringVar(value=acc.email)
        ent_email = ttk.Entry(frm, textvariable=email_var, state="readonly", width=40)
        ent_email.grid(row=0, column=1, sticky=tk.W, pady=4)

        ttk.Label(frm, text="备注:").grid(row=1, column=0, sticky=tk.W, pady=4)
        note_var = tk.StringVar(value=acc.note)
        ent_note = ttk.Entry(frm, textvariable=note_var, width=40)
        ent_note.grid(row=1, column=1, sticky=tk.W, pady=4)

        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=(12, 0))

        def on_ok() -> None:
            acc.note = note_var.get()
            storage.save_accounts(self.accounts)
            self.refresh_accounts_view()
            win.destroy()

        def on_cancel() -> None:
            win.destroy()

        btn_ok = ttk.Button(btn_frame, text="保存", command=on_ok)
        btn_cancel = ttk.Button(btn_frame, text="取消", command=on_cancel)
        btn_ok.pack(side=tk.LEFT, padx=4)
        btn_cancel.pack(side=tk.LEFT, padx=4)

        win.bind("<Return>", lambda _e: on_ok())
        win.bind("<Escape>", lambda _e: on_cancel())

    def on_switch_account(self) -> None:
        selected = list(self.tree.selection())
        if not selected:
            messagebox.showinfo("切换账号", "请先选择一个要切换的账号。")
            return
        if len(selected) > 1:
            messagebox.showinfo("切换账号", "一次仅支持切换到一个账号，请只选择一个账号。")
            return

        acc_id = selected[0]
        acc = next((a for a in self.accounts if a.id == acc_id), None)
        if acc is None:
            return

        self.active_account_id = acc_id
        self.refresh_accounts_view()

        messagebox.showinfo(
            "切换账号",
            f"已在管理器中切换到账号: {acc.email}\n\n后续将基于此账号执行切号相关操作（例如配置切换或外部登录脚本）。",
        )

    # MCP / Rules 相关逻辑

    def refresh_mcp_view(self) -> None:
        if not hasattr(self, "tree_mcp"):
            return
        for item in self.tree_mcp.get_children():
            self.tree_mcp.delete(item)
        for server in self.mcp_servers:
            enabled_text = "是" if server.enabled else "否"
            self.tree_mcp.insert(
                "",
                tk.END,
                iid=server.id,
                values=(server.id, server.name, server.command, enabled_text),
            )

    def refresh_rules_view(self) -> None:
        if not hasattr(self, "tree_rules"):
            return
        for item in self.tree_rules.get_children():
            self.tree_rules.delete(item)
        for rule in self.rules:
            prompt_display = rule.prompt.replace("\n", " ")
            if len(prompt_display) > 60:
                prompt_display = prompt_display[:57] + "..."
            self.tree_rules.insert(
                "",
                tk.END,
                iid=rule.id,
                values=(rule.id, prompt_display),
            )

    def on_open_mcp_file(self) -> None:
        path_str = filedialog.askopenfilename(
            title="选择 MCP 配置 JSON",
            filetypes=(("JSON 文件", "*.json"), ("所有文件", "*.*")),
        )
        if not path_str:
            return
        path = Path(path_str)
        try:
            self.mcp_servers = mcp_rules.load_mcp_config(path)
            self.mcp_config_path = path
            self.refresh_mcp_view()
        except Exception as exc:
            messagebox.showerror("打开 MCP 文件失败", f"读取 MCP 配置失败: {exc}")

    def on_save_mcp_file(self) -> None:
        if self.mcp_config_path is None:
            path_str = filedialog.asksaveasfilename(
                title="保存 MCP 配置 JSON",
                defaultextension=".json",
                filetypes=(("JSON 文件", "*.json"), ("所有文件", "*.*")),
            )
            if not path_str:
                return
            self.mcp_config_path = Path(path_str)
        try:
            mcp_rules.save_mcp_config(self.mcp_config_path, self.mcp_servers)
        except Exception as exc:
            messagebox.showerror("保存 MCP 文件失败", f"写入 MCP 配置失败: {exc}")

    def on_backup_mcp(self) -> None:
        if not self.mcp_servers:
            if not messagebox.askyesno("备份 MCP", "当前 MCP 列表为空，仍要备份为空配置吗？"):
                return
        path_str = filedialog.asksaveasfilename(
            title="选择 MCP 备份文件保存路径",
            defaultextension=".json",
            filetypes=(("JSON 文件", "*.json"), ("所有文件", "*.*")),
        )
        if not path_str:
            return
        path = Path(path_str)
        try:
            mcp_rules.save_mcp_config(path, self.mcp_servers)
        except Exception as exc:
            messagebox.showerror("备份 MCP 失败", f"写入 MCP 备份失败: {exc}")

    def on_add_mcp(self) -> None:
        self._edit_mcp_server(None)

    def on_edit_mcp(self) -> None:
        selected = list(self.tree_mcp.selection())
        if not selected:
            messagebox.showinfo("编辑 MCP", "请先选择一个 MCP 配置。")
            return
        if len(selected) > 1:
            messagebox.showinfo("编辑 MCP", "一次仅支持编辑一个 MCP 配置。")
            return
        server = next((s for s in self.mcp_servers if s.id == selected[0]), None)
        if server is None:
            return
        self._edit_mcp_server(server)

    def on_tree_mcp_double_click(self, _event: tk.Event) -> None:  # type: ignore[override]
        item_id = self.tree_mcp.focus()
        if not item_id:
            return
        server = next((s for s in self.mcp_servers if s.id == item_id), None)
        if server is None:
            return
        self._edit_mcp_server(server)

    def _edit_mcp_server(self, server: Optional[McpServerConfig]) -> None:
        editing = server is not None

        win = tk.Toplevel(self.root)
        win.title("编辑 MCP" if editing else "新建 MCP")
        win.transient(self.root)
        win.grab_set()

        frm = ttk.Frame(win)
        frm.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        ttk.Label(frm, text="ID:").grid(row=0, column=0, sticky=tk.W, pady=4)
        id_var = tk.StringVar(value=server.id if editing else str(uuid4()))
        ent_id = ttk.Entry(frm, textvariable=id_var, width=40)
        ent_id.grid(row=0, column=1, sticky=tk.W, pady=4)

        ttk.Label(frm, text="名称:").grid(row=1, column=0, sticky=tk.W, pady=4)
        name_var = tk.StringVar(value=server.name if editing else "")
        ent_name = ttk.Entry(frm, textvariable=name_var, width=40)
        ent_name.grid(row=1, column=1, sticky=tk.W, pady=4)

        ttk.Label(frm, text="命令:").grid(row=2, column=0, sticky=tk.W, pady=4)
        command_var = tk.StringVar(value=server.command if editing else "")
        ent_command = ttk.Entry(frm, textvariable=command_var, width=40)
        ent_command.grid(row=2, column=1, sticky=tk.W, pady=4)

        ttk.Label(frm, text="参数(空格分隔):").grid(row=3, column=0, sticky=tk.W, pady=4)
        args_value = "" if not editing else " ".join(server.args)
        args_var = tk.StringVar(value=args_value)
        ent_args = ttk.Entry(frm, textvariable=args_var, width=40)
        ent_args.grid(row=3, column=1, sticky=tk.W, pady=4)

        ttk.Label(frm, text="环境变量(KEY=VALUE 每行一条):").grid(row=4, column=0, sticky=tk.NW, pady=4)
        txt_env = tk.Text(frm, width=40, height=5)
        if editing and server.env:
            lines = [f"{k}={v}" for k, v in server.env.items()]
            txt_env.insert("1.0", "\n".join(lines))
        txt_env.grid(row=4, column=1, sticky=tk.W, pady=4)

        enabled_var = tk.BooleanVar(value=server.enabled if editing else True)
        chk_enabled = ttk.Checkbutton(frm, text="启用", variable=enabled_var)
        chk_enabled.grid(row=5, column=1, sticky=tk.W, pady=(4, 0))

        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=(12, 0))

        def on_ok() -> None:
            id_val = id_var.get().strip()
            if not id_val:
                messagebox.showerror("保存 MCP", "ID 不能为空。")
                return
            name_val = name_var.get().strip()
            command_val = command_var.get().strip()
            args_str = args_var.get().strip()
            args_list = [a for a in args_str.split(" ") if a]

            env_text = txt_env.get("1.0", tk.END).strip()
            env_dict = {}
            if env_text:
                for line in env_text.splitlines():
                    line = line.strip()
                    if not line or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    env_dict[k.strip()] = v.strip()

            if editing and server is not None:
                server.id = id_val
                server.name = name_val
                server.command = command_val
                server.args = args_list
                server.env = env_dict
                server.enabled = enabled_var.get()
            else:
                new_server = McpServerConfig(
                    id=id_val,
                    name=name_val,
                    command=command_val,
                    args=args_list,
                    env=env_dict,
                    enabled=enabled_var.get(),
                )
                self.mcp_servers.append(new_server)

            self.refresh_mcp_view()
            win.destroy()

        def on_cancel() -> None:
            win.destroy()

        btn_ok = ttk.Button(btn_frame, text="保存", command=on_ok)
        btn_cancel = ttk.Button(btn_frame, text="取消", command=on_cancel)
        btn_ok.pack(side=tk.LEFT, padx=4)
        btn_cancel.pack(side=tk.LEFT, padx=4)

        win.bind("<Return>", lambda _e: on_ok())
        win.bind("<Escape>", lambda _e: on_cancel())

    def on_delete_mcp(self) -> None:
        selected = list(self.tree_mcp.selection())
        if not selected:
            return
        if not messagebox.askyesno("删除 MCP", f"确定要删除选中的 {len(selected)} 条 MCP 配置吗？"):
            return
        self.mcp_servers = [s for s in self.mcp_servers if s.id not in selected]
        self.refresh_mcp_view()

    def on_open_rules_file(self) -> None:
        path_str = filedialog.askopenfilename(
            title="选择 Rules 配置 JSON",
            filetypes=(("JSON 文件", "*.json"), ("所有文件", "*.*")),
        )
        if not path_str:
            return
        path = Path(path_str)
        try:
            self.rules = mcp_rules.load_rules(path)
            self.rules_config_path = path
            self.refresh_rules_view()
        except Exception as exc:
            messagebox.showerror("打开 Rules 文件失败", f"读取 Rules 配置失败: {exc}")

    def on_save_rules_file(self) -> None:
        if self.rules_config_path is None:
            path_str = filedialog.asksaveasfilename(
                title="保存 Rules 配置 JSON",
                defaultextension=".json",
                filetypes=(("JSON 文件", "*.json"), ("所有文件", "*.*")),
            )
            if not path_str:
                return
            self.rules_config_path = Path(path_str)
        try:
            mcp_rules.save_rules(self.rules_config_path, self.rules)
        except Exception as exc:
            messagebox.showerror("保存 Rules 文件失败", f"写入 Rules 配置失败: {exc}")

    def on_backup_rules(self) -> None:
        if not self.rules:
            if not messagebox.askyesno("备份 Rules", "当前 Rules 列表为空，仍要备份为空配置吗？"):
                return
        path_str = filedialog.asksaveasfilename(
            title="选择 Rules 备份文件保存路径",
            defaultextension=".json",
            filetypes=(("JSON 文件", "*.json"), ("所有文件", "*.*")),
        )
        if not path_str:
            return
        path = Path(path_str)
        try:
            mcp_rules.save_rules(path, self.rules)
        except Exception as exc:
            messagebox.showerror("备份 Rules 失败", f"写入 Rules 备份失败: {exc}")

    def on_add_rule(self) -> None:
        self._edit_rule(None)

    def on_edit_rule(self) -> None:
        selected = list(self.tree_rules.selection())
        if not selected:
            messagebox.showinfo("编辑 Rule", "请先选择一个 Rule。")
            return
        if len(selected) > 1:
            messagebox.showinfo("编辑 Rule", "一次仅支持编辑一个 Rule。")
            return
        rule = next((r for r in self.rules if r.id == selected[0]), None)
        if rule is None:
            return
        self._edit_rule(rule)

    def on_tree_rules_double_click(self, _event: tk.Event) -> None:  # type: ignore[override]
        item_id = self.tree_rules.focus()
        if not item_id:
            return
        rule = next((r for r in self.rules if r.id == item_id), None)
        if rule is None:
            return
        self._edit_rule(rule)

    def _edit_rule(self, rule: Optional[RuleConfig]) -> None:
        editing = rule is not None

        win = tk.Toplevel(self.root)
        win.title("编辑 Rule" if editing else "新建 Rule")
        win.transient(self.root)
        win.grab_set()

        frm = ttk.Frame(win)
        frm.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        ttk.Label(frm, text="ID:").grid(row=0, column=0, sticky=tk.W, pady=4)
        id_var = tk.StringVar(value=rule.id if editing else str(uuid4()))
        ent_id = ttk.Entry(frm, textvariable=id_var, width=40)
        ent_id.grid(row=0, column=1, sticky=tk.W, pady=4)

        ttk.Label(frm, text="提示词:").grid(row=1, column=0, sticky=tk.NW, pady=4)
        txt_prompt = tk.Text(frm, width=40, height=8)
        if editing and rule is not None:
            txt_prompt.insert("1.0", rule.prompt)
        txt_prompt.grid(row=1, column=1, sticky=tk.W, pady=4)

        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=(12, 0))

        def on_ok() -> None:
            id_val = id_var.get().strip()
            if not id_val:
                messagebox.showerror("保存 Rule", "ID 不能为空。")
                return
            prompt_val = txt_prompt.get("1.0", tk.END).rstrip("\n")

            if editing and rule is not None:
                rule.id = id_val
                rule.prompt = prompt_val
            else:
                new_rule = RuleConfig(id=id_val, prompt=prompt_val)
                self.rules.append(new_rule)

            self.refresh_rules_view()
            win.destroy()

        def on_cancel() -> None:
            win.destroy()

        btn_ok = ttk.Button(btn_frame, text="保存", command=on_ok)
        btn_cancel = ttk.Button(btn_frame, text="取消", command=on_cancel)
        btn_ok.pack(side=tk.LEFT, padx=4)
        btn_cancel.pack(side=tk.LEFT, padx=4)

        win.bind("<Return>", lambda _e: on_ok())
        win.bind("<Escape>", lambda _e: on_cancel())

    def on_delete_rules(self) -> None:
        selected = list(self.tree_rules.selection())
        if not selected:
            return
        if not messagebox.askyesno("删除 Rules", f"确定要删除选中的 {len(selected)} 条 Rules 吗？"):
            return
        self.rules = [r for r in self.rules if r.id not in selected]
        self.refresh_rules_view()


def run_app() -> None:
    root = tk.Tk()
    App(root)
    root.mainloop()
