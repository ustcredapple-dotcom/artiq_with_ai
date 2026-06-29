# Moku:Go API/驱动下载与使用说明

结论：**Moku:Go 有官方 API 功能**。Liquid Instruments 官方 Python 包名是 `moku`，用于对 Moku:Go 等 Moku 设备进行 command、control 和 monitoring。官方还提供 `mokucli` 工具，用于局域网设备发现、数据流和相关文件操作。

本目录已经下载好官方 Python API 包和 MokuCLI 安装包，方便后续在当前电脑或 Linux 工控机上安装。

## 一、当前目录内容

```text
observer/moku/
  README_中文.md
  moku_config.example.json
  moku_tools.py
  requirements.txt
  install_from_downloads.bat
  install_from_downloads_linux.sh
  packages/
    moku-4.2.2.1-py3-none-any.whl
    以及 Windows Python 3.11 下的依赖 wheel
  packages_source/
    moku-4.2.2.1.tar.gz
  installers/
    mokucli-windows.exe
    mokucli-linux.tar.gz
  examples/
    oscilloscope_snapshot.py
```

已下载版本：

- `moku==4.2.2.1`
- MokuCLI Windows installer
- MokuCLI Linux tar.gz

注意：`packages/` 中的部分依赖 wheel 是当前电脑下载的 Windows CPython 3.11 版本。如果换成 Linux 或不同 Python 版本，优先使用在线安装：

```bash
python -m pip install --upgrade moku
```

如果必须离线安装，需要为目标系统和 Python 版本重新下载对应 wheel。

## 二、官方资料

- Moku API 文档：<https://apis.liquidinstruments.com/api/>
- Python getting started：<https://apis.liquidinstruments.com/api/getting-started/starting-python.html>
- PyPI `moku` 包：<https://pypi.org/project/moku/>
- Moku Utilities / MokuCLI 下载页：<https://liquidinstruments.com/software/utilities/>

从 `moku` 包元数据可见，该包支持 `Moku:Go`，并提供如下 instrument 类：

- `Oscilloscope`
- `WaveformGenerator`
- `LockInAmp`
- `SpectrumAnalyzer`
- `Datalogger`
- `Phasemeter`
- `PIDController`
- `FrequencyResponseAnalyzer`
- `ArbitraryWaveformGenerator`
- 以及其他 Moku instrument

## 三、网络拓扑

用户说明：当前电脑、Linux 工控机、ARTIQ 设备、Moku:Go 都通过路由器接入同一个局域网 `hku_ultracold`。

```text
当前电脑
  |
  | hku_ultracold
  |
  +-- Linux 工控机，运行 ARTIQ host/master
  +-- ARTIQ core device
  +-- Moku:Go
```

Moku:Go 可以由当前电脑直接控制，也可以由 Linux 工控机控制。若要和 ARTIQ 实验同步，后续可以把 Moku 控制脚本放到工控机上，由 ARTIQ host 侧 Python 逻辑调用；但要注意 Moku API 网络调用不是 ARTIQ RTIO 实时序列的一部分。

## 四、Windows 当前电脑安装

进入本目录：

```powershell
cd /d "Z:\Wang Junjie\Artiq_Project\observer\moku"
```

安装 MokuCLI：

```powershell
.\installers\mokucli-windows.exe
```

安装 Python API。若当前电脑 Python 是 3.11，可尝试离线安装：

```powershell
.\install_from_downloads.bat
```

如果离线安装失败，说明 Python 版本或系统架构与已下载 wheel 不匹配，改用在线安装：

```powershell
python -m pip install --upgrade moku
```

检查安装：

```powershell
python moku_tools.py check --config moku_config.example.json
```

## 五、Linux 工控机安装

把 `observer/moku` 目录拷贝到工控机后：

```bash
cd observer/moku
mkdir -p ~/bin/mokucli
tar -xzf installers/mokucli-linux.tar.gz -C ~/bin/mokucli
export PATH="$HOME/bin/mokucli:$PATH"
mokucli list
```

安装 Python API，优先在线安装：

```bash
python3 -m pip install --upgrade moku
```

如果需要尝试离线安装：

```bash
bash install_from_downloads_linux.sh
```

如果离线安装失败，通常是 `packages/` 中依赖 wheel 不是 Linux 版本，需要在有网络的机器上为 Linux/Python 版本重新下载。

## 六、配置 Moku:Go

复制配置：

```powershell
copy moku_config.example.json moku_config.local.json
notepad moku_config.local.json
```

填写实际 IP，例如：

```json
{
  "moku_ip": "192.168.10.100",
  "moku_serial": "",
  "moku_os_version": "4.2.2",
  "force_connect": false,
  "timebase_start_s": -0.001,
  "timebase_end_s": 0.001
}
```

字段说明：

- `moku_ip`：Moku:Go 在 `hku_ultracold` 局域网中的 IP。
- `moku_serial`：可选，使用序列号连接时填写。
- `moku_os_version`：MokuOS/FW 版本，用于 `moku download --os-ver` 下载 instrument definitions。
- `force_connect`：如果设备被其他客户端占用，是否强制接管。默认 `false` 更安全。
- `timebase_start_s` / `timebase_end_s`：示波器只读测试的时间窗口。

## 七、发现设备

安装 MokuCLI 后：

```powershell
mokucli list
```

或用本目录脚本：

```powershell
python moku_tools.py discover
```

完整检查：

```powershell
python moku_tools.py check --config moku_config.local.json
```

如果发现不了设备，检查：

- Moku:Go 是否连接到 `hku_ultracold`。
- 当前电脑是否也在同一局域网。
- 防火墙是否阻止局域网发现广播。
- Moku:Go 是否已经被其他电脑占用。

## 八、下载 instrument definitions

官方 Python 包说明中，Python API 使用前需要通过 `moku` 命令下载对应 MokuOS 版本的 instrument definitions：

```powershell
python moku_tools.py download-instruments --config moku_config.local.json
```

或直接指定版本：

```powershell
python moku_tools.py download-instruments --os-version 4.2.2
```

这里的版本应该和 Moku:Go 实际 MokuOS/FW 版本匹配。可以从 Moku App 或 `mokucli list` 输出中确认。

## 九、只读示波器测试

确认 Moku:Go 输入端接线安全后，执行：

```powershell
python moku_tools.py scope-read --config moku_config.local.json
```

这个命令会：

1. 连接 Moku:Go。
2. 部署 `Oscilloscope` instrument。
3. 设置 timebase。
4. 读取一帧输入数据。
5. 释放设备 ownership。

它不会打开输出信号。

若只想看将要做什么，不连接设备：

```powershell
python moku_tools.py scope-read --config moku_config.local.json --dry-run
```

## 十、最小 Python 示例

`examples/oscilloscope_snapshot.py` 是官方风格的最小示例。使用前把里面的 `MOKU_IP` 改成实际 IP：

```python
from moku.instruments import Oscilloscope

instrument = Oscilloscope("192.168.10.100", force_connect=False)
try:
    instrument.set_timebase(-0.001, 0.001)
    data = instrument.get_data()
    print(data["ch1"], data["ch2"], data["time"])
finally:
    instrument.relinquish_ownership()
```

## 十一、和 ARTIQ 配合时的注意点

- ARTIQ 的硬实时序列由 core device 执行；Moku API 是普通网络控制，不属于 RTIO 硬实时链路。
- 如果只需要 Moku:Go 采集慢速监测数据，可以让当前电脑直接运行 Moku Python 脚本。
- 如果需要 ARTIQ 实验开始前/结束后配置 Moku，可以把 Moku 控制放在 ARTIQ host 侧 Python 逻辑中，而不是 `@kernel` 里。
- 如果需要精确同步，应优先使用硬件触发线，例如 ARTIQ TTL 输出触发 Moku:Go 输入触发，再用 Moku 采集数据。

## 十二、安全提醒

- 不要在未确认接线、电压范围、50 ohm/1 Mohm 设置前运行波形输出脚本。
- 当前提供的脚本只做发现设备和示波器输入读取，不默认开启输出。
- 如果设备正在被其他实验占用，不要随意设置 `force_connect=true`。
