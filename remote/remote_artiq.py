#!/usr/bin/env python3
"""
Remote ARTIQ helper.

This script lets a Windows/macOS/Linux workstation submit ARTIQ experiments to a
Linux industrial PC over Ethernet. It has two operating modes:

1. SSH/SCP mode: copy the experiment to the Linux PC and execute artiq_run there.
2. ARTIQ client mode: call local artiq_client and submit to a running artiq_master.

The SSH/SCP mode only needs Python 3 and OpenSSH client tools on this computer.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import shlex
import shutil
import socket
import subprocess
import sys
from typing import Any


DEFAULT_CONFIG: dict[str, Any] = {
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
    "local_artiq_dashboard": "artiq_dashboard",
}


def die(message: str, code: int = 2) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def info(message: str) -> None:
    print(message, flush=True)


def load_config(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        die(f"配置文件不存在: {path}\n请先复制 config.example.json 为 config.local.json 并修改。")

    with path.open("r", encoding="utf-8") as f:
        user_config = json.load(f)

    config = dict(DEFAULT_CONFIG)
    config.update(user_config)

    if not config["linux_host"]:
        die("配置项 linux_host 不能为空。")
    if not config["linux_user"]:
        die("配置项 linux_user 不能为空。")
    if not config["artiq_master_host"]:
        config["artiq_master_host"] = config["linux_host"]
    return config


def write_config(path: pathlib.Path, force: bool) -> None:
    if path.exists() and not force:
        die(f"文件已存在: {path}\n如需覆盖，请加 --force。")
    path.write_text(
        json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    info(f"已写入配置模板: {path}")


def expand_local_path(value: str) -> str:
    if not value:
        return value
    return str(pathlib.Path(value).expanduser())


def require_tool(name: str, description: str) -> str | None:
    found = shutil.which(name)
    if found:
        info(f"[OK] {description}: {found}")
    else:
        info(f"[MISSING] {description}: 未找到命令 {name}")
    return found


def tcp_probe(host: str, port: int, timeout: float = 3.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def ssh_base(config: dict[str, Any]) -> list[str]:
    cmd = [
        "ssh",
        "-p",
        str(config["ssh_port"]),
        "-o",
        "ConnectTimeout=8",
    ]
    identity = expand_local_path(str(config.get("ssh_identity_file", "")))
    if identity:
        cmd.extend(["-i", identity])
    return cmd


def scp_base(config: dict[str, Any]) -> list[str]:
    cmd = [
        "scp",
        "-P",
        str(config["ssh_port"]),
        "-o",
        "ConnectTimeout=8",
    ]
    identity = expand_local_path(str(config.get("ssh_identity_file", "")))
    if identity:
        cmd.extend(["-i", identity])
    return cmd


def remote_login(config: dict[str, Any]) -> str:
    return f"{config['linux_user']}@{config['linux_host']}"


def bash_wrap(script: str) -> str:
    return "bash -lc " + shlex.quote(script)


def remote_script(config: dict[str, Any], commands: list[str]) -> str:
    lines = ["set -euo pipefail"]
    env_setup = str(config.get("remote_env_setup", "")).strip()
    if env_setup:
        lines.append(env_setup)
    lines.extend(commands)
    return "\n".join(lines)


def run_command(command: list[str], dry_run: bool = False) -> int:
    info("+ " + " ".join(shlex.quote(part) for part in command))
    if dry_run:
        return 0
    return subprocess.call(command)


def capture_command(command: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        command,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return proc.returncode, proc.stdout


def ssh_command(config: dict[str, Any], script: str) -> list[str]:
    return ssh_base(config) + [remote_login(config), bash_wrap(script)]


def sanitize_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("._")
    return cleaned[:80] or "experiment"


def remote_join(base: str, *parts: str) -> str:
    result = base.rstrip("/")
    for part in parts:
        result += "/" + part.strip("/")
    return result


def remote_path_arg(path: str) -> str:
    """Quote a remote path for bash while preserving leading ~/ expansion."""
    if path == "~":
        return '"$HOME"'
    if path.startswith("~/"):
        rest = path[2:]
        return '"$HOME"/' + shlex.quote(rest)
    return shlex.quote(path)


def make_job_dir(config: dict[str, Any], experiment: pathlib.Path) -> str:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = sanitize_name(experiment.stem)
    return remote_join(str(config["remote_project_dir"]), f"{stamp}_{stem}")


def sanitize_file_name(name: str) -> str:
    path = pathlib.PurePath(name)
    suffix = path.suffix if re.fullmatch(r"\.[A-Za-z0-9_.-]+", path.suffix) else ""
    return sanitize_name(path.stem) + suffix


def scp_to(
    config: dict[str, Any],
    local_path: pathlib.Path,
    remote_dir: str,
    remote_name: str | None = None,
) -> int:
    flags = ["-r"] if local_path.is_dir() else []
    target_name = remote_name or local_path.name
    target = f"{remote_login(config)}:{remote_join(remote_dir, target_name)}"
    return run_command(scp_base(config) + flags + [str(local_path), target])


def cmd_init_config(args: argparse.Namespace) -> int:
    write_config(args.output, args.force)
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    config = load_config(args.config)

    info("== 本机工具检查 ==")
    require_tool("ssh", "OpenSSH SSH 客户端")
    require_tool("scp", "OpenSSH SCP 客户端")
    require_tool(str(config["local_artiq_client"]), "本机 artiq_client，可选")
    require_tool(str(config["local_artiq_dashboard"]), "本机 artiq_dashboard，可选")

    info("\n== 网络端口检查 ==")
    ssh_ok = tcp_probe(str(config["linux_host"]), int(config["ssh_port"]))
    info(f"[{'OK' if ssh_ok else 'FAIL'}] SSH {config['linux_host']}:{config['ssh_port']}")

    master_host = str(config["artiq_master_host"])
    for label, port in [
        ("ARTIQ master control", int(config["artiq_master_control_port"])),
        ("ARTIQ master notify", int(config["artiq_master_notify_port"])),
    ]:
        ok = tcp_probe(master_host, port, timeout=2.0)
        info(f"[{'OK' if ok else 'WARN'}] {label} {master_host}:{port}")

    if args.deep:
        info("\n== 远端 ARTIQ 环境检查 ==")
        script = remote_script(
            config,
            [
                "echo HOST=$(hostname)",
                "echo USER=$(whoami)",
                "command -v artiq_run || true",
                "artiq_run --version || true",
                "command -v artiq_client || true",
                "command -v artiq_master || true",
            ],
        )
        code, output = capture_command(ssh_command(config, script))
        print(output, end="")
        if code != 0:
            info(f"[WARN] 远端检查命令返回码: {code}")

    return 0


def cmd_shell(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    script = remote_script(config, [args.command])
    return run_command(ssh_command(config, script), dry_run=args.dry_run)


def cmd_run(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    experiment = args.experiment.resolve()
    if not experiment.exists():
        die(f"实验文件不存在: {experiment}")
    if not experiment.is_file():
        die(f"实验路径不是文件: {experiment}")

    job_dir = make_job_dir(config, experiment)
    remote_file_name = sanitize_file_name(experiment.name)
    remote_file = remote_join(job_dir, remote_file_name)

    info("== 创建远端任务目录 ==")
    mkdir_script = remote_script(config, [f"mkdir -p {remote_path_arg(job_dir)}"])
    code = run_command(ssh_command(config, mkdir_script), dry_run=args.dry_run)
    if code != 0:
        return code

    info("\n== 上传实验文件 ==")
    if not args.dry_run:
        code = scp_to(config, experiment, job_dir, remote_file_name)
        if code != 0:
            return code
        for extra in args.extra:
            extra_path = extra.resolve()
            if not extra_path.exists():
                die(f"额外上传路径不存在: {extra_path}")
            code = scp_to(config, extra_path, job_dir)
            if code != 0:
                return code
    else:
        info(f"[dry-run] 跳过上传: {experiment} -> {remote_file}")

    info("\n== 在 Linux 工控机上运行 artiq_run ==")
    artiq_args = " ".join(shlex.quote(item) for item in args.artiq_args)
    run_script = remote_script(
        config,
        [
            f"cd {remote_path_arg(job_dir)}",
            f"{config['remote_artiq_run']} {shlex.quote(remote_file_name)} {artiq_args}".rstrip(),
        ],
    )
    return run_command(ssh_command(config, run_script), dry_run=args.dry_run)


def cmd_client_submit(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    experiment = args.experiment.resolve()
    if not experiment.exists():
        die(f"实验文件不存在: {experiment}")

    command = [
        str(config["local_artiq_client"]),
        "-s",
        str(config["artiq_master_host"]),
    ]
    control_port = int(config["artiq_master_control_port"])
    if control_port != 3251:
        command.extend(["--port", str(control_port)])
    command.extend(["submit", "--content"])
    if args.class_name:
        command.extend(["-c", args.class_name])
    if args.pipeline:
        command.extend(["-p", args.pipeline])
    if args.priority is not None:
        command.extend(["-P", str(args.priority)])
    if args.flush:
        command.append("-f")
    command.append(str(experiment))
    command.extend(args.artiq_args)
    return run_command(command, dry_run=args.dry_run)


def cmd_dashboard(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    command = [
        str(config["local_artiq_dashboard"]),
        "-s",
        str(config["artiq_master_host"]),
    ]
    control_port = int(config["artiq_master_control_port"])
    notify_port = int(config["artiq_master_notify_port"])
    if control_port != 3251:
        command.extend(["--port-control", str(control_port)])
    if notify_port != 3250:
        command.extend(["--port-notify", str(notify_port)])
    return run_command(command, dry_run=args.dry_run)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="通过 SSH/SCP 或 artiq_client 远程控制 Linux 工控机上的 ARTIQ。",
    )
    parser.add_argument(
        "--config",
        type=pathlib.Path,
        default=pathlib.Path("config.local.json"),
        help="配置文件路径，默认 config.local.json。",
    )

    def add_config_arg(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument(
            "--config",
            type=pathlib.Path,
            default=argparse.SUPPRESS,
            help="配置文件路径，默认 config.local.json。可放在子命令前或后。",
        )

    sub = parser.add_subparsers(dest="command_name", required=True)

    p = sub.add_parser("init-config", help="生成一份配置模板。")
    p.add_argument("--output", type=pathlib.Path, default=pathlib.Path("config.local.json"))
    p.add_argument("--force", action="store_true", help="覆盖已有文件。")
    p.set_defaults(func=cmd_init_config)

    p = sub.add_parser("check", help="检查本机工具、网络端口和可选的远端 ARTIQ 环境。")
    add_config_arg(p)
    p.add_argument("--deep", action="store_true", help="通过 SSH 检查远端 artiq_run/artiq_master。")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("shell", help="在 Linux 工控机上执行一条命令。")
    add_config_arg(p)
    p.add_argument("command", help="要在远端 bash 中执行的命令。")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_shell)

    p = sub.add_parser("run", help="上传一个实验文件，并在 Linux 工控机上执行 artiq_run。")
    add_config_arg(p)
    p.add_argument("experiment", type=pathlib.Path, help="本机实验 Python 文件。")
    p.add_argument("--extra", type=pathlib.Path, action="append", default=[], help="额外上传的文件或目录，可重复。")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("artiq_args", nargs=argparse.REMAINDER, help="透传给 artiq_run 的参数，例如 -c ClassName 或 key=value。")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("client-submit", help="用本机 artiq_client 提交到已经运行的 artiq_master。")
    add_config_arg(p)
    p.add_argument("experiment", type=pathlib.Path, help="本机实验 Python 文件。")
    p.add_argument("-c", "--class-name", help="实验类名。")
    p.add_argument("-p", "--pipeline", help="pipeline 名称，默认由 ARTIQ 决定。")
    p.add_argument("-P", "--priority", type=int, help="提交优先级，数值越大越优先。")
    p.add_argument("-f", "--flush", action="store_true", help="提交前清空 pipeline。")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("artiq_args", nargs=argparse.REMAINDER, help="透传给实验的参数，例如 key=value。")
    p.set_defaults(func=cmd_client_submit)

    p = sub.add_parser("dashboard", help="打开连接到远端 artiq_master 的 artiq_dashboard。")
    add_config_arg(p)
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_dashboard)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
