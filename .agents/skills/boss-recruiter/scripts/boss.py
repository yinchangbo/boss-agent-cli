#!/usr/bin/env python3
"""使用本 Skill 的独立环境调用 boss，透传参数、输出和退出码。"""

import os
from pathlib import Path
import subprocess
import sys


def main() -> int:
	if hasattr(sys.stderr, "reconfigure"):
		sys.stderr.reconfigure(encoding="utf-8")
	scripts_dir = Path(__file__).resolve().parent
	python = scripts_dir.parent / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
	if not python.is_file():
		print(f'尚未安装招聘 CLI，请先运行：python "{scripts_dir / "setup_cli.py"}"', file=sys.stderr)
		return 1
	env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
	try:
		# 项目没有 __main__.py，直接调用 pyproject.toml 声明的 console entrypoint。
		return subprocess.run(
			[str(python), "-c", "from boss_agent_cli.main import cli; cli(prog_name='boss')", *sys.argv[1:]],
			env=env,
		).returncode
	except OSError as exc:
		print(f"无法启动招聘 CLI：{exc}", file=sys.stderr)
		return 1


if __name__ == "__main__":
	raise SystemExit(main())
