# 后续 AI Agent 协作说明

本项目会由多个 AI agent 接续处理。用户希望以后只说“在这个目录下继续”，不再反复复制上下文。因此每个 agent 开始工作前必须先读本文件，并按本文件更新记录。

## 开始工作时先读

按顺序阅读：

1. `PROJECT_CONTEXT.md`：当前系统拓扑、目标、重要路径和约定。
2. `PROJECT_LOG.md`：最近的聊天/工作摘要，重点看最后几条。
3. 与任务相关的子目录文档：
   - `Z:\Wang Junjie\Artiq_Project\remote\README_中文.md`
   - `Z:\Wang Junjie\Artiq_Project\remote\docs\网络部署检查表.md`
   - `Z:\Wang Junjie\Artiq_Project\remote\docs\故障排查.md`
   - `Z:\Wang Junjie\Artiq_Project\observer\moku\README_中文.md`

如果文档和实际文件冲突，以实际文件和用户最新指令为准，并更新文档说明差异。

## 聊天记录怎么记

不要保存完整逐字聊天记录。每次较完整的工作回合结束前，在 `PROJECT_LOG.md` 追加一条摘要，格式如下：

```markdown
## YYYY-MM-DD HH:mm Agent 摘要

- 用户需求：
- 已完成：
- 修改/新增文件：
- 验证：
- 未完成/待确认：
- 重要注意：
```

记录要足够让下一个 agent 继续工作，但不要写密码、token、内网账号密码、私钥内容。IP、端口、设备名可以记录；如果用户明确要求保密，则用占位符。

## 文档怎么更新

每次改代码或配置模板后，必须同步检查相关中文文档：

- 持久事实、网络拓扑、目录路径、约定：更新 `PROJECT_CONTEXT.md`。
- 具体操作步骤：更新对应子目录的 `README_中文.md`。
- 常见问题和现场排障经验：更新对应 `docs\*.md`。
- 本轮做了什么、还有什么没做：追加到 `PROJECT_LOG.md`。

不要把临时命令输出大量粘进文档；只记录关键结果、命令和结论。

## 文件和配置约定

- 用户项目目录：`Z:\Wang Junjie\Artiq_Project`
- ARTIQ 远程控制目录：`Z:\Wang Junjie\Artiq_Project\remote`
- Moku:Go 观察/控制目录：`Z:\Wang Junjie\Artiq_Project\observer\moku`
- 当前 Codex 根目录：`C:\Users\ustcr\Documents\Codex\2026-06-30\linux-artiq-artiq`
- 不要覆盖 `config.local.json`、真实账号、真实 IP 配置，除非用户明确要求。
- 对包含空格的 Windows 路径，一律加引号。

## 当前技术方向

- ARTIQ：优先用当前电脑通过 SSH/SCP 把实验脚本传给 Linux 工控机，再由工控机运行 `artiq_run`。可选方案是工控机运行 `artiq_master`，当前电脑用 `artiq_client`/`artiq_dashboard` 提交。
- Moku:Go：使用 Liquid Instruments 官方 Python 包 `moku` 和 MokuCLI。Moku:Go 与当前电脑、Linux 工控机、ARTIQ 设备同在 `hku_ultracold` 局域网。

## 交接原则

- 先读文档，再动代码。
- 先保护用户已有文件，再新增或小范围修改。
- 任何真实硬件操作前，优先做 dry-run、连通性检查或只读查询。
- 涉及输出电压、TTL、激光、RF、触发等硬件动作时，在文档和脚本里明确提醒，不默认打开危险输出。
