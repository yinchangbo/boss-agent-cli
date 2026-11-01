#!/usr/bin/env python3
"""构建 Windows x64 招聘 Skill：随包 Python、固定依赖和匹配的 Chromium。"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents/skills/boss-recruiter"
WORK = ROOT / "dist/windows-build"
SKILL_FILES = (
	"SKILL.md",
	"agents/openai.yaml",
	"references/recruiter-cli.md",
	"scripts/boss.py",
	"boss.cmd",
	"patchright.cmd",
	"assets/runtime-lock.json",
	"assets/requirements-windows.lock.txt",
)


def sha256(path: Path) -> str:
	digest = hashlib.sha256()
	with path.open("rb") as stream:
		for block in iter(lambda: stream.read(1024 * 1024), b""):
			digest.update(block)
	return digest.hexdigest()


def download_python(lock: dict, cache: Path) -> Path:
	path = cache / lock["python_url"].rsplit("/", 1)[-1]
	path.parent.mkdir(parents=True, exist_ok=True)
	if not path.exists():
		partial = path.with_suffix(".part")
		with urlopen(lock["python_url"], timeout=120) as response, partial.open("wb") as target:
			shutil.copyfileobj(response, target)
		partial.replace(path)
	if sha256(path) != lock["python_sha256"]:
		raise ValueError(f"Python 下载包 SHA-256 与锁定值不符：{path}")
	return path


def check_browser_manifest(site: Path, lock: dict) -> dict:
	manifest = json.loads((site / "patchright/driver/package/browsers.json").read_text(encoding="utf-8"))
	for name in ("chromium", "chromium-headless-shell"):
		entry = next(item for item in manifest["browsers"] if item["name"] == name)
		if entry["revision"] != lock["chromium_revision"] or entry["browserVersion"] != lock["chromium_version"]:
			raise ValueError(f"{name} 与锁定的 Chromium 不匹配：{entry}")
	return manifest


def remove_build_paths(runtime: Path) -> None:
	# pip 生成的 .exe 启动器含构建机绝对路径；便携包只使用手写的相对路径 .cmd。
	scripts = (runtime / "Scripts").resolve()
	if not scripts.is_relative_to(runtime.resolve()):
		raise ValueError("Scripts 路径越出本次构建的 Python 目录")
	if scripts.exists():
		shutil.rmtree(scripts)
	for cache in runtime.rglob("__pycache__"):
		if not cache.resolve().is_relative_to(runtime.resolve()):
			raise ValueError("字节码缓存越出构建目录")
		shutil.rmtree(cache)
	for direct_url in (runtime / "Lib/site-packages").glob("*.dist-info/direct_url.json"):
		direct_url.unlink()
		record = direct_url.with_name("RECORD")
		if record.exists():
			with record.open(encoding="utf-8", newline="") as stream:
				rows = [row for row in csv.reader(stream) if not row[0].endswith("/direct_url.json")]
			with record.open("w", encoding="utf-8", newline="") as stream:
				csv.writer(stream).writerows(rows)


def copy_skill_files(source: Path, destination: Path) -> None:
	"""从源码白名单复制，不带已有环境、缓存、登录态和业务数据。"""
	for name in SKILL_FILES:
		path = source / name
		if not path.is_file() or path.is_symlink():
			raise ValueError(f"分发文件缺失或为符号链接：{path}")
		target = destination / name
		target.parent.mkdir(parents=True, exist_ok=True)
		shutil.copy2(path, target)


def write_portable_archive(skill: Path, destination: Path) -> None:
	with ZipFile(destination, "w", compression=ZIP_DEFLATED, compresslevel=6) as archive:
		for path in sorted(skill.rglob("*")):
			if path.is_symlink():
				raise ValueError(f"便携包不接受符号链接：{path}")
			if path.is_file():
				archive.write(path, (Path("boss-recruiter") / path.relative_to(skill)).as_posix())


def main() -> int:
	if hasattr(sys.stdout, "reconfigure"):
		sys.stdout.reconfigure(encoding="utf-8")
	if os.name != "nt" or platform.machine().lower() not in {"amd64", "x86_64"}:
		raise SystemExit("请在 Windows x64 构建和验证此便携包")
	lock = json.loads((SKILL / "assets/runtime-lock.json").read_text(encoding="utf-8"))
	requirements = SKILL / "assets/requirements-windows.lock.txt"
	if f"patchright=={lock['patchright_version']} " not in requirements.read_text(encoding="utf-8").lower():
		raise ValueError("依赖锁与 runtime-lock.json 的 Patchright 版本不一致")
	WORK.mkdir(parents=True, exist_ok=True)
	embed = download_python(lock, WORK / "downloads")
	env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PIP_DISABLE_PIP_VERSION_CHECK="1")
	for key in ("PYTHONPATH", "PYTHONHOME"):
		env.pop(key, None)

	def run(args: list[str], **kwargs) -> subprocess.CompletedProcess:
		return subprocess.run(args, check=True, env=env, **kwargs)

	with tempfile.TemporaryDirectory(prefix="assemble-", dir=WORK) as temporary:
		stage = Path(temporary)
		skill = stage / "boss-recruiter"
		copy_skill_files(SKILL, skill)
		wheel_dir = stage / "cli-wheel"
		run([sys.executable, "-m", "pip", "wheel", "--no-deps", "--wheel-dir", str(wheel_dir), str(ROOT)])
		cli_wheels = list(wheel_dir.glob("boss_agent_cli-*.whl"))
		if len(cli_wheels) != 1:
			raise ValueError("构建结果必须恰好包含一个 CLI wheel")
		wheel = cli_wheels[0]
		runtime = skill / "runtime"
		with ZipFile(embed) as archive:
			archive.extractall(runtime)
		# _pth 保持隔离，所有路径相对于 python.exe；启用 site 以加载 pywin32 的 .pth。
		py_tag = "".join(lock["python_version"].split(".")[:2])
		(runtime / f"python{py_tag}._pth").write_text(
			f"python{py_tag}.zip\n.\nLib/site-packages\nimport site\n", encoding="utf-8"
		)
		python = runtime / "python.exe"
		pip = [sys.executable, "-m", "pip", "--python", str(python)]
		wheels = WORK / "wheels"
		# download 使用目标解释器解析依赖；哈希锁阻止构建时静默升级。
		run(
			[
				*pip,
				"download",
				"--only-binary=:all:",
				"--require-hashes",
				"-r",
				str(requirements),
				"--dest",
				str(wheels),
			]
		)
		run(
			[
				*pip,
				"install",
				"--no-index",
				"--find-links",
				str(wheels),
				"--require-hashes",
				"--no-compile",
				"--no-warn-script-location",
				"-r",
				str(requirements),
			]
		)
		run([*pip, "install", "--no-deps", "--no-compile", "--no-warn-script-location", str(wheel)])
		run([*pip, "check"])
		site = runtime / "Lib/site-packages"
		browser_manifest = check_browser_manifest(site, lock)
		browsers = WORK / f"browsers-patchright-{lock['patchright_version']}"
		env["PLAYWRIGHT_BROWSERS_PATH"] = str(browsers)
		env["PLAYWRIGHT_SKIP_BROWSER_GC"] = "1"
		print("下载并校验锁定版本的 Chromium、Headless Shell 及配套组件……", flush=True)
		run([str(python), "-I", "-B", "-X", "utf8", "-m", "patchright", "install", "chromium"])
		# 只复制安装器选中的二进制目录；不带 .links 中的构建机路径和其他缓存。
		for name in ("chromium", "chromium-headless-shell", "ffmpeg", "winldd"):
			entry = next(item for item in browser_manifest["browsers"] if item["name"] == name)
			directory = f"{name.replace('-', '_')}-{entry['revision']}"
			source = browsers / directory
			if not source.is_dir():
				raise ValueError(f"浏览器组件缺失：{source}")
			shutil.copytree(source, skill / "ms-playwright" / directory)
		remove_build_paths(runtime)
		installed = run(
			[
				str(python),
				"-I",
				"-B",
				"-c",
				"import importlib.metadata as m, json; print(json.dumps({d.metadata['Name']:d.version for d in m.distributions()}))",
			],
			capture_output=True,
			text=True,
		)
		manifest = {"runtime": lock, "packages": json.loads(installed.stdout), "files": {}}
		if manifest["packages"].get("patchright") != lock["patchright_version"]:
			raise ValueError("安装后的 Patchright 版本与锁不一致")
		for path in sorted(skill.rglob("*")):
			if path.is_file():
				manifest["files"][path.relative_to(skill).as_posix()] = sha256(path)
		(skill / "portable-manifest.json").write_text(
			json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
		)
		partial = WORK / "boss-recruiter.pending.zip"
		print("压缩便携包……", flush=True)
		write_portable_archive(skill, partial)
	# 解压到全新中文/空格路径，清空 Python PATH 和浏览器缓存引用后验收。
	run(
		[
			sys.executable,
			str(ROOT / "scripts/verify_recruiter_windows.py"),
			str(partial),
			"--report",
			str(ROOT / "dist/boss-recruiter.validation.json"),
		]
	)
	destination = ROOT / "dist/boss-recruiter.zip"
	partial.replace(destination)
	digest = sha256(destination)
	destination.with_suffix(".zip.sha256").write_text(f"{digest}  {destination.name}\n", encoding="ascii")
	report_path = ROOT / "dist/boss-recruiter.validation.json"
	report = json.loads(report_path.read_text(encoding="utf-8"))
	report.update(archive=destination.name, sha256=digest)
	report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
	print(f"已生成并通过迁移验收：{destination}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
