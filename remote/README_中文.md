# 通过以太网远程控制 Linux 工控机上的 ARTIQ

本目录提供一套小工具，用于在当前电脑上编写 ARTIQ 实验程序，然后通过以太网把程序交给 Linux 工控机执行。工控机负责连接 ARTIQ core device / Kasli / 控制硬件，并调用 `artiq_run` 或 `artiq_master` 完成真正的实验执行。

推荐先使用“SSH/SCP 方案”，因为它只要求当前电脑有 Python 和 SSH 客户端，不要求当前电脑安装完整 ARTIQ。

## 一、推荐网络结构

```text
当前电脑
  |
  | hku_ultracold 局域网
  |
  +-- Linux 工控机，已安装 ARTIQ
  +-- ARTIQ core device / Kasli / 控制硬件
  +-- Moku:Go
```

用户当前规划是：Linux 工控机、当前电脑、ARTIQ 设备和 Moku:Go 都通过路由器接入同一个 `hku_ultracold` 局域网。这种结构可以工作。ARTIQ 程序仍推荐由 Linux 工控机执行，因为工控机上已经装好 ARTIQ 环境，并且更适合作为 host/master。

如果以后追求更高稳定性，也可以让 Linux 工控机增加第二块网卡，一块连接实验室局域网，一块专门连接 ARTIQ core device。Moku:Go 可以继续留在实验室局域网，也可以根据触发/采集需求调整接线。

## 二、目录内容

```text
remote/
  remote_artiq.py          主程序
  config.example.json      配置模板
  run_core_reset.bat       Windows 一键运行最小测试实验
  examples/
    core_reset.py          最小实验：只复位 core device
    ttl_blink.py           TTL 闪烁示例，需要 device_db.py 中存在 ttl0
  docs/
    网络部署检查表.md
    故障排查.md
```

## 三、一次性准备

### 1. 当前电脑

需要：

- Python 3.9 或更新版本。
- OpenSSH 客户端，即命令行里能运行 `ssh` 和 `scp`。

在 Windows PowerShell 中检查：

```powershell
python --version
ssh -V
scp
```

如果 `ssh` 不存在，可以在 Windows 的“可选功能”中安装 OpenSSH Client。

### 2. Linux 工控机

需要：

- 已安装 ARTIQ。
- 能在工控机本机运行 `artiq_run`。
- 已配置好 `device_db.py`，其中 `core_addr` 指向 ARTIQ core device 的 IP。
- SSH 服务已开启，当前电脑能登录：

```powershell
ssh 用户名@工控机IP
```

进入工控机后建议先测试：

```bash
which artiq_run
artiq_run --version
ping ARTIQ_core_device_IP
```

### 3. IP 建议

如果所有设备都在 `hku_ultracold` 下，典型设置可以是：

```text
当前电脑 IP:       192.168.10.1
Linux 工控机 IP:  192.168.10.2
ARTIQ core IP:    192.168.1.75
Moku:Go IP:       192.168.10.100
```

上面的 IP 只是示例，请以路由器或设备界面显示的实际地址为准。当前电脑和工控机需要互相访问；工控机和 ARTIQ core device 需要互相访问。当前电脑不一定需要直接控制 ARTIQ core device，因为实际执行由工控机负责。

## 四、快速开始：SSH/SCP 方案

进入本目录：

```powershell
cd /d "Z:\Wang Junjie\Artiq_Project\remote"
```

复制配置模板：

```powershell
copy config.example.json config.local.json
notepad config.local.json
```

把里面的 `linux_host`、`linux_user` 改成你的工控机实际 IP 和用户名。例如：

```json
{
  "linux_host": "192.168.10.2",
  "linux_user": "artiq",
  "ssh_port": 22,
  "ssh_identity_file": "",
  "remote_project_dir": "~/artiq_remote_jobs",
  "remote_env_setup": "",
  "remote_artiq_run": "artiq_run",
  "artiq_master_host": "",
  "artiq_master_control_port": 3251,
  "artiq_master_notify_port": 3250,
  "local_artiq_client": "artiq_client",
  "local_artiq_dashboard": "artiq_dashboard"
}
```

检查本机工具和网络：

```powershell
python remote_artiq.py check --config config.local.json
```

通过 SSH 进一步检查工控机上的 ARTIQ 环境：

```powershell
python remote_artiq.py check --config config.local.json --deep
```

运行最小测试实验：

```powershell
python remote_artiq.py run --config config.local.json examples\core_reset.py
```

如果这个命令成功，说明完整链路已经通了：

```text
当前电脑 -> SSH/SCP -> Linux 工控机 -> artiq_run -> ARTIQ core device
```

## 五、运行自己的 ARTIQ 实验

把你的实验文件放在本目录或任意本机路径，然后执行：

```powershell
python remote_artiq.py run --config config.local.json path\to\your_experiment.py
```

如果一个文件里有多个实验类，需要指定类名，可以把参数透传给 `artiq_run`：

```powershell
python remote_artiq.py run --config config.local.json path\to\your_experiment.py -c YourExperimentClass
```

如果实验需要参数：

```powershell
python remote_artiq.py run --config config.local.json path\to\your_experiment.py -c YourExperimentClass frequency=10e6 repetitions=20
```

如果实验还依赖本地的辅助模块或目录，可以用 `--extra` 一起上传。注意 `--extra` 要写在实验文件前面：

```powershell
python remote_artiq.py run --config config.local.json --extra common_utils.py --extra drivers path\to\your_experiment.py -c YourExperimentClass
```

程序会在工控机上创建类似下面的目录：

```text
~/artiq_remote_jobs/20260630_010203_your_experiment/
```

然后把实验文件上传进去并执行：

```bash
artiq_run your_experiment.py ...
```

## 六、remote_env_setup 的用法

有些工控机只有在登录交互式 shell 后才有 `artiq_run`，但 SSH 非交互命令里找不到。这时需要在 `config.local.json` 中设置 `remote_env_setup`。

如果 ARTIQ 在 conda 环境中：

```json
"remote_env_setup": "source ~/miniconda3/etc/profile.d/conda.sh && conda activate artiq"
```

如果 ARTIQ 在虚拟环境中：

```json
"remote_env_setup": "source ~/artiq-venv/bin/activate"
```

如果你需要加载某个 profile：

```json
"remote_env_setup": "source ~/.bashrc"
```

修改后重新检查：

```powershell
python remote_artiq.py check --config config.local.json --deep
```

如果 `--deep` 能显示 `artiq_run --version`，说明远端环境已经正确加载。

## 七、可选方案：artiq_master / artiq_client

当你希望多人提交任务、排队执行、使用 dashboard 查看状态时，可以使用 ARTIQ 的管理系统模式：

```text
当前电脑上的 artiq_client / artiq_dashboard
  |
  | TCP，默认 control 端口 3251，notify 端口 3250
  v
Linux 工控机上的 artiq_master
  |
  v
ARTIQ core device
```

在工控机上启动 master，例如：

```bash
cd ~/artiq_project
artiq_master --bind 0.0.0.0
```

如果你的 `device_db.py` 或 repository 不在当前目录，请根据 `artiq_master --help` 指定对应参数。

当前电脑上如果已经安装了与工控机版本匹配的 ARTIQ 客户端，可以提交：

```powershell
python remote_artiq.py client-submit --config config.local.json examples\core_reset.py -c CoreReset
```

打开 dashboard：

```powershell
python remote_artiq.py dashboard --config config.local.json
```

这种方案的优点是更接近 ARTIQ 官方工作流，适合长期实验控制。缺点是当前电脑也需要安装 ARTIQ 客户端，而且版本最好与工控机一致。

## 八、常用命令汇总

生成配置：

```powershell
python remote_artiq.py init-config --output config.local.json
```

检查网络：

```powershell
python remote_artiq.py check --config config.local.json
```

检查远端 ARTIQ：

```powershell
python remote_artiq.py check --config config.local.json --deep
```

在工控机执行任意命令：

```powershell
python remote_artiq.py shell --config config.local.json "hostname && whoami && artiq_run --version"
```

运行最小实验：

```powershell
python remote_artiq.py run --config config.local.json examples\core_reset.py
```

运行 TTL 闪烁示例：

```powershell
python remote_artiq.py run --config config.local.json examples\ttl_blink.py -c TTLBlink count=5 pulse_ms=100
```

打印 dashboard 启动命令但不执行：

```powershell
python remote_artiq.py dashboard --config config.local.json --dry-run
```

## 九、安全建议

- 不要把 `artiq_master` 或 SSH 直接暴露到公网。
- 工控机建议只允许实验室内网访问。
- 优先使用 SSH 密钥登录，少用弱密码。
- 如果多人共用工控机，建议建立单独的实验用户，并限制写入目录。
- `config.local.json` 可能包含私有路径或密钥位置，已在 `.gitignore` 中排除。

## 十、官方文档入口

- ARTIQ 管理系统、`artiq_master`、`artiq_client`、`artiq_dashboard`：<https://m-labs.hk/artiq/manual/getting_started_mgmt.html>
- 网络和 `device_db.py` 配置：<https://m-labs.hk/artiq/manual/configuring.html>
- 默认网络端口：<https://m-labs.hk/artiq/manual/default_network_ports.html>
