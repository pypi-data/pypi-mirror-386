"""Configure local MCP clients (Cursor, Claude) to use stdio servers."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path


def backup_file(path: Path) -> Path | None:
    if not path.exists():
        return None
    ts = int(time.time())
    backup = path.with_suffix(path.suffix + f".bak.{ts}")
    shutil.copy2(path, backup)
    return backup


def atomic_write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    json.loads(tmp.read_text(encoding="utf-8"))
    os.replace(tmp, path)


def configure_cursor(server_name: str, command: str, args: list[str] | None = None, env: dict[str, str] | None = None, dry_run: bool = False) -> None:
    cfg_path = Path.home() / ".cursor" / "mcp.json"
    args = args or []
    env = env or {}
    existing = {"servers": {}}
    if cfg_path.exists():
        try:
            existing = json.loads(cfg_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise SystemExit(f"Failed to parse {cfg_path}: {exc}")
    if "servers" not in existing or not isinstance(existing["servers"], dict):
        existing["servers"] = {}
    existing["servers"][server_name] = {
        "type": "stdio",
        "command": command,
        "args": args,
        "env": env,
    }
    if dry_run:
        print(f"[dry-run] Would update {cfg_path} with server '{server_name}'")
        return
    backup_file(cfg_path)
    atomic_write_json(cfg_path, existing)
    print(f"Updated Cursor config: {cfg_path}")


def configure_claude(server_name: str, command: str, args: list[str] | None = None, env: dict[str, str] | None = None, dry_run: bool = False) -> None:
    cfg_path = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    args = args or []
    env = env or {}
    existing = {"mcpServers": {}}
    if cfg_path.exists():
        try:
            existing = json.loads(cfg_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise SystemExit(f"Failed to parse {cfg_path}: {exc}")
    if "mcpServers" not in existing or not isinstance(existing["mcpServers"], dict):
        existing["mcpServers"] = {}
    existing["mcpServers"][server_name] = {
        "command": command,
        "args": args,
        "env": env,
    }
    if dry_run:
        print(f"[dry-run] Would update {cfg_path} with server '{server_name}'")
        return
    backup_file(cfg_path)
    atomic_write_json(cfg_path, existing)
    print(f"Updated Claude Desktop config: {cfg_path}")


def parse_env(pairs: list[str]) -> dict[str, str]:
    env: dict[str, str] = {}
    for item in pairs:
        if "=" not in item:
            print(f"Ignoring malformed env '{item}', expected KEY=VALUE", file=sys.stderr)
            continue
        key, value = item.split("=", 1)
        env[key] = value
    return env


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Configure local MCP clients")
    ap.add_argument("--server-name", default="coda-mcp")
    ap.add_argument("--command", default="coda-mcp")
    ap.add_argument("--arg", dest="args", action="append", default=[])
    ap.add_argument("--env", dest="env", action="append", default=[])
    ap.add_argument("--cursor", action="store_true", help="Configure Cursor")
    ap.add_argument("--claude", action="store_true", help="Configure Claude Desktop")
    ap.add_argument("--dry-run", action="store_true")
    return ap


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)
    env = parse_env(ns.env)
    if not ns.cursor and not ns.claude:
        ns.cursor = ns.claude = True
    if ns.cursor:
        configure_cursor(ns.server_name, ns.command, ns.args, env, ns.dry_run)
    if ns.claude:
        configure_claude(ns.server_name, ns.command, ns.args, env, ns.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

