# ARTIQ with AI 实验控制项目

本仓库用于记录和维护一个多 AI agent 接续开发的实验控制项目。目标是在 `hku_ultracold` 局域网中，让当前电脑、Linux 工控机、ARTIQ 设备和 Moku:Go 协同工作。

## 当前内容

- `remote/`：通过当前电脑远程调用 Linux 工控机上的 ARTIQ 环境，支持 SSH/SCP 执行 `artiq_run`，也预留 `artiq_master` / `artiq_client` 工作流。
- `observer/moku/`：Moku:Go 官方 Python API、MokuCLI 下载包、安装说明、检测脚本和只读示波器示例。
- `AGENTS.md`：后续 AI agent 的协作规范，说明怎么读上下文、怎么更新文档、怎么记录工作摘要。
- `PROJECT_CONTEXT.md`：项目背景、网络拓扑、重要路径和待确认信息。
- `PROJECT_LOG.md`：每轮工作摘要记录。

## 后续 agent 开始方式

进入仓库根目录后，先读：

1. `AGENTS.md`
2. `PROJECT_CONTEXT.md`
3. `PROJECT_LOG.md`
4. 当前任务相关子目录的 `README_中文.md`

用户以后可以直接说“在这个目录下继续”，后续 AI agent 应根据这些文档接续工作。

## 重要提醒

- 不要提交真实密码、token、私钥或用户本地真实配置文件。
- `config.local.json`、`moku_config.local.json` 只应保留在本机。
- 涉及 ARTIQ TTL、RF、激光、Moku 输出等硬件动作前，应先做 dry-run、只读查询或人工确认接线与电压范围。
