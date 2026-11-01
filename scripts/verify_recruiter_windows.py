#!/usr/bin/env python3
"""在隔离的中文/空格目录验收 Windows 便携 Skill，不访问招聘业务接口。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from zipfile import ZipFile


BROWSER_PROBE = r"""
import importlib.util
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import sys
import site

skill = Path(sys.argv[1])
manifest = json.loads((skill / 'portable-manifest.json').read_text(encoding='utf-8'))
lock = manifest['runtime']
assert '.'.join(map(str, sys.version_info[:3])) == lock['python_version']
assert not site.ENABLE_USER_SITE
assert metadata.version('patchright') == lock['patchright_version']
assert {d.metadata['Name']: d.version for d in metadata.distributions()} == manifest['packages']
import boss_agent_cli
assert Path(boss_agent_cli.__file__).resolve().is_relative_to(skill / 'runtime')
# 验证嵌入式 Python 的原生扩展及 pywin32 DLL 均可加载。
import win32api, pythoncom, pywintypes, _cffi_backend, greenlet, lz4.frame
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
key = AESGCM.generate_key(bit_length=128)
cipher = AESGCM(key)
assert cipher.decrypt(b'0' * 12, cipher.encrypt(b'0' * 12, b'portable', None), None) == b'portable'

spec = importlib.util.spec_from_file_location('skill_launcher', skill / 'scripts/boss.py')
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = launcher._resolve_browsers_path(skill)
from boss_agent_cli.services.browser_runtime import patchright_chromium_revision
from boss_agent_cli.wizard.preflight import _browser_kernel_status
assert patchright_chromium_revision() == lock['chromium_revision']
assert _browser_kernel_status()[0] == 'ok', _browser_kernel_status()

from patchright.sync_api import sync_playwright
versions = {}
with sync_playwright() as p:
    assert Path(p.chromium.executable_path).resolve().is_relative_to(skill / 'ms-playwright')
    # 默认无头模式使用 Headless Shell；chromium 通道使用完整 Chromium，均不开可见窗口。
    for name, options in [('headless_shell', {}), ('chromium', {'channel': 'chromium'})]:
        browser = p.chromium.launch(headless=True, **options)
        try:
            page = browser.new_page()
            page.goto('data:text/html,<title>portable-ok</title><p>offline</p>')
            assert page.title() == 'portable-ok'
            assert browser.version == lock['chromium_version'], browser.version
            versions[name] = browser.version
        finally:
            browser.close()
print(json.dumps({'python': lock['python_version'], 'patchright': metadata.version('patchright'), 'browsers': versions}))
"""


def verify(archive_path: Path) -> dict:
	if os.name != "nt":
		raise ValueError("Windows 便携包需要在 Windows 上验收")
	with tempfile.TemporaryDirectory(prefix="boss-skill-迁移 验收-") as temporary:
		root = Path(temporary).resolve()
		with ZipFile(archive_path) as archive:
			for name in archive.namelist():
				if not (root / name).resolve().is_relative_to(root):
					raise ValueError(f"压缩包路径越界：{name}")
			archive.extractall(root)
		skill = root / "boss-recruiter"
		manifest = json.loads((skill / "portable-manifest.json").read_text(encoding="utf-8"))
		actual_files = {p.relative_to(skill).as_posix() for p in skill.rglob("*") if p.is_file()}
		if actual_files != set(manifest["files"]) | {"portable-manifest.json"}:
			raise ValueError("包内文件与清单不一致")
		for name, expected in manifest["files"].items():
			with (skill / name).open("rb") as stream:
				digest = hashlib.sha256()
				for block in iter(lambda: stream.read(1024 * 1024), b""):
					digest.update(block)
			if digest.hexdigest() != expected:
				raise ValueError(f"文件校验失败：{name}")
		print(f"已解压并校验 {len(manifest['files'])} 个文件", flush=True)
		env = dict(os.environ)
		for key in list(env):
			if key.upper().startswith(("PYTHON", "PLAYWRIGHT", "BOSS_")) or key.upper() == "INIT_CWD":
				env.pop(key)
		windows = Path(os.environ["SystemRoot"])
		env["PATH"] = str(windows / "System32")
		for key, value in {
			"USERPROFILE": root / "user",
			"HOME": root / "user",
			"LOCALAPPDATA": root / "user/local",
			"APPDATA": root / "user/roaming",
		}.items():
			value.mkdir(parents=True, exist_ok=True)
			env[key] = str(value)
		cwd = root / "业务工作目录"
		cwd.mkdir()

		def run(command: list[str]) -> subprocess.CompletedProcess:
			result = subprocess.run(
				command, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", timeout=120
			)
			if result.returncode:
				raise RuntimeError(f"验收命令失败（{result.returncode}）：{command}\n{result.stdout}\n{result.stderr}")
			return result

		boss = str(skill / "boss.cmd")
		common = [boss, "--data-dir", str(root / "data"), "--json", "--role", "recruiter", "--platform", "zhipin"]
		schema = json.loads(run([*common, "schema"]).stdout)
		assert schema["ok"] is True
		assert "candidates" in run([boss, "hr", "--help"]).stdout
		# 参数错误的退出码应透传到调用 Agent。
		bad = subprocess.run([boss, "--invalid-portable-option"], cwd=cwd, env=env, capture_output=True, timeout=30)
		assert bad.returncode != 0
		print("清空系统 Python PATH 后，boss.cmd、schema、帮助及退出码检查通过", flush=True)
		doctor = json.loads(run([*common, "doctor"]).stdout)
		checks = {item["name"]: item for item in doctor["data"]["checks"]}
		for name in ("python", "patchright", "patchright_chromium"):
			assert checks[name]["status"] == "ok", checks[name]
		python = skill / "runtime/python.exe"
		probe = json.loads(run([str(python), "-I", "-B", "-X", "utf8", "-c", BROWSER_PROBE, str(skill)]).stdout)
		print("完整 Chromium 和 Headless Shell 实际启动成功，版本与锁一致", flush=True)
		# 用户显式覆盖空目录时，doctor 必须报告缺失，不借用包内或宿主缓存。
		env["PLAYWRIGHT_BROWSERS_PATH"] = str(root / "empty-browser-override")
		overridden = json.loads(run([*common, "doctor"]).stdout)
		check = next(item for item in overridden["data"]["checks"] if item["name"] == "patchright_chromium")
		assert check["status"] == "warn", check
		return {
			"passed": True,
			"archive": archive_path.name,
			"file_count": len(manifest["files"]),
			"versions": probe,
			"checks": [
				"file_hashes",
				"isolated_python",
				"native_extensions",
				"cli_schema",
				"cli_help",
				"exit_code",
				"doctor",
				"wizard_preflight",
				"headless_shell_launch",
				"chromium_launch",
				"browser_path_override",
			],
			"live_recruitment_tested": False,
		}


def main() -> int:
	if hasattr(sys.stdout, "reconfigure"):
		sys.stdout.reconfigure(encoding="utf-8")
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("archive", type=Path)
	parser.add_argument("--report", type=Path)
	args = parser.parse_args()
	result = verify(args.archive.resolve())
	if args.report:
		args.report.parent.mkdir(parents=True, exist_ok=True)
		args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
	print("Windows 便携包迁移验收通过；未连接招聘业务或读取真实登录态。")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
