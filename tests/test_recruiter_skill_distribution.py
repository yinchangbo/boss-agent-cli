"""验证 Windows Skill 的独立入口、版本锁与分发文件边界。"""

import importlib.util
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load_script(path):
	spec = importlib.util.spec_from_file_location(path.stem, path)
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


def test_copy_excludes_development_environment_and_business_data(tmp_path):
	packager = load_script(ROOT / "scripts/package_recruiter_skill.py")
	source = tmp_path / "source"
	for name in [*packager.SKILL_FILES, ".venv/pyvenv.cfg", "candidates.json", "scripts/__pycache__/boss.pyc"]:
		path = source / name
		path.parent.mkdir(parents=True, exist_ok=True)
		path.write_text("测试", encoding="utf-8")
	destination = tmp_path / "bundle"
	packager.copy_skill_files(source, destination)
	assert {p.relative_to(destination).as_posix() for p in destination.rglob("*") if p.is_file()} == set(
		packager.SKILL_FILES
	)


@pytest.mark.parametrize("override", [None, "0", "relative-browsers", "C:/custom/browsers"])
def test_launcher_resolves_browser_path_and_preserves_override(tmp_path, monkeypatch, override):
	launcher = load_script(ROOT / ".agents/skills/boss-recruiter/scripts/boss.py")
	(tmp_path / "ms-playwright").mkdir()
	monkeypatch.delenv("PLAYWRIGHT_BROWSERS_PATH", raising=False)
	if override is not None:
		monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", override)
	assert launcher._resolve_browsers_path(tmp_path) == (override or str(tmp_path / "ms-playwright"))


@pytest.mark.skipif(os.name != "nt", reason="Windows 启动器")
def test_launcher_uses_bundled_python_and_passes_arguments_and_exit_code(tmp_path, monkeypatch):
	launcher = load_script(ROOT / ".agents/skills/boss-recruiter/scripts/boss.py")
	python = tmp_path / "runtime/python.exe"
	python.parent.mkdir()
	python.touch()
	(tmp_path / "ms-playwright").mkdir()
	monkeypatch.delenv("PLAYWRIGHT_BROWSERS_PATH", raising=False)
	monkeypatch.setattr(launcher, "__file__", str(tmp_path / "scripts/boss.py"))
	arguments = ["hr", "candidates", "中文 空格 & 特殊字符"]
	monkeypatch.setattr(sys, "argv", ["boss.py", *arguments])
	calls = []
	monkeypatch.setattr(
		launcher.subprocess,
		"run",
		lambda command, **kwargs: calls.append((command, kwargs)) or SimpleNamespace(returncode=7),
	)
	assert launcher.main() == 7
	command, options = calls[0]
	assert command[0] == str(python)
	assert command[-3:] == arguments
	assert "-I" in command
	assert options["env"]["PLAYWRIGHT_BROWSERS_PATH"] == str(tmp_path / "ms-playwright")
	assert options["env"]["PATH"].split(os.pathsep)[0] == str(tmp_path)
	assert "PLAYWRIGHT_BROWSERS_PATH" not in os.environ


@pytest.mark.skipif(os.name != "nt", reason="Windows 启动器")
def test_launcher_does_not_fall_back_to_old_venv(tmp_path, monkeypatch):
	launcher = load_script(ROOT / ".agents/skills/boss-recruiter/scripts/boss.py")
	old = tmp_path / ".venv/Scripts/python.exe"
	old.parent.mkdir(parents=True)
	old.touch()
	monkeypatch.setattr(launcher, "__file__", str(tmp_path / "scripts/boss.py"))
	assert launcher.main() == 1


def test_packager_rejects_browser_revision_drift(tmp_path):
	packager = load_script(ROOT / "scripts/package_recruiter_skill.py")
	lock = json.loads((ROOT / ".agents/skills/boss-recruiter/assets/runtime-lock.json").read_text(encoding="utf-8"))
	manifest = tmp_path / "patchright/driver/package/browsers.json"
	manifest.parent.mkdir(parents=True)
	entries = [
		{"name": name, "revision": lock["chromium_revision"], "browserVersion": lock["chromium_version"]}
		for name in ("chromium", "chromium-headless-shell")
	]
	manifest.write_text(json.dumps({"browsers": entries}), encoding="utf-8")
	assert packager.check_browser_manifest(tmp_path, lock)["browsers"] == entries
	entries[1]["revision"] = "9999"
	manifest.write_text(json.dumps({"browsers": entries}), encoding="utf-8")
	with pytest.raises(ValueError, match="不匹配"):
		packager.check_browser_manifest(tmp_path, lock)


def test_packager_rejects_corrupted_python_download(tmp_path):
	packager = load_script(ROOT / "scripts/package_recruiter_skill.py")
	(tmp_path / "python.zip").write_bytes(b"corrupt")
	with pytest.raises(ValueError, match="SHA-256"):
		packager.download_python(
			{"python_url": "https://www.python.org/python.zip", "python_sha256": "0" * 64}, tmp_path
		)
