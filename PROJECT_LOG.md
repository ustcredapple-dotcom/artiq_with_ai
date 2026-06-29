# 项目工作记录

本文件只记录摘要，不保存完整聊天记录。后续 AI agent 每次完成一轮较完整工作后，请在顶部下方追加新的日期小节。

## 2026-06-30 01:15 Codex 摘要

- 用户需求：把当前工作完成后上传到 GitHub 仓库 `ustcredapple-dotcom/artiq_with_ai`。
- 已完成：新增仓库根 README，准备将根交接文档、`remote/`、`observer/moku/` 同步到 GitHub 仓库。
- 修改/新增文件：根目录 `README_中文.md`，并更新本日志。
- 验证：上传前会在临时 clone 中检查 `git status`、提交并尝试 push。
- 未完成/待确认：真实 GitHub push 是否成功取决于当前环境是否已有该仓库写权限/凭据。
- 重要注意：不要提交本地真实配置文件或凭据。

## 2026-06-30 01:00 Codex 摘要

- 用户需求：确认是否能通过当前电脑以太网连接 Linux 工控机，再由工控机控制 ARTIQ；随后要求把程序和详细中文文档写到 `Z:\Wang Junjie\Artiq_Project\remote`。用户补充网络拓扑为当前电脑、Linux 工控机、ARTIQ 设备、Moku:Go 都在 `hku_ultracold` 局域网，并要求下载 Moku:Go/API 驱动到 `Z:\Wang Junjie\Artiq_Project\observer\moku`。最后要求根目录增加给后续 AI agent 的交接文档。
- 已完成：创建 ARTIQ 远程控制脚本、配置模板、示例实验、中文 README、网络检查表、故障排查文档；确认 Moku:Go 官方 Python API 包名为 `moku`，下载 `moku==4.2.2.1` wheel、依赖 wheel、`moku` 源码包，以及 MokuCLI Windows/Linux 安装包；创建 Moku 中文 README、配置模板、检测脚本和示波器只读示例；创建本交接文档。
- 修改/新增文件：见 `Z:\Wang Junjie\Artiq_Project\remote`、`Z:\Wang Junjie\Artiq_Project\observer\moku`、根目录 `AGENTS.md`、`PROJECT_CONTEXT.md`、`PROJECT_LOG.md`。Moku 下载清单在 `Z:\Wang Junjie\Artiq_Project\observer\moku\DOWNLOAD_MANIFEST.txt`。
- 验证：`remote_artiq.py`、`moku_tools.py` 和示例脚本已通过 `python -m py_compile`；`remote_artiq.py run --dry-run` 能生成正确 SSH/SCP/artiq_run 命令；`moku_tools.py --help` 和 `scope-read --dry-run` 正常；JSON 模板可解析；Moku 包和 MokuCLI 安装包已下载并生成 SHA256 清单。
- 未完成/待确认：真实工控机 IP、SSH 用户名、ARTIQ core IP、Moku:Go IP/FW 版本未知，因此尚未做真实硬件连通性测试。
- 重要注意：不要覆盖用户未来填写的 `config.local.json`；真实输出硬件动作前先做只读查询或 dry-run。
