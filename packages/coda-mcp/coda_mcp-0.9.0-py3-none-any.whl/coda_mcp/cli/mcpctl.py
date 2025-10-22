"""Local MCP server manager CLI."""
from __future__ import annotations

import argparse
import json
import os
import stat
import sys
import textwrap
import time
from pathlib import Path
from typing import Any

from .configure_clients import configure_claude, configure_cursor

try:  # optional dependency for YAML overlays
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


def default_overlay_path() -> Path | None:
    candidate = Path("mcp.yml")
    return candidate if candidate.exists() else None


def load_overlay(path: Path | None) -> dict[str, Any] | None:
    if not path:
        return None
    try:
        text = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except Exception:
        pass
    if yaml is None:  # pragma: no cover - optional dependency missing
        print(f"Warning: PyYAML not installed, cannot parse overlay '{path}'", file=sys.stderr)
        return None
    try:
        data = yaml.safe_load(text)
        return data if isinstance(data, dict) else None
    except Exception as exc:  # pragma: no cover
        print(f"Warning: failed to parse overlay '{path}': {exc}", file=sys.stderr)
        return None


def format_overlay(data: dict[str, Any]) -> list[str]:
    output: list[str] = []
    tasks = data.get("tasks")
    prompts = data.get("prompts")
    resources = data.get("resources")
    if tasks:
        output.append("")
        output.append("Tasks")
        for item in tasks:
            if isinstance(item, dict):
                name = item.get("name") or item.get("title") or "Task"
                description = item.get("description")
                line = f"- {name}"
                if description:
                    line += f": {description}"
                output.append(line)
            else:
                output.append(f"- {item}")
    if prompts:
        output.append("")
        output.append("Prompts")
        for prompt in prompts:
            if isinstance(prompt, dict):
                pid = prompt.get("id") or prompt.get("name") or "prompt"
                description = prompt.get("description")
                line = f"- {pid}"
                if description:
                    line += f": {description}"
                output.append(line)
            else:
                output.append(f"- {prompt}")
    if resources:
        output.append("")
        output.append("Resources")
        for resource in resources:
            if isinstance(resource, dict):
                rid = resource.get("uri") or resource.get("name") or "resource"
                description = resource.get("description")
                line = f"- {rid}"
                if description:
                    line += f": {description}"
                output.append(line)
            else:
                output.append(f"- {resource}")
    return output


def generate_plist(payload: dict[str, Any]) -> str:
    def format_value(value: Any, indent: int = 2) -> str:
        space = " " * indent
        if isinstance(value, dict):
            items = [f"{space}<key>{k}</key>\n{format_value(v, indent + 2)}" for k, v in value.items()]
            return f"{space}<dict>\n" + "\n".join(items) + f"\n{space}</dict>"
        if isinstance(value, list):
            items = [format_value(v, indent + 2) for v in value]
            return f"{space}<array>\n" + "\n".join(items) + f"\n{space}</array>"
        if isinstance(value, bool):
            return f"{space}<{'true' if value else 'false'}/>"
        return f"{space}<string>{value}</string>"

    items = []
    for key, val in payload.items():
        items.append(f"  <key>{key}</key>\n{format_value(val, 2)}")
    body = "\n".join(items)
    return textwrap.dedent(
        f"""\
        <?xml version=\"1.0\" encoding=\"UTF-8\"?>
        <!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">
        <plist version=\"1.0\">
        <dict>
        {body}
        </dict>
        </plist>
        """
    ).strip() + "\n"

# Helpers -----------------------------------------------------------------


def default_overlay_path() -> Path | None:
    candidate = Path("mcp.yml")
    return candidate if candidate.exists() else None


def load_overlay(path: Path | None) -> dict[str, Any] | None:
    if not path:
        return None
    try:
        text = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    # Try JSON first
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except Exception:
        pass
    if yaml is None:  # pragma: no cover - optional dependency missing
        print(f"Warning: PyYAML not installed, cannot parse overlay '{path}'", file=sys.stderr)
        return None
    try:
        data = yaml.safe_load(text)
        return data if isinstance(data, dict) else None
    except Exception as exc:  # pragma: no cover
        print(f"Warning: failed to parse overlay '{path}': {exc}", file=sys.stderr)
        return None


def format_overlay(data: dict[str, Any]) -> list[str]:
    output: list[str] = []
    tasks = data.get("tasks")
    prompts = data.get("prompts")
    resources = data.get("resources")
    if tasks:
        output.append("")
        output.append("Tasks")
        for item in tasks:
            if isinstance(item, dict):
                name = item.get("name") or item.get("title") or "Task"
                description = item.get("description")
                line = f"- {name}"
                if description:
                    line += f": {description}"
                output.append(line)
            else:
                output.append(f"- {item}")
    if prompts:
        output.append("")
        output.append("Prompts")
        for prompt in prompts:
            if isinstance(prompt, dict):
                pid = prompt.get("id") or prompt.get("name") or "prompt"
                description = prompt.get("description")
                line = f"- {pid}"
                if description:
                    line += f": {description}"
                output.append(line)
            else:
                output.append(f"- {prompt}")
    if resources:
        output.append("")
        output.append("Resources")
        for resource in resources:
            if isinstance(resource, dict):
                rid = resource.get("uri") or resource.get("name") or "resource"
                description = resource.get("description")
                line = f"- {rid}"
                if description:
                    line += f": {description}"
                output.append(line)
            else:
                output.append(f"- {resource}")
    return output


def generate_plist(payload: dict[str, Any]) -> str:
    def format_value(value: Any, indent: int = 2) -> str:
        space = " " * indent
        if isinstance(value, dict):
            items = [f"{space}<key>{k}</key>\n{format_value(v, indent + 2)}" for k, v in value.items()]
            return f"{space}<dict>\n" + "\n".join(items) + f"\n{space}</dict>"
        if isinstance(value, list):
            items = [format_value(v, indent + 2) for v in value]
            return f"{space}<array>\n" + "\n".join(items) + f"\n{space}</array>"
        if isinstance(value, bool):
            return f"{space}<{'true' if value else 'false'}/>"
        return f"{space}<string>{value}</string>"

    items = []
    for key, val in payload.items():
        items.append(f"  <key>{key}</key>\n{format_value(val, 2)}")
    body = "\n".join(items)
    return textwrap.dedent(
        f"""\
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
        <dict>
        {body}
        </dict>
        </plist>
        """
    ).strip() + "\n"


def config_home() -> Path:
    base = os.environ.get("MCP_CONFIG_HOME")
    if base:
        return Path(base).expanduser()
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg).expanduser() / "mcp"
    return Path.home() / ".config" / "mcp"


def registry_path() -> Path:
    return config_home() / "registry.json"


def read_registry(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"servers": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"Failed to parse {path}: {exc}")


def backup_file(path: Path) -> None:
    if path.exists():
        ts = int(time.time())
        bak = path.with_suffix(path.suffix + f".bak.{ts}")
        bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    json.loads(tmp.read_text(encoding="utf-8"))
    os.replace(tmp, path)


def cmd_list(_: argparse.Namespace) -> int:
    reg = read_registry(registry_path())
    servers = reg.get("servers", {})
    if not servers:
        print("No servers registered")
        return 0
    for name, server in servers.items():
        args = " ".join(server.get("args", []))
        env_file = server.get("env_file")
        extras = f" [{env_file}]" if env_file else ""
        print(f"- {name}: {server.get('command')} {args}{extras}")
    return 0


def cmd_register(ns: argparse.Namespace) -> int:
    reg_path = registry_path()
    registry = read_registry(reg_path)
    registry.setdefault("servers", {})
    entry: dict[str, Any] = {
        "command": ns.command,
        "args": ns.args or [],
        "autostart": bool(ns.autostart),
    }
    if ns.env_file:
        entry["env_file"] = ns.env_file
    if ns.docs:
        entry["docs"] = ns.docs
    if ns.tools_index:
        entry["tools_index"] = ns.tools_index
    registry["servers"][ns.name] = entry
    backup_file(reg_path)
    atomic_write_json(reg_path, registry)
    print(f"Registered '{ns.name}'")
    return 0


def cmd_unregister(ns: argparse.Namespace) -> int:
    reg_path = registry_path()
    registry = read_registry(reg_path)
    servers = registry.get("servers", {})
    if ns.name not in servers:
        print(f"No such server '{ns.name}'", file=sys.stderr)
        return 1
    del servers[ns.name]
    backup_file(reg_path)
    atomic_write_json(reg_path, registry)
    print(f"Unregistered '{ns.name}'")
    return 0


def load_servers() -> dict[str, dict[str, Any]]:
    return read_registry(registry_path()).get("servers", {})


def cmd_export_agents(ns: argparse.Namespace) -> int:
    servers = load_servers()
    names = ns.name or list(servers)
    lines = [
        "Agent Integration (MCP)",
        "",
        "These MCP servers are available on this machine:",
    ]
    for name in names:
        server = servers.get(name)
        if not server:
            continue
        lines.append(f"- {name}: command `{server.get('command')}`")
        if server.get("tools_index"):
            lines.append(f"  - Tools index: {server['tools_index']}")
        if server.get("docs"):
            lines.append(f"  - Docs: {server['docs']}")
    overlay = load_overlay(ns.overlay) if ns.overlay else load_overlay(default_overlay_path())
    if overlay:
        lines.extend(format_overlay(overlay))
    output = "\n".join(lines) + "\n"
    if ns.output:
        Path(ns.output).write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
    return 0


def load_env_file(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key] = value
    return env


def cmd_create_wrappers(ns: argparse.Namespace) -> int:
    servers = load_servers()
    if not servers:
        print("No servers registered", file=sys.stderr)
        return 1
    bin_dir = Path(ns.bin_dir).expanduser() if ns.bin_dir else (Path.home() / ".local" / "bin")
    bin_dir.mkdir(parents=True, exist_ok=True)
    created: list[str] = []
    for name, server in servers.items():
        wrapper = bin_dir / name
        env_file = server.get("env_file")
        lines = [
            "#!/usr/bin/env bash",
            "set -euo pipefail",
            "# Auto-generated by mcpctl",
        ]
        if env_file:
            lines.append(f"if [ -f '{env_file}' ]; then set -a; source '{env_file}'; set +a; fi")
        cmd = server.get("command")
        args = " ".join(server.get("args", []))
        lines.append(f"exec {cmd} {args} \"$@\"")
        wrapper.write_text("\n".join(lines) + "\n", encoding="utf-8")
        wrapper.chmod(wrapper.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        created.append(str(wrapper))
    print("Created wrappers:\n" + "\n".join(created))
    return 0


def cmd_create_launchd(ns: argparse.Namespace) -> int:
    servers = load_servers()
    server = servers.get(ns.name)
    if not server:
        print(f"No such server '{ns.name}'", file=sys.stderr)
        return 1
    label = ns.label or f"com.local.{ns.name}"
    output_dir = Path(ns.output).expanduser() if ns.output else (Path.home() / "Library" / "LaunchAgents")
    output_dir.mkdir(parents=True, exist_ok=True)
    plist_path = output_dir / f"{label}.plist"
    program = server.get("command")
    args = server.get("args", [])
    program_arguments = [program, *args]
    env_file = server.get("env_file")
    env_dict = load_env_file(Path(env_file)) if env_file else {}
    plist = {
        "Label": label,
        "ProgramArguments": program_arguments,
        "RunAtLoad": True,
        "KeepAlive": bool(ns.keep_alive),
    }
    if env_dict:
        plist["EnvironmentVariables"] = env_dict
    plist_content = generate_plist(plist)
    plist_path.write_text(plist_content, encoding="utf-8")
    print(f"LaunchAgent written to {plist_path}")
    return 0


def cmd_configure(ns: argparse.Namespace) -> int:
    name = ns.name or "coda-mcp"
    if not ns.cursor and not ns.claude:
        ns.cursor = ns.claude = True
    if ns.dry_run:
        print(f"[dry-run] Would configure clients for '{name}'")
        targets = []
        if ns.cursor:
            targets.append("Cursor (~/.cursor/mcp.json)")
        if ns.claude:
            targets.append("Claude Desktop (~/Library/Application Support/Claude/claude_desktop_config.json)")
        for t in targets:
            print(f"  - {t}")
        return 0
    if ns.cursor:
        configure_cursor(name, name)
    if ns.claude:
        configure_claude(name, name)
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="mcpctl", description="Local MCP server manager")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("list", help="List registered servers")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("register", help="Register a server")
    p.add_argument("--name", required=True)
    p.add_argument("--command", required=True)
    p.add_argument("--arg", dest="args", action="append", default=[])
    p.add_argument("--env-file")
    p.add_argument("--docs")
    p.add_argument("--tools-index")
    p.add_argument("--autostart", action="store_true")
    p.set_defaults(func=cmd_register)

    p = sub.add_parser("unregister", help="Unregister a server")
    p.add_argument("--name", required=True)
    p.set_defaults(func=cmd_unregister)

    p = sub.add_parser("export-agents", help="Export AGENTS.md MCP section")
    p.add_argument("--name", action="append", help="Restrict to specific server names")
    p.add_argument("--output")
    p.add_argument("--overlay", help="Path to mcp.yml overlay (defaults to ./mcp.yml if present)")
    p.set_defaults(func=cmd_export_agents)

    p = sub.add_parser("create-wrappers", help="Create PATH wrappers for all servers")
    p.add_argument("--bin-dir")
    p.set_defaults(func=cmd_create_wrappers)

    p = sub.add_parser("create-launchd", help="Generate a launchd plist for a server")
    p.add_argument("--name", required=True, help="Registered server name")
    p.add_argument("--label", help="LaunchAgent label (defaults to com.local.<name>)")
    p.add_argument("--output", help="Directory for plist (defaults to ~/Library/LaunchAgents)")
    p.add_argument("--keep-alive", action="store_true", help="Keep the server alive (LaunchAgent KeepAlive)")
    p.set_defaults(func=cmd_create_launchd)

    p = sub.add_parser("configure", help="Configure MCP clients")
    p.add_argument("--name", help="Server name (default: coda-mcp)")
    p.add_argument("--cursor", action="store_true")
    p.add_argument("--claude", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_configure)

    return ap


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)
    return ns.func(ns)


if __name__ == "__main__":
    raise SystemExit(main())
