# 项目上下文

## 目标

搭建一个实验控制项目，使当前电脑可以在局域网 `hku_ultracold` 中远程控制 Linux 工控机上的 ARTIQ，并准备 Moku:Go 的 API/驱动环境，方便后续采集、观测或协同控制。

## 当前网络拓扑

用户说明：Linux 工控机、当前电脑、ARTIQ 设备、Moku:Go 都通过路由器接入同一个局域网 `hku_ultracold`。

推荐逻辑关系：

```text
当前电脑
  |  hku_ultracold 局域网
  v
Linux 工控机，已安装 ARTIQ 驱动/环境
  |  hku_ultracold 局域网
  v
ARTIQ core device / Kasli / 相关量子控制硬件

Moku:Go 也接入 hku_ultracold，可由当前电脑或 Linux 工控机通过 Moku API 控制。
```

注意：即使所有设备在同一个局域网中，推荐仍让 Linux 工控机负责 ARTIQ 实验执行，因为 `@kernel` 实时序列在 ARTIQ core device 上执行，工控机只做 host/master 侧控制。

## 重要目录

- `Z:\Wang Junjie\Artiq_Project\remote`：ARTIQ 远程执行工具、示例实验和中文文档。
- `Z:\Wang Junjie\Artiq_Project\observer\moku`：Moku:Go API/驱动下载、安装说明和示例脚本。
- `C:\Users\ustcr\Documents\Codex\2026-06-30\linux-artiq-artiq`：本交接文档所在根目录。

## 已确认事实

- ARTIQ 可以通过 Linux 工控机远程执行；最稳妥方案是当前电脑 SSH/SCP 到工控机，由工控机调用 `artiq_run`。
- ARTIQ 管理系统方案也可用：工控机运行 `artiq_master`，当前电脑运行 `artiq_client` 或 `artiq_dashboard`。
- Moku:Go 有官方 Python API，PyPI 包名为 `moku`。
- 截至 2026-06-30，PyPI 最新 `moku` 版本为 `4.2.2.1`，发布时间为 2026-05-12，要求 Python >= 3.8。
- Liquid Instruments 官方说明中，MokuCLI 用于设备发现、文件传输、数据流等功能；Python API 使用前还需要下载 instrument definitions/bitstreams。

## 待用户补充

- Linux 工控机在 `hku_ultracold` 中的实际 IP 和 SSH 用户名。
- ARTIQ core device 的实际 IP，以及工控机 `device_db.py` 路径。
- Moku:Go 的实际 IP、序列号、MokuOS/FW 版本。
- 实验中 Moku:Go 需要扮演的角色：示波器、锁相放大器、波形发生器、频谱仪、数据记录仪，或只做旁路观测。
