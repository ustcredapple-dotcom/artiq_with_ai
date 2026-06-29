#!/usr/bin/env python3
"""Small helper for Liquid Instruments Moku:Go on the lab LAN."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import pathlib
import platform
import shutil
import subprocess
import sys
from typing import Any


DEFAULT_CONFIG: dict[str, Any] = {
    "moku_ip": "192.168.10.100",
    "moku_serial": "",
    "moku_os_version": "",
    "force_connect": False,
    "timebase_start_s": -0.001,
    "timebase_end_s": 0.001,
}


def die(message: str, code: int = 2) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def info(message: str) -> None:
    print(message, flush=True)


def load_config(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        die(f"配置文件不存在: {path}\n请复制 moku_config.example.json 为 moku_config.local.json 并修改。")
    with path.open("r", encoding="utf-8") as f:
        user_config = json.load(f)
    config = dict(DEFAULT_CONFIG)
    config.update(user_config)
    return config


def write_config(path: pathlib.Path, force: bool) -> int:
    if path.exists() and not force:
        die(f"文件已存在: {path}\n如需覆盖，请加 --force。")
    path.write_text(json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    info(f"已写入配置模板: {path}")
    return 0


def run_command(command: list[str], dry_run: bool = False) -> int:
    quoted = " ".join(command)
    info("+ " + quoted)
    if dry_run:
        return 0
    return subprocess.call(command)


def capture_command(command: list[str], timeout: int = 20) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            command,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
        return proc.returncode, proc.stdout
    except FileNotFoundError:
        return 127, f"command not found: {command[0]}\n"
    except subprocess.TimeoutExpired as exc:
        return 124, (exc.stdout or "") + f"\ncommand timed out after {timeout}s\n"


def installed_version(package: str) -> str | None:
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return None


def ping_host(host: str) -> bool:
    if not host:
        return False
    if platform.system().lower().startswith("win"):
        command = ["ping", "-n", "1", "-w", "1000", host]
    else:
        command = ["ping", "-c", "1", "-W", "1", host]
    code, output = capture_command(command, timeout=5)
    print(output, end="")
    return code == 0


def cmd_init_config(args: argparse.Namespace) -> int:
    return write_config(args.output, args.force)


def cmd_check(args: argparse.Namespace) -> int:
    config = load_config(args.config)

    info("== Python API 检查 ==")
    info(f"Python: {sys.version.split()[0]} ({sys.executable})")
    moku_version = installed_version("moku")
    if moku_version:
        info(f"[OK] moku Python 包: {moku_version}")
    else:
        info("[MISSING] moku Python 包未安装。可运行 install_from_downloads.bat 或 pip install -r requirements.txt")

    info("\n== 命令行工具检查 ==")
    for tool in ["moku", "mokucli"]:
        path = shutil.which(tool)
        if path:
            info(f"[OK] {tool}: {path}")
        else:
            info(f"[MISSING] {tool}: 未在 PATH 中找到")

    moku_ip = str(config.get("moku_ip", "")).strip()
    if moku_ip:
        info(f"\n== Moku:Go IP 连通性检查: {moku_ip} ==")
        ok = ping_host(moku_ip)
        info(f"[{'OK' if ok else 'WARN'}] ping {moku_ip}")

    info("\n== mokucli 设备发现 ==")
    code, output = capture_command(["mokucli", "list"], timeout=20)
    print(output, end="")
    if code != 0:
        info(f"[WARN] mokucli list 返回码: {code}")
    return 0


def cmd_discover(args: argparse.Namespace) -> int:
    return run_command(["mokucli", "list"], dry_run=args.dry_run)


def cmd_download_instruments(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    os_version = args.os_version or str(config.get("moku_os_version", "")).strip()
    if not os_version:
        die("请在 moku_config.local.json 中填写 moku_os_version，或使用 --os-version 指定。")
    return run_command(["moku", "download", "--os-ver", os_version], dry_run=args.dry_run)


def connect_oscilloscope(config: dict[str, Any]):
    from moku.instruments import Oscilloscope

    force_connect = bool(config.get("force_connect", False))
    moku_ip = str(config.get("moku_ip", "")).strip()
    serial = str(config.get("moku_serial", "")).strip()
    if moku_ip:
        return Oscilloscope(moku_ip, force_connect=force_connect)
    if serial:
        return Oscilloscope(serial=int(serial), force_connect=force_connect)
    die("请在配置中填写 moku_ip 或 moku_serial。")


def cmd_scope_read(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    if args.dry_run:
        info("[dry-run] 将连接 Moku:Go，部署 Oscilloscope，设置 timebase，并读取一帧数据。")
        return 0

    instrument = connect_oscilloscope(config)
    try:
        start = float(config.get("timebase_start_s", -0.001))
        end = float(config.get("timebase_end_s", 0.001))
        instrument.set_timebase(start, end)
        data = instrument.get_data()
        keys = sorted(data.keys())
        info(f"数据字段: {keys}")
        for key in keys:
            value = data[key]
            try:
                info(f"{key}: {len(value)} points")
            except TypeError:
                info(f"{key}: {value}")
        return 0
    finally:
        try:
            instrument.relinquish_ownership()
        except Exception as exc:
            info(f"[WARN] relinquish_ownership 失败: {exc}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Moku:Go 安装检查、发现和只读示波器测试工具。")
    parser.add_argument(
        "--config",
        type=pathlib.Path,
        default=pathlib.Path("moku_config.local.json"),
        help="配置文件路径，默认 moku_config.local.json。",
    )

    def add_config_arg(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument(
            "--config",
            type=pathlib.Path,
            default=argparse.SUPPRESS,
            help="配置文件路径，默认 moku_config.local.json。可放在子命令前或后。",
        )

    sub = parser.add_subparsers(dest="command_name", required=True)

    p = sub.add_parser("init-config", help="生成配置模板。")
    p.add_argument("--output", type=pathlib.Path, default=pathlib.Path("moku_config.local.json"))
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_init_config)

    p = sub.add_parser("check", help="检查 Python 包、MokuCLI 和局域网设备发现。")
    add_config_arg(p)
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("discover", help="调用 mokucli list 发现局域网 Moku 设备。")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_discover)

    p = sub.add_parser("download-instruments", help="下载当前 MokuOS 对应的 instrument definitions。")
    add_config_arg(p)
    p.add_argument("--os-version", help="MokuOS 版本，例如 4.2.2。")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_download_instruments)

    p = sub.add_parser("scope-read", help="部署 Oscilloscope 并读取一帧输入数据，不打开输出。")
    add_config_arg(p)
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_scope_read)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
