#!/usr/bin/env python3
"""构建招聘 Skill 的随包 CLI，并生成可跨电脑分发的压缩包。"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents/skills/boss-recruiter"


def write_archive(skill_dir: Path, wheel: Path, destination: Path) -> None:
	# 明确列出发布文件，避免把虚拟环境、缓存、登录态或临时业务数据打入包。
	files = [
		skill_dir / "SKILL.md",
		skill_dir / "agents/openai.yaml",
		skill_dir / "references/recruiter-cli.md",
		skill_dir / "scripts/boss.py",
		skill_dir / "scripts/setup_cli.py",
		wheel,
	]
	for path in files:
		if not path.is_file() or path.is_symlink():
			raise ValueError(f"分发文件缺失或为符号链接：{path}")
	destination.parent.mkdir(parents=True, exist_ok=True)
	with ZipFile(destination, "w", compression=ZIP_DEFLATED) as archive:
		for path in files:
			archive.write(path, (Path("boss-recruiter") / path.relative_to(skill_dir)).as_posix())


def main() -> int:
	if hasattr(sys.stdout, "reconfigure"):
		sys.stdout.reconfigure(encoding="utf-8")
	with tempfile.TemporaryDirectory(prefix="boss-skill-build-") as temporary:
		subprocess.run(
			[sys.executable, "-m", "pip", "wheel", "--no-deps", "--wheel-dir", temporary, str(ROOT)],
			check=True,
		)
		wheels = list(Path(temporary).glob("boss_agent_cli-*.whl"))
		if len(wheels) != 1:
			raise ValueError("构建结果必须恰好包含一个 CLI wheel")
		assets = SKILL / "assets"
		assets.mkdir(exist_ok=True)
		wheel = assets / wheels[0].name
		shutil.copy2(wheels[0], wheel)
		# 仅清理本脚本生成的旧版本安装包，不删除其他 Skill 文件。
		for old in assets.glob("boss_agent_cli-*.whl"):
			if old != wheel:
				old.unlink()
	archive = ROOT / "dist/boss-recruiter.zip"
	write_archive(SKILL, wheel, archive)
	print(f"已生成分发包：{archive}")
	print("接收者解压后，在 boss-recruiter 目录执行：python scripts/setup_cli.py")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
