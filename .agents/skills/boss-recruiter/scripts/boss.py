#!/usr/bin/env python3
"""使用 Windows 便携包内的 Python 调用 boss，透传参数、输出和退出码。"""

import os
from pathlib import Path
import subprocess
import sys


def _resolve_browsers_path(skill_dir: Path) -> str | None:
	"""保留显式覆盖（包括 0），否则使用便携包内的浏览器。"""
	if configured := os.environ.get("PLAYWRIGHT_BROWSERS_PATH"):
		return configured
	bundled = skill_dir / "ms-playwright"
	return str(bundled) if bundled.is_dir() else None


def main() -> int:
	if hasattr(sys.stderr, "reconfigure"):
		sys.stderr.reconfigure(encoding="utf-8")
	scripts_dir = Path(__file__).resolve().parent
	skill_dir = scripts_dir.parent
	if os.name != "nt":
		print("此 Skill 便携包仅支持 Windows x64。", file=sys.stderr)
		return 1
	python = skill_dir / "runtime/python.exe"
	if not python.is_file():
		print("缺少包内 Python，请重新解压完整的 Windows 便携包，并使用 boss.cmd。", file=sys.stderr)
		return 1
	env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
	if browsers := _resolve_browsers_path(skill_dir):
		env["PLAYWRIGHT_BROWSERS_PATH"] = browsers
	else:
		print("缺少包内 ms-playwright，请重新解压完整便携包。", file=sys.stderr)
		return 1
	# 仅影响子进程，使 doctor 能找到随包 patchright.cmd；不修改用户环境。
	env["PATH"] = str(skill_dir) + os.pathsep + env.get("PATH", "")
	flags = ["-I", "-B", "-X", "utf8"]
	try:
		# 项目没有 __main__.py，直接调用 pyproject.toml 声明的 console entrypoint。
		return subprocess.run(
			[str(python), *flags, "-c", "from boss_agent_cli.main import cli; cli(prog_name='boss')", *sys.argv[1:]],
			env=env,
		).returncode
	except OSError as exc:
		print(f"无法启动招聘 CLI：{exc}", file=sys.stderr)
		return 1


if __name__ == "__main__":
	raise SystemExit(main())
