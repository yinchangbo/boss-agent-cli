#!/usr/bin/env python3
"""将招聘 CLI 安装到本 Skill 的独立环境。"""

import argparse
import os
from pathlib import Path
import subprocess
import sys
import venv


def main() -> int:
	for stream in (sys.stdout, sys.stderr):
		if hasattr(stream, "reconfigure"):
			stream.reconfigure(encoding="utf-8")
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--source", help="本地项目目录或带版本的 pip 包规格；默认查找所在仓库")
	parser.add_argument("--browser", action="store_true", help="同时安装扫码登录所需的 Chromium")
	args = parser.parse_args()
	if sys.version_info < (3, 10):
		parser.error("需要 Python 3.10 及以上")
	skill_dir = Path(__file__).resolve().parents[1]
	source = args.source
	if source is None:
		for parent in skill_dir.parents:
			if (parent / "pyproject.toml").is_file() and (parent / "src/boss_agent_cli/main.py").is_file():
				source = str(parent)
				break
	if not source:
		parser.error('找不到项目源码，请指定 --source 仓库路径 或 --source "boss-agent-cli==版本"')
	source_path = Path(source).expanduser()
	if source_path.is_dir():
		install_args = ["--editable", str(source_path.resolve())]
	else:
		install_args = [source]
	env_dir = skill_dir / ".venv"
	python = env_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
	env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
	try:
		if not python.is_file():
			venv.EnvBuilder(with_pip=True).create(env_dir)
		subprocess.run(
			[str(python), "-m", "pip", "install", *install_args],
			check=True,
			env=env,
			stdout=sys.stderr,
		)
		if args.browser:
			subprocess.run(
				[str(python), "-m", "patchright", "install", "chromium"],
				check=True,
				env=env,
				stdout=sys.stderr,
			)
	except subprocess.CalledProcessError as exc:
		print("安装未完成，请修复上述错误后重新运行安装脚本。", file=sys.stderr)
		return exc.returncode
	except OSError as exc:
		print(f"无法创建或运行 Skill 环境：{exc}", file=sys.stderr)
		return 1
	print(f"招聘 CLI 已安装：{env_dir}", file=sys.stderr)
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
